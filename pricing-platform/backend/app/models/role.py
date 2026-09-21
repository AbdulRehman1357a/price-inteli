import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A named set of permissions.

    organization_id is nullable: system roles (is_system_role=True, e.g. the
    six built-in roles seeded for Phase 1) are global templates shared by
    every tenant and have organization_id NULL.

    cloned_from_role_id (additive, not in any literal phase spec) supports
    per-organization permission customization: a system role's permission
    set can't be edited in place — that row is shared by every tenant — so
    editing one instead forks it into an org-scoped copy (organization_id
    set, is_system_role=False) seeded from the original's permissions, and
    existing UserRole assignments for that org are migrated onto the fork.
    This column records which system role a fork originated from, so
    RoleRepository.list_assignable can show the fork in place of the
    original for that organization instead of both. See role_service.py.
    """

    __tablename__ = "roles"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cloned_from_role_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("roles.id"), nullable=True, index=True
    )

    organization: Mapped["Organization | None"] = relationship(back_populates="roles")  # noqa: F821
