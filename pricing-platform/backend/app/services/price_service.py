import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.mixins import utcnow
from app.models.price import Price, PriceStatus
from app.models.price_history import PriceHistory
from app.repositories.price_history_repository import PriceHistoryRepository
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.price import PriceCreate, PriceListParams, PriceUpdate
from app.services import output_router_service


def _as_aware(value: datetime) -> datetime:
    """SQLite (used in tests) drops tzinfo on round-trip even for
    DateTime(timezone=True) columns; MySQL always returns naive values
    already normalized to UTC. Either way, a naive value from the DB means
    UTC — attach tzinfo so it can be compared against an aware `now`.
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def compute_display_status(price: Price, now: datetime | None = None) -> PriceStatus:
    """The stored status is authoritative for the manual INACTIVE state;
    ACTIVE/SCHEDULED/EXPIRED are otherwise date-driven and computed here at
    read time rather than persisted — mirrors Phase 4's Inventory status
    pattern, and avoids silently mutating rows just because someone did a
    GET.
    """
    now = now or utcnow()
    if price.status == PriceStatus.INACTIVE:
        return PriceStatus.INACTIVE
    if price.effective_to is not None and _as_aware(price.effective_to) < now:
        return PriceStatus.EXPIRED
    if _as_aware(price.effective_from) > now:
        return PriceStatus.SCHEDULED
    return PriceStatus.ACTIVE


def _validate_scope(
    db: Session, *, organization_id: uuid.UUID, product_id: uuid.UUID, store_id: uuid.UUID | None
) -> None:
    if ProductRepository(db).get_by_id_for_organization(product_id, organization_id) is None:
        raise NotFoundError("Product not found.", code="product_not_found")
    if store_id is not None:
        if StoreRepository(db).get_by_id_for_organization(store_id, organization_id) is None:
            raise NotFoundError("Store not found.", code="store_not_found")


def _record_history(
    db: Session,
    *,
    organization_id: uuid.UUID,
    price: Price,
    old_price: Decimal | None,
    change_type: str,
    source: str,
    reason: str | None,
    changed_by: uuid.UUID | None,
) -> None:
    PriceHistoryRepository(db).add(
        PriceHistory(
            id=uuid.uuid4(),
            organization_id=organization_id,
            store_id=price.store_id,
            product_id=price.product_id,
            old_price=old_price,
            new_price=price.selling_price,
            change_type=change_type,
            source=source,
            reason=reason,
            changed_by=changed_by,
        )
    )


def create_price(
    db: Session, *, organization_id: uuid.UUID, user_id: uuid.UUID | None, payload: PriceCreate
) -> Price:
    """user_id is None for system-triggered creation (e.g. Phase 10's
    integration sync apply step, which has no authenticated user) — Price
    .created_by is a nullable FK, so this is safe.
    """
    _validate_scope(
        db, organization_id=organization_id, product_id=payload.product_id, store_id=payload.store_id
    )

    now = utcnow()
    effective_from = payload.effective_from or now
    status = payload.status or (PriceStatus.SCHEDULED if effective_from > now else PriceStatus.ACTIVE)

    price = Price(
        id=uuid.uuid4(),
        organization_id=organization_id,
        store_id=payload.store_id,
        product_id=payload.product_id,
        price_type=payload.price_type,
        base_price=payload.base_price,
        selling_price=payload.selling_price,
        currency=payload.currency,
        effective_from=effective_from,
        effective_to=payload.effective_to,
        status=status,
        created_by=user_id,
    )
    price = PriceRepository(db).add(price)

    _record_history(
        db,
        organization_id=organization_id,
        price=price,
        old_price=None,
        change_type="created",
        source=payload.source,
        reason=payload.reason,
        changed_by=user_id,
    )
    _route_price_change(db, organization_id=organization_id, price=price)
    return price


def get_price(db: Session, *, organization_id: uuid.UUID, price_id: uuid.UUID) -> Price:
    price = PriceRepository(db).get_by_id_for_organization(price_id, organization_id)
    if price is None:
        raise NotFoundError("Price not found.", code="price_not_found")
    return price


def list_prices(
    db: Session, *, organization_id: uuid.UUID, params: PriceListParams
) -> tuple[list[Price], int]:
    offset = (params.page - 1) * params.page_size
    return PriceRepository(db).search(
        organization_id,
        product_id=params.product_id,
        store_id=params.store_id,
        price_type=params.price_type,
        status=params.status,
        offset=offset,
        limit=params.page_size,
    )


def update_price(
    db: Session, *, organization_id: uuid.UUID, user_id: uuid.UUID, price_id: uuid.UUID, payload: PriceUpdate
) -> Price:
    price = get_price(db, organization_id=organization_id, price_id=price_id)
    old_selling_price = price.selling_price

    updates = payload.model_dump(exclude_unset=True, exclude={"source", "reason"})
    for field, value in updates.items():
        setattr(price, field, value)
    price = PriceRepository(db).add(price)

    if "selling_price" in updates and updates["selling_price"] != old_selling_price:
        _record_history(
            db,
            organization_id=organization_id,
            price=price,
            old_price=old_selling_price,
            change_type="updated",
            source=payload.source,
            reason=payload.reason,
            changed_by=user_id,
        )
        _route_price_change(db, organization_id=organization_id, price=price)
    return price


def _route_price_change(db: Session, *, organization_id: uuid.UUID, price: Price) -> None:
    """The "Price Change -> Execution Event" trigger for Phase 14's Output
    Router. Fetches the Product (routing conditions match on category_id)
    and delegates to output_router_service, which is the only thing that
    knows about routing rules/output channels — kept out of this module to
    respect the Routes->Services->Repositories layering (this is a
    service-to-service call, not a repository reach-around).
    """
    product = ProductRepository(db).get_by_id_for_organization(price.product_id, organization_id)
    if product is None:
        return
    output_router_service.route_price_change(
        db, organization_id=organization_id, product=product, store_id=price.store_id, price=price
    )
