import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.integrations.competitors.api_provider import APICompetitorPriceProvider
from app.models.competitor import Competitor
from app.models.competitor_price import CompetitorPrice
from app.models.competitor_product import CompetitorProduct
from app.models.mixins import utcnow
from app.repositories.competitor_price_repository import CompetitorPriceRepository
from app.repositories.competitor_product_repository import CompetitorProductRepository
from app.repositories.competitor_repository import CompetitorRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.competitor import (
    CompetitorCreate,
    CompetitorDashboardRow,
    CompetitorProductCreate,
    CompetitorProductUpdate,
    CompetitorUpdate,
    ManualCompetitorPriceCreate,
)
from app.services import pricing_engine

_MONEY = Decimal("0.0001")


def create_competitor(db: Session, *, organization_id: uuid.UUID, payload: CompetitorCreate) -> Competitor:
    competitor = Competitor(
        id=uuid.uuid4(),
        organization_id=organization_id,
        name=payload.name,
        website=payload.website,
        status=payload.status,
    )
    return CompetitorRepository(db).add(competitor)


def get_competitor(db: Session, *, organization_id: uuid.UUID, competitor_id: uuid.UUID) -> Competitor:
    competitor = CompetitorRepository(db).get_by_id_for_organization(competitor_id, organization_id)
    if competitor is None:
        raise NotFoundError("Competitor not found.", code="competitor_not_found")
    return competitor


def list_competitors(db: Session, *, organization_id: uuid.UUID) -> list[Competitor]:
    return CompetitorRepository(db).list_for_organization(organization_id)


