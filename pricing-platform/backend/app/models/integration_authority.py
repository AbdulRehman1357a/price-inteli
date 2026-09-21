import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.integration_mapping import CanonicalEntityType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AuthoritySource(enum.StrEnum):
    """Which system is the source of truth for a governed field. "pip"
    means PIP itself owns the value (inbound sync for that field is
    blocked unless allow_override is set); "external" means the connected
    system owns it (today's default behavior when no row exists at all —
    see app.services.integration_authority_service.may_apply).
    """

    PIP = "pip"
    EXTERNAL = "external"


class IntegrationAuthority(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Source-of-truth configuration for one (entity_type, field_name) pair
    on one integration — app.services.integration_authority_service checks
    this before every inbound apply_* write. field_name="*" is a wildcard
    covering the whole entity when no more specific row exists. No
    organization_id column — tenant scoping joins through integration_id.
    """

    __tablename__ = "integration_authorities"
    __table_args__ = (
        UniqueConstraint(
            "integration_id",
            "entity_type",
            "field_name",
            name="uq_integration_authorities_integration_entity_field",
        ),
    )

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    entity_type: Mapped[CanonicalEntityType] = mapped_column(
        Enum(CanonicalEntityType, native_enum=False, length=20), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    authority: Mapped[AuthoritySource] = mapped_column(
        Enum(AuthoritySource, native_enum=False, length=10), nullable=False
    )
    # If True, a conflicting inbound value is still applied but logged to
    # IntegrationReconciliation instead of being blocked outright — the
    # "allow, but flag for review" escape hatch.
    allow_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
