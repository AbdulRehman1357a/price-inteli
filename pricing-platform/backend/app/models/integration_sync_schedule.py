import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.integration_mapping import CanonicalEntityType
from app.models.integration_sync_job import IntegrationSyncJobType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class IntegrationSyncSchedule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Fixed-interval periodic sync configuration for one (integration,
    entity_type) pair. Deliberately interval-based (not cron) — a static
    Celery Beat entry per integration isn't possible, so one beat task
    (app.services.integration_schedule_service.dispatch_due_schedules,
    every minute) scans these rows for whichever are due, which only needs
    a simple "next_run_at <= now" comparison. No organization_id column —
    tenant scoping joins through integration_id.
    """

    __tablename__ = "integration_sync_schedules"
    __table_args__ = (
        UniqueConstraint(
            "integration_id", "entity_type", name="uq_integration_sync_schedules_integration_entity"
        ),
    )

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    entity_type: Mapped[CanonicalEntityType] = mapped_column(
        Enum(CanonicalEntityType, native_enum=False, length=20), nullable=False
    )
    job_type: Mapped[IntegrationSyncJobType] = mapped_column(
        Enum(IntegrationSyncJobType, native_enum=False, length=20),
        nullable=False,
        default=IntegrationSyncJobType.INCREMENTAL_SYNC,
    )
    interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    last_dispatched_job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integration_sync_jobs.id"), nullable=True
    )
