import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.store import StoreStatus
from app.schemas.common import PaginationParams


class StoreBase(BaseModel):
    """Every field the client may set. organization_id is deliberately absent —
    it always comes from the authenticated tenant context (current_user.organization_id
    in the route/service layer), never from the request body.
    """

    store_code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    store_type: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    country: str = Field(min_length=1, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    postal_code: str | None = Field(default=None, max_length=30)
    address_line_1: str = Field(min_length=1, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    timezone: str = Field(min_length=1, max_length=100)
    currency: str = Field(min_length=1, max_length=10)
    status: StoreStatus = StoreStatus.ACTIVE
    opening_date: date | None = None


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    """All fields optional: only keys present in the request body are applied
    (see StoreService.update — uses model_dump(exclude_unset=True)), so a
    partial edit doesn't clobber fields the client didn't send.
    """

    store_code: str | None = Field(default=None, min_length=1, max_length=100)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    store_type: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    postal_code: str | None = Field(default=None, max_length=30)
    address_line_1: str | None = Field(default=None, min_length=1, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    timezone: str | None = Field(default=None, min_length=1, max_length=100)
    currency: str | None = Field(default=None, min_length=1, max_length=10)
    status: StoreStatus | None = None
    opening_date: date | None = None


class StoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    store_code: str
    name: str
    legal_name: str | None
    store_type: str | None
    email: str | None
    phone: str | None
    country: str
    state: str | None
    city: str
    postal_code: str | None
    address_line_1: str
    address_line_2: str | None
    timezone: str
    currency: str
    status: StoreStatus
    opening_date: date | None
    created_at: datetime
    updated_at: datetime


class StoreListParams(PaginationParams):
    search: str | None = Field(default=None, description="Matches store_code, name, or city")
    status: StoreStatus | None = None
    store_type: str | None = None
