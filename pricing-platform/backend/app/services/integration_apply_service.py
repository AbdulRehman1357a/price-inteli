import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.external_inventory import ExternalInventory
from app.models.external_order import ExternalOrder
from app.models.external_price import ExternalPrice
from app.models.external_product import ExternalProduct
from app.models.external_promotion import ExternalPromotion, ExternalPromotionStatus
from app.models.external_store import ExternalStore
from app.models.integration_authority import AuthoritySource
from app.models.integration_mapping import CanonicalEntityType
from app.models.integration_sync_job import IntegrationSyncDirection
from app.models.inventory import Inventory
from app.models.mixins import utcnow
from app.models.product import Product
from app.models.store import Store
from app.repositories.category_repository import CategoryRepository
from app.repositories.external_inventory_repository import ExternalInventoryRepository
from app.repositories.external_order_repository import ExternalOrderRepository
from app.repositories.external_price_repository import ExternalPriceRepository
from app.repositories.external_product_repository import ExternalProductRepository
from app.repositories.external_promotion_repository import ExternalPromotionRepository
from app.repositories.external_store_repository import ExternalStoreRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.canonical import (
    CanonicalInventory,
    CanonicalOrder,
    CanonicalPrice,
    CanonicalProduct,
    CanonicalPromotion,
    CanonicalStore,
)
from app.schemas.price import PriceCreate
from app.services import integration_authority_service, price_service


class ApplyError(Exception):
    """A canonical record couldn't be reconciled into the domain tables —
    caught per-record by the sync worker (app.services.integration_sync_service)
    so one bad row doesn't abort the whole sync run, mirroring Phase 5's
    per-row _RowValidationError handling.
    """


def _maybe_log_override(
    db: Session,
    *,
    authority,
    integration_id: uuid.UUID,
    entity_type: CanonicalEntityType,
    external_id: str,
    field_name: str,
    pip_value: str | None,
    external_value: str | None,
) -> None:
    if authority is not None and authority.authority == AuthoritySource.PIP and authority.allow_override:
        integration_authority_service.log_override(
            db,
            integration_id=integration_id,
            entity_type=entity_type,
            external_id=external_id,
            field_name=field_name,
            pip_value=pip_value,
            external_value=external_value,
        )


@dataclass
class ApplyResult:
    """Every apply_* function's return shape (Phase 10 upgrade) — lets
    integration_sync_service._run() tally records_created/records_updated/
    records_skipped instead of a single records_processed count.
    "skipped" covers both the authority-allowed-but-logged case (handled by
    the caller before apply_* even runs) and the loop-prevention
    skip-if-unchanged case inside apply_price.
    """

    status: Literal["created", "updated", "skipped"]
    entity_id: uuid.UUID | None = None


def apply_product(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, canonical: CanonicalProduct
) -> ApplyResult:
    allowed, authority = integration_authority_service.may_apply(
        db, integration_id=integration_id, entity_type=CanonicalEntityType.PRODUCT, field_name="*"
    )
    if not allowed:
        raise integration_authority_service.AuthorityBlockedError(
            "PIP is configured as the authority for products on this integration — "
            "the inbound record was not applied.",
        )
    _maybe_log_override(
        db,
        authority=authority,
        integration_id=integration_id,
        entity_type=CanonicalEntityType.PRODUCT,
        external_id=canonical.external_id or canonical.sku,
        field_name="*",
        pip_value=None,
        external_value=None,
    )

    if canonical.selling_price is None:
        raise ApplyError("selling_price is required to create/update a product.")

    category = None
    if canonical.category:
        category_repo = CategoryRepository(db)
        category = category_repo.get_by_name(organization_id, canonical.category)
        if category is None:
            category = category_repo.add(
                Category(id=uuid.uuid4(), organization_id=organization_id, name=canonical.category)
            )
    if category is None:
        raise ApplyError("category is required to create/update a product.")

    product_repo = ProductRepository(db)
    existing = product_repo.get_by_sku(organization_id, canonical.sku)
    if existing is not None:
        existing.product_name = canonical.product_name
        existing.category_id = category.id
        existing.selling_price = canonical.selling_price
        if canonical.cost_price is not None:
            existing.cost_price = canonical.cost_price
        if canonical.barcode:
            existing.barcode = canonical.barcode
        if canonical.currency:
            existing.currency = canonical.currency
        product = product_repo.add(existing)
        status: Literal["created", "updated"] = "updated"
    else:
        product = product_repo.add(
            Product(
                id=uuid.uuid4(),
                organization_id=organization_id,
                category_id=category.id,
                sku=canonical.sku,
                product_name=canonical.product_name,
                barcode=canonical.barcode,
                cost_price=canonical.cost_price,
                selling_price=canonical.selling_price,
                currency=canonical.currency,
            )
        )
        status = "created"

    _upsert_external_product(db, integration_id=integration_id, canonical=canonical, product=product)
    return ApplyResult(status=status, entity_id=product.id)


