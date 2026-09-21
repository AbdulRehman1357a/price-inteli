import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.price import PriceStatus, PriceType
from app.schemas.common import PaginationParams


class PriceCreate(BaseModel):
    """organization_id is deliberately absent — it always comes from the
    authenticated tenant context, never the request body. reason/source
    aren't Price columns — they're forwarded into the PriceHistory row this
    creates (every applied price must create price history).
    """

    store_id: uuid.UUID | None = None
    product_id: uuid.UUID
    price_type: PriceType = PriceType.REGULAR
    base_price: Decimal = Field(max_digits=15, decimal_places=4, ge=0)
    selling_price: Decimal = Field(max_digits=15, decimal_places=4, ge=0)
    currency: str = Field(min_length=1, max_length=10)
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    status: PriceStatus | None = None
    source: str = Field(default="manual", max_length=255)
    reason: str | None = None


class PriceUpdate(BaseModel):
    """All fields optional (exclude_unset pattern). Any change to
    selling_price writes a new PriceHistory row.
    """

    price_type: PriceType | None = None
    base_price: Decimal | None = Field(default=None, max_digits=15, decimal_places=4, ge=0)
    selling_price: Decimal | None = Field(default=None, max_digits=15, decimal_places=4, ge=0)
    currency: str | None = Field(default=None, min_length=1, max_length=10)
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    status: PriceStatus | None = None
    source: str = Field(default="manual", max_length=255)
    reason: str | None = None


class PriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    store_id: uuid.UUID | None
    product_id: uuid.UUID
    price_type: PriceType
    base_price: Decimal
    selling_price: Decimal
    currency: str
    effective_from: datetime
    effective_to: datetime | None
    status: PriceStatus
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class PriceListParams(PaginationParams):
    product_id: uuid.UUID | None = None
    store_id: uuid.UUID | None = None
    price_type: PriceType | None = None
    status: PriceStatus | None = None


class PriceHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    store_id: uuid.UUID | None
    old_price: Decimal | None
    new_price: Decimal
    change_type: str
    source: str
    reason: str | None
    changed_by: uuid.UUID | None
    created_at: datetime
