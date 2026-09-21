import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.public import PublicPriceDisplay
from app.services.output_job_service import resolve_display_price


def get_public_price_display(
    db: Session, *, product_id: uuid.UUID, store_id: uuid.UUID | None
) -> PublicPriceDisplay:
    """No authentication/tenant context here by design — this is the target
    of a QR code or shelf label a customer scans, so it looks the product up
    by ID directly rather than through an organization-scoped repository
    method, exposing only customer-facing fields.
    """
    product = ProductRepository(db).get_by_id(product_id)
    if product is None:
        raise NotFoundError("Product not found.", code="product_not_found")

    store = None
    if store_id is not None:
        store = StoreRepository(db).get_by_id(store_id)
        if store is None or store.organization_id != product.organization_id:
            raise NotFoundError("Store not found.", code="store_not_found")

    price, currency = resolve_display_price(
        db, organization_id=product.organization_id, product=product, store_id=store_id
    )
    return PublicPriceDisplay(
        product_name=product.product_name,
        sku=product.sku,
        price=str(price),
        currency=currency,
        store_name=store.name if store else None,
    )