def _upsert_external_product(
    db: Session, *, integration_id: uuid.UUID, canonical: CanonicalProduct, product: Product
) -> None:
    if not canonical.external_id:
        return
    repo = ExternalProductRepository(db)
    existing = repo.get_by_external_id(integration_id, canonical.external_id)
    now = utcnow()
    if existing is not None:
        existing.external_variant_id = canonical.external_variant_id
        existing.sku = canonical.sku
        existing.product_id = product.id
        existing.last_synced_at = now
        repo.add(existing)
        return
    repo.add(
        ExternalProduct(
            id=uuid.uuid4(),
            integration_id=integration_id,
            external_id=canonical.external_id,
            external_variant_id=canonical.external_variant_id,
            sku=canonical.sku,
            product_id=product.id,
            last_synced_at=now,
        )
    )


def apply_price(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, canonical: CanonicalPrice
) -> ApplyResult:
    allowed, authority = integration_authority_service.may_apply(
        db, integration_id=integration_id, entity_type=CanonicalEntityType.PRICE, field_name="selling_price"
    )
    if not allowed:
        raise integration_authority_service.AuthorityBlockedError(
            "PIP is configured as the authority for prices on this integration — "
            "the inbound record was not applied.",
        )

    product = ProductRepository(db).get_by_sku(organization_id, canonical.sku)
    if product is None:
        raise ApplyError(f"Unknown SKU {canonical.sku!r} — the product must exist first.")

    store_id = None
    if canonical.store_code:
        store = StoreRepository(db).get_by_code(organization_id, canonical.store_code)
        if store is None:
            raise ApplyError(f"Unknown store code {canonical.store_code!r}.")
        store_id = store.id

    # Loop-prevention: if the incoming value already matches what PIP has
    # on record, skip writing a new Price row entirely. This is what keeps
    # a provider echoing PIP's own outbound push back through inbound
    # sync/webhook from creating an infinite create-new-Price loop — it's
    # provider-agnostic (doesn't rely on the provider round-tripping a
    # correlation id PIP sent it).
    latest = PriceRepository(db).get_latest_for_product_store(
        organization_id, product_id=product.id, store_id=store_id
    )

    _maybe_log_override(
        db,
        authority=authority,
        integration_id=integration_id,
        entity_type=CanonicalEntityType.PRICE,
        external_id=f"{canonical.sku}@{canonical.store_code or ''}",
        field_name="selling_price",
        pip_value=str(latest.selling_price) if latest is not None else None,
        external_value=str(canonical.selling_price),
    )

    if (
        latest is not None
        and latest.selling_price == canonical.selling_price
        and latest.currency == canonical.currency
    ):
        _upsert_external_price(
            db,
            integration_id=integration_id,
            canonical=canonical,
            store_code=canonical.store_code,
            price=latest,
        )
        return ApplyResult(status="skipped", entity_id=latest.id)

    price = price_service.create_price(
        db,
        organization_id=organization_id,
        user_id=None,
        payload=PriceCreate(
            store_id=store_id,
            product_id=product.id,
            base_price=canonical.selling_price,
            selling_price=canonical.selling_price,
            currency=canonical.currency,
            effective_from=canonical.effective_from,
        ),
    )
    _upsert_external_price(
        db, integration_id=integration_id, canonical=canonical, store_code=canonical.store_code, price=price
    )
    return ApplyResult(status="created", entity_id=price.id)


