import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.category import CategoryStatus
from app.schemas.common import PaginationParams


class CategoryBase(BaseModel):
    """organization_id is deliberately absent — it always comes from the
    authenticated tenant context, never the request body.
    """

    parent_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=100)
    description: str | None = None
    status: CategoryStatus = CategoryStatus.ACTIVE


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    """All fields optional: only keys present in the request body are applied
    (service uses model_dump(exclude_unset=True)).
    """

    parent_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=100)
    description: str | None = None
    status: CategoryStatus | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    parent_id: uuid.UUID | None
    name: str
    code: str | None
    description: str | None
    status: CategoryStatus
    created_at: datetime
    updated_at: datetime


class CategoryListParams(PaginationParams):
    search: str | None = Field(default=None, description="Matches name or code")
    status: CategoryStatus | None = None
    sort: str | None = Field(
        default=None, description="One of: name, -name, created_at, -created_at (default)"
    )
