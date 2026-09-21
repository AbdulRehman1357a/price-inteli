import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class IntegrationLocation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One external store location discovered during onboarding (Setup
    Checklist's "discover/select locations" step) — POST
    /integrations/{id}/locations/discover upserts these from
    adapter.fetch_records(entity_type="store"). Distinct from
    app.models.external_store.ExternalStore: this table is the
    onboarding-time discovery/enablement record (before a location is
    necessarily linked to a PIP store or has ever been synced), while
    ExternalStore is the external-ID-mapping byproduct of an actual Store
    entity-sync run. No organization_id column — tenant scoping joins
    through integration_id, same as IntegrationMapping/IntegrationSyncJob.
    """

    __tablename__ = "integration_locations"
    __table_args__ = (
        UniqueConstraint(
            "integration_id", "external_location_id", name="uq_integration_locations_integration_external"
        ),
    )

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("stores.id"), nullable=True, index=True
    )
    external_location_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_location_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    linked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