def _upsert_external_price(
    db: Session, *, integration_id: uuid.UUID, canonical: CanonicalPrice, store_code: str | None, price
) -> None:
    repo = ExternalPriceRepository(db)
    existing = repo.get_by_sku_store(integration_id, sku=canonical.sku, store_code=store_code)
    now = utcnow()
    if existing is not None:
        existing.price_id = price.id
        existing.external_selling_price = canonical.selling_price
        existing.currency = canonical.currency
        existing.direction = IntegrationSyncDirection.INBOUND
        existing.last_synced_at = now
        repo.add(existing)
        return
    repo.add(
        ExternalPrice(
            id=uuid.uuid4(),
            integration_id=integration_id,
            sku=canonical.sku,
            store_code=store_code,
            price_id=price.id,
            external_selling_price=canonical.selling_price,
            currency=canonical.currency,
            direction=IntegrationSyncDirection.INBOUND,
            last_synced_at=now,
        )
    )


def apply_inventory(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, canonical: CanonicalInventory
) -> ApplyResult:
    allowed, authority = integration_authority_service.may_apply(
        db,
        integration_id=integration_id,
        entity_type=CanonicalEntityType.INVENTORY,
        field_name="quantity_on_hand",
    )
    if not allowed:
        raise integration_authority_service.AuthorityBlockedError(
            "PIP is configured as the authority for inventory on this integration — "
            "the inbound record was not applied.",
        )

    product = ProductRepository(db).get_by_sku(organization_id, canonical.sku)
    if product is None:
        raise ApplyError(f"Unknown SKU {canonical.sku!r} — the product must exist first.")
    store = StoreRepository(db).get_by_code(organization_id, canonical.store_code)
    if store is None:
        raise ApplyError(f"Unknown store code {canonical.store_code!r}.")

    inventory_repo = InventoryRepository(db)
    existing = inventory_repo.get_by_store_and_product(organization_id, store.id, product.id)
    _maybe_log_override(
        db,
        authority=authority,
        integration_id=integration_id,
        entity_type=CanonicalEntityType.INVENTORY,
        external_id=f"{canonical.sku}@{canonical.store_code}",
        field_name="quantity_on_hand",
        pip_value=str(existing.quantity_on_hand) if existing is not None else None,
        external_value=str(canonical.quantity_on_hand),
    )
    now = datetime.now(UTC)
    if existing is not None:
        existing.quantity_on_hand = canonical.quantity_on_hand
        existing.quantity_available = existing.quantity_on_hand - existing.quantity_reserved
        existing.last_stock_update_at = now
        inventory = inventory_repo.add(existing)
        status: Literal["created", "updated"] = "updated"
    else:
        inventory = inventory_repo.add(
            Inventory(
                id=uuid.uuid4(),
                organization_id=organization_id,
                store_id=store.id,
                product_id=product.id,
                quantity_on_hand=canonical.quantity_on_hand,
                quantity_available=canonical.quantity_on_hand,
                last_stock_update_at=now,
            )
        )
        status = "created"

    _upsert_external_inventory(db, integration_id=integration_id, canonical=canonical, inventory=inventory)
    return ApplyResult(status=status, entity_id=inventory.id)


