import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.integration_mapping import CanonicalEntityType
from app.models.mixins import UUIDPrimaryKeyMixin, utcnow


class IntegrationWebhookEventStatus(enum.StrEnum):
    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class IntegrationWebhookEvent(UUIDPrimaryKeyMixin, Base):
    """One inbound webhook delivery
    (app/api/v1/integration_webhooks.py -> app.services.integration_webhook_service).
    The UniqueConstraint on (integration_id, provider_event_id) *is* the
    dedup/idempotency mechanism (spec section 5/32/18) — a redelivered
    event is detected by an existence check before any processing and
    marked "duplicate" rather than reprocessed. No organization_id column
    (tenant scoping joins through integration_id) and no TimestampMixin —
    received_at serves as creation time, matching IntegrationSyncJob's own
    started_at precedent.
    """

    __tablename__ = "integration_webhook_events"
    __table_args__ = (
        UniqueConstraint(
            "integration_id", "provider_event_id", name="uq_integration_webhook_events_integration_event"
        ),
    )

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    provider_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[CanonicalEntityType | None] = mapped_column(
        Enum(CanonicalEntityType, native_enum=False, length=20), nullable=True
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    signature_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[IntegrationWebhookEventStatus] = mapped_column(
        Enum(IntegrationWebhookEventStatus, native_enum=False, length=20),
        nullable=False,
        default=IntegrationWebhookEventStatus.RECEIVED,
    )
    sync_job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integration_sync_jobs.id"), nullable=True
    )
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
