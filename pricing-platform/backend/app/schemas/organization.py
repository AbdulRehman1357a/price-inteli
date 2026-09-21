import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.organization import OrganizationStatus


class OrganizationUpdate(BaseModel):
    """Company details a tenant admin may edit. slug and status are
    deliberately excluded: slug is an immutable identifier and status is
    system/admin-controlled outside this endpoint.
    """

    name: str | None = Field(default=None, min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    website: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, max_length=100)
    timezone: str | None = Field(default=None, min_length=1, max_length=100)
    currency: str | None = Field(default=None, min_length=1, max_length=10)


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    legal_name: str | None
    slug: str
    email: str
    phone: str | None
    website: str | None
    country: str | None
    timezone: str
    currency: str
    status: OrganizationStatus
    created_at: datetime
    updated_at: datetime
