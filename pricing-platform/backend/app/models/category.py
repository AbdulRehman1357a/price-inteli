import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CategoryStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A product category, optionally nested under a parent category to form
    a hierarchy. No soft delete — not in the Phase 3 spec, and
    CategoryService.delete blocks deletion of a category that still has
    child categories or products rather than needing to reason about
    orphaned/soft-deleted subtrees.
    """

    __tablename__ = "categories"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("categories.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CategoryStatus] = mapped_column(
        Enum(CategoryStatus, native_enum=False, length=20), nullable=False, default=CategoryStatus.ACTIVE
    )
