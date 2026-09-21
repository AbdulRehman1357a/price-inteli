import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import APIResponse
from app.db.session import get_db
from app.schemas.public import PublicPriceDisplay
from app.services import public_price_service

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/price/{product_id}", response_model=APIResponse[PublicPriceDisplay])
def get_public_price(
    product_id: uuid.UUID,
    store_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> APIResponse[PublicPriceDisplay]:
    """No auth — this is the public product price page QR/web outputs point
    to. Deliberately exposes only customer-facing fields (see PublicPriceDisplay).
    """
    display = public_price_service.get_public_price_display(db, product_id=product_id, store_id=store_id)
    return APIResponse(data=display)