def _upsert_external_inventory(
    db: Session, *, integration_id: uuid.UUID, canonical: CanonicalInventory, inventory: Inventory
) -> None:
    repo = ExternalInventoryRepository(db)
    existing = repo.get_by_sku_store(integration_id, sku=canonical.sku, store_code=canonical.store_code)
    now = utcnow()
    if existing is not None:
        existing.inventory_id = inventory.id
        existing.quantity_on_hand = canonical.quantity_on_hand
        existing.last_synced_at = now
        repo.add(existing)
        return
    repo.add(
        ExternalInventory(
            id=uuid.uuid4(),
            integration_id=integration_id,
            sku=canonical.sku,
            store_code=canonical.store_code,
            inventory_id=inventory.id,
            quantity_on_hand=canonical.quantity_on_hand,
            last_synced_at=now,
        )
    )


def apply_store(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, canonical: CanonicalStore
) -> ApplyResult:
    allowed, authority = integration_authority_service.may_apply(
        db, integration_id=integration_id, entity_type=CanonicalEntityType.STORE, field_name="*"
    )
    if not allowed:
        raise integration_authority_service.AuthorityBlockedError(
            "PIP is configured as the authority for stores on this integration — "
            "the inbound record was not applied.",
        )
    _maybe_log_override(
        db,
        authority=authority,
        integration_id=integration_id,
        entity_type=CanonicalEntityType.STORE,
        external_id=canonical.external_id or canonical.store_code,
        field_name="*",
        pip_value=None,
        external_value=None,
    )

    store_repo = StoreRepository(db)
    existing = store_repo.get_by_code(organization_id, canonical.store_code)
    if existing is not None:
        existing.name = canonical.name
        if canonical.city:
            existing.city = canonical.city
        if canonical.country:
            existing.country = canonical.country
        store = store_repo.add(existing)
        status: Literal["created", "updated"] = "updated"
    else:
        store = store_repo.add(
            Store(
                id=uuid.uuid4(),
                organization_id=organization_id,
                store_code=canonical.store_code,
                name=canonical.name,
                city=canonical.city or "Unknown",
                country=canonical.country or "Unknown",
                address_line_1=canonical.address_line_1 or "Unknown",
                timezone=canonical.timezone or "UTC",
                currency=canonical.currency or "USD",
            )
        )
        status = "created"

    if canonical.external_id:
        ext_repo = ExternalStoreRepository(db)
        existing_ext = ext_repo.get_by_external_id(integration_id, canonical.external_id)
        now = utcnow()
        if existing_ext is not None:
            existing_ext.store_id = store.id
            existing_ext.store_code = canonical.store_code
            existing_ext.last_synced_at = now
            ext_repo.add(existing_ext)
        else:
            ext_repo.add(
                ExternalStore(
                    id=uuid.uuid4(),
                    integration_id=integration_id,
                    external_id=canonical.external_id,
                    store_id=store.id,
                    store_code=canonical.store_code,
                    last_synced_at=now,
                )
            )

    return ApplyResult(status=status, entity_id=store.id)


