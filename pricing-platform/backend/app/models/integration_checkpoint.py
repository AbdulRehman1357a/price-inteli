import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.integration_mapping import CanonicalEntityType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class IntegrationCheckpoint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Incremental-sync watermark for one (integration, entity_type) pair.
    cursor_value is deliberately opaque/adapter-defined (a page token, a
    change-version number, an updated-since timestamp serialized as text —
    whichever shape the adapter's own incremental API expects) rather than
    a typed column, since different providers' incremental mechanisms are
    genuinely different shapes. No organization_id column — tenant scoping
    joins through integration_id.
    """

    __tablename__ = "integration_checkpoints"
    __table_args__ = (
        UniqueConstraint(
            "integration_id", "entity_type", name="uq_integration_checkpoints_integration_entity"
        ),
    )

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    entity_type: Mapped[CanonicalEntityType] = mapped_column(
        Enum(CanonicalEntityType, native_enum=False, length=20), nullable=False
    )
    cursor_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
