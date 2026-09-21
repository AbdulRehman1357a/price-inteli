import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class ExternalStore(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """External-ID mapping for stores, the byproduct of an actual Store
    entity-sync run. Distinct from app.models.integration_location.IntegrationLocation,
    which is the onboarding-time discovery/enablement record — a location
    can be discovered and enabled long before any Store entity sync ever
    populates a row here. No organization_id column — tenant scoping joins
    through integration_id.
    """

    __tablename__ = "external_stores"
    __table_args__ = (
        UniqueConstraint("integration_id", "external_id", name="uq_external_stores_integration_external"),
    )

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("stores.id"), nullable=True, index=True
    )
    store_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