def apply_promotion(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, canonical: CanonicalPromotion
) -> ApplyResult:
    """The platform has no persisted, pricing-engine-integrated Promotion
    entity (see app.schemas.canonical.CanonicalPromotion's docstring), so
    this stages the record into ExternalPromotion — synced end-to-end and
    queryable — rather than either failing outright or fabricating a
    promotions feature that isn't built.
    """
    del organization_id  # promotions are staged, not applied against organization-scoped domain tables

    allowed, authority = integration_authority_service.may_apply(
        db, integration_id=integration_id, entity_type=CanonicalEntityType.PROMOTION, field_name="*"
    )
    if not allowed:
        raise integration_authority_service.AuthorityBlockedError(
            "PIP is configured as the authority for promotions on this integration — "
            "the inbound record was not applied.",
        )

    if not canonical.external_id:
        raise ApplyError(
            "Promotion sync requires external_id — it's the only stable dedup key for staging "
            "a promotion (name alone isn't unique)."
        )
    _maybe_log_override(
        db,
        authority=authority,
        integration_id=integration_id,
        entity_type=CanonicalEntityType.PROMOTION,
        external_id=canonical.external_id,
        field_name="*",
        pip_value=None,
        external_value=None,
    )

    now = utcnow()
    computed_status = _compute_promotion_status(canonical.start_date, canonical.end_date, now)

    repo = ExternalPromotionRepository(db)
    existing = repo.get_by_external_promotion_id(integration_id, canonical.external_id)
    if existing is not None:
        existing.name = canonical.name
        existing.sku = canonical.sku
        existing.discount_percentage = canonical.discount_percentage
        existing.discount_amount = canonical.discount_amount
        existing.start_date = canonical.start_date
        existing.end_date = canonical.end_date
        existing.status = computed_status
        existing.synced_at = now
        promotion = repo.add(existing)
        return ApplyResult(status="updated", entity_id=promotion.id)

    promotion = repo.add(
        ExternalPromotion(
            id=uuid.uuid4(),
            integration_id=integration_id,
            external_promotion_id=canonical.external_id,
            name=canonical.name,
            sku=canonical.sku,
            discount_percentage=canonical.discount_percentage,
            discount_amount=canonical.discount_amount,
            start_date=canonical.start_date,
            end_date=canonical.end_date,
            status=computed_status,
            synced_at=now,
        )
    )
    return ApplyResult(status="created", entity_id=promotion.id)


def _compute_promotion_status(
    start_date: datetime | None, end_date: datetime | None, now: datetime
) -> ExternalPromotionStatus:
    """Providers don't agree on a status vocabulary, so status is derived
    from the dates PIP actually received rather than synced verbatim.
    """

    def _aware(value: datetime) -> datetime:
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)

    if end_date is not None and _aware(end_date) < now:
        return ExternalPromotionStatus.EXPIRED
    if start_date is not None and _aware(start_date) > now:
        return ExternalPromotionStatus.PENDING
    return ExternalPromotionStatus.ACTIVE


def apply_order(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, canonical: CanonicalOrder
) -> ApplyResult:
    """Sales/order sync (Phase 10 upgrade) — staged into ExternalOrder for
    future analytics use, same "queryable but not domain-integrated"
    pattern as apply_promotion. There is no persisted domain Order entity
    to reconcile into.
    """
    del organization_id  # orders are staged, not applied against organization-scoped domain tables

    allowed, authority = integration_authority_service.may_apply(
        db, integration_id=integration_id, entity_type=CanonicalEntityType.ORDER, field_name="*"
    )
    if not allowed:
        raise integration_authority_service.AuthorityBlockedError(
            "PIP is configured as the authority for orders on this integration — "
            "the inbound record was not applied.",
        )
    _maybe_log_override(
        db,
        authority=authority,
        integration_id=integration_id,
        entity_type=CanonicalEntityType.ORDER,
        external_id=canonical.external_id,
        field_name="*",
        pip_value=None,
        external_value=None,
    )

    now = utcnow()
    line_items = [line.model_dump(mode="json") for line in canonical.lines]

    repo = ExternalOrderRepository(db)
    existing = repo.get_by_external_order_id(integration_id, canonical.external_id)
    if existing is not None:
        existing.store_code = canonical.store_code
        existing.order_date = canonical.order_date
        existing.status = canonical.status
        existing.currency = canonical.currency
        existing.subtotal = canonical.subtotal
        existing.tax_total = canonical.tax_total
        existing.total = canonical.total
        existing.line_items = line_items
        existing.synced_at = now
        order = repo.add(existing)
        return ApplyResult(status="updated", entity_id=order.id)

    order = repo.add(
        ExternalOrder(
            id=uuid.uuid4(),
            integration_id=integration_id,
            external_order_id=canonical.external_id,
            store_code=canonical.store_code,
            order_date=canonical.order_date,
            status=canonical.status,
            currency=canonical.currency,
            subtotal=canonical.subtotal,
            tax_total=canonical.tax_total,
            total=canonical.total,
            line_items=line_items,
            synced_at=now,
        )
    )
    return ApplyResult(status="created", entity_id=order.id)