def update_competitor(
    db: Session, *, organization_id: uuid.UUID, competitor_id: uuid.UUID, payload: CompetitorUpdate
) -> Competitor:
    competitor = get_competitor(db, organization_id=organization_id, competitor_id=competitor_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(competitor, field, value)
    return CompetitorRepository(db).add(competitor)


def delete_competitor(db: Session, *, organization_id: uuid.UUID, competitor_id: uuid.UUID) -> None:
    competitor = get_competitor(db, organization_id=organization_id, competitor_id=competitor_id)
    if CompetitorProductRepository(db).list_for_competitor(competitor.id):
        raise ConflictError(
            "This competitor has tracked products and can't be deleted — remove those first.",
            code="competitor_has_products",
        )
    CompetitorRepository(db).delete(competitor)


def add_competitor_product(
    db: Session, *, organization_id: uuid.UUID, competitor_id: uuid.UUID, payload: CompetitorProductCreate
) -> CompetitorProduct:
    get_competitor(db, organization_id=organization_id, competitor_id=competitor_id)  # tenant check
    if ProductRepository(db).get_by_id_for_organization(payload.product_id, organization_id) is None:
        raise NotFoundError("Product not found.", code="product_not_found")

    competitor_product = CompetitorProduct(
        id=uuid.uuid4(),
        competitor_id=competitor_id,
        product_id=payload.product_id,
        external_product_url=payload.external_product_url,
        match_confidence=payload.match_confidence,
        status=payload.status,
    )
    return CompetitorProductRepository(db).add(competitor_product)


def get_competitor_product(
    db: Session, *, organization_id: uuid.UUID, competitor_product_id: uuid.UUID
) -> CompetitorProduct:
    competitor_product = CompetitorProductRepository(db).get_by_id_for_organization(
        competitor_product_id, organization_id
    )
    if competitor_product is None:
        raise NotFoundError("Tracked competitor product not found.", code="competitor_product_not_found")
    return competitor_product


def list_competitor_products(
    db: Session, *, organization_id: uuid.UUID, competitor_id: uuid.UUID
) -> list[CompetitorProduct]:
    get_competitor(db, organization_id=organization_id, competitor_id=competitor_id)  # tenant check
    return CompetitorProductRepository(db).list_for_competitor(competitor_id)


def update_competitor_product(
    db: Session,
    *,
    organization_id: uuid.UUID,
    competitor_product_id: uuid.UUID,
    payload: CompetitorProductUpdate,
) -> CompetitorProduct:
    competitor_product = get_competitor_product(
        db, organization_id=organization_id, competitor_product_id=competitor_product_id
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(competitor_product, field, value)
    return CompetitorProductRepository(db).add(competitor_product)


def delete_competitor_product(
    db: Session, *, organization_id: uuid.UUID, competitor_product_id: uuid.UUID
) -> None:
    competitor_product = get_competitor_product(
        db, organization_id=organization_id, competitor_product_id=competitor_product_id
    )
    if CompetitorPriceRepository(db).list_for_competitor_product(competitor_product.id, limit=1):
        raise ConflictError(
            "This tracked product has recorded price history and can't be deleted — set it to "
            "inactive instead.",
            code="competitor_product_has_prices",
        )
    CompetitorProductRepository(db).delete(competitor_product)


def record_manual_price(
    db: Session,
    *,
    organization_id: uuid.UUID,
    competitor_product_id: uuid.UUID,
    payload: ManualCompetitorPriceCreate,
) -> CompetitorPrice:
    get_competitor_product(db, organization_id=organization_id, competitor_product_id=competitor_product_id)
    price = CompetitorPrice(
        id=uuid.uuid4(),
        competitor_product_id=competitor_product_id,
        price=payload.price,
        currency=payload.currency,
        availability=payload.availability,
        captured_at=payload.captured_at or utcnow(),
        source="manual",
    )
    return CompetitorPriceRepository(db).add(price)


def sync_price_from_api(
    db: Session, *, organization_id: uuid.UUID, competitor_product_id: uuid.UUID
) -> CompetitorPrice:
    """The authorized-API ingestion path — see
    app/integrations/competitors/api_provider.py's docstring for what
    "authorized" means here.
    """
    competitor_product = get_competitor_product(
        db, organization_id=organization_id, competitor_product_id=competitor_product_id
    )
    if not competitor_product.external_product_url:
        raise ValidationError("This tracked product has no external_product_url configured.")

    observation = APICompetitorPriceProvider().fetch_price(competitor_product.external_product_url)
    price = CompetitorPrice(
        id=uuid.uuid4(),
        competitor_product_id=competitor_product.id,
        price=observation.price,
        currency=observation.currency,
        availability=observation.availability,
        captured_at=utcnow(),
        source="api",
    )
    return CompetitorPriceRepository(db).add(price)


def list_prices(
    db: Session, *, organization_id: uuid.UUID, competitor_product_id: uuid.UUID, limit: int = 20
) -> list[CompetitorPrice]:
    get_competitor_product(db, organization_id=organization_id, competitor_product_id=competitor_product_id)
    return CompetitorPriceRepository(db).list_for_competitor_product(competitor_product_id, limit=limit)


def get_dashboard(db: Session, *, organization_id: uuid.UUID) -> list[CompetitorDashboardRow]:
    competitor_products = CompetitorProductRepository(db).list_for_organization(organization_id)
    if not competitor_products:
        return []

    price_repo = CompetitorPriceRepository(db)
    latest_by_cp_id = price_repo.list_latest_for_competitor_products([cp.id for cp in competitor_products])

    competitor_repo = CompetitorRepository(db)
    competitors_by_id = {c.id: c for c in competitor_repo.list_for_organization(organization_id)}
    product_repo = ProductRepository(db)

    now = utcnow()
    rows: list[CompetitorDashboardRow] = []
    for cp in competitor_products:
        product = product_repo.get_by_id(cp.product_id)
        competitor = competitors_by_id.get(cp.competitor_id)
        if product is None or competitor is None:
            continue

        our_price = pricing_engine.evaluate_for_product(
            db, organization_id=organization_id, product=product, store_id=None, now=now
        ).current_price

        latest = latest_by_cp_id.get(cp.id)
        competitor_price = latest.price if latest else None

        price_gap = None
        price_gap_percent = None
        position = "unknown"
        if competitor_price is not None:
            price_gap = (our_price - competitor_price).quantize(_MONEY)
            if competitor_price > 0:
                price_gap_percent = (price_gap / competitor_price * Decimal("100")).quantize(Decimal("0.01"))
            if price_gap > 0:
                position = "more_expensive"
            elif price_gap < 0:
                position = "cheaper"
            else:
                position = "match"

        rows.append(
            CompetitorDashboardRow(
                product_id=product.id,
                product_name=product.product_name,
                sku=product.sku,
                our_price=our_price,
                our_currency=product.currency or "USD",
                competitor_id=competitor.id,
                competitor_name=competitor.name,
                competitor_product_id=cp.id,
                competitor_price=competitor_price,
                competitor_currency=latest.currency if latest else None,
                competitor_availability=latest.availability if latest else None,
                captured_at=latest.captured_at if latest else None,
                price_gap=price_gap,
                price_gap_percent=price_gap_percent,
                position=position,
            )
        )
    return rows
