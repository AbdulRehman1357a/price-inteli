import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.competitor import CompetitorStatus
from app.models.competitor_product import CompetitorProductStatus


class CompetitorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    status: CompetitorStatus = CompetitorStatus.ACTIVE


class CompetitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    status: CompetitorStatus | None = None


class CompetitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    website: str | None
    status: CompetitorStatus
    created_at: datetime
    updated_at: datetime


class CompetitorProductCreate(BaseModel):
    product_id: uuid.UUID
    external_product_url: str | None = Field(default=None, max_length=1000)
    match_confidence: Decimal | None = Field(default=None, ge=0, le=1, max_digits=5, decimal_places=4)
    status: CompetitorProductStatus = CompetitorProductStatus.ACTIVE


class CompetitorProductUpdate(BaseModel):
    external_product_url: str | None = Field(default=None, max_length=1000)
    match_confidence: Decimal | None = Field(default=None, ge=0, le=1, max_digits=5, decimal_places=4)
    status: CompetitorProductStatus | None = None


class CompetitorProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    competitor_id: uuid.UUID
    product_id: uuid.UUID
    external_product_url: str | None
    match_confidence: Decimal | None
    status: CompetitorProductStatus
    created_at: datetime
    updated_at: datetime


class CompetitorProductDetail(CompetitorProductOut):
    product_name: str
    sku: str
    latest_price: Decimal | None
    latest_price_currency: str | None
    latest_price_captured_at: datetime | None


class ManualCompetitorPriceCreate(BaseModel):
    price: Decimal = Field(gt=0, max_digits=15, decimal_places=4)
    currency: str = Field(default="USD", min_length=1, max_length=10)
    availability: str | None = Field(default=None, max_length=50)
    captured_at: datetime | None = None


class CompetitorPriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    competitor_product_id: uuid.UUID
    price: Decimal
    currency: str
    availability: str | None
    captured_at: datetime
    source: str


class CompetitorDashboardRow(BaseModel):
    product_id: uuid.UUID
    product_name: str
    sku: str
    our_price: Decimal | None
    our_currency: str | None
    competitor_id: uuid.UUID
    competitor_name: str
    competitor_product_id: uuid.UUID
    competitor_price: Decimal | None
    competitor_currency: str | None
    competitor_availability: str | None
    captured_at: datetime | None
    price_gap: Decimal | None
    price_gap_percent: Decimal | None
    position: str
