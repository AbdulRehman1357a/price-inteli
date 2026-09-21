import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class IntegrationErrorSeverity(enum.StrEnum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IntegrationError(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """A structured, resolvable error record spanning every Phase 10
    operation kind (sync, webhook, outbound push) — distinct from
    IntegrationSyncJob.error_details, which is a per-job JSON blob of
    per-record failures for *that job only*. This table is what the
    Integration Errors tab / health dashboard reads, and what an admin
    marks resolved. error_type uses the same coarse vocabulary as
    IntegrationSyncJob.error_type. No organization_id column — tenant
    scoping joins through integration_id.
    """

    __tablename__ = "integration_errors"

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    sync_job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("integration_sync_jobs.id"),
        nullable=True,
        index=True,
    )
    error_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[IntegrationErrorSeverity] = mapped_column(
        Enum(IntegrationErrorSeverity, native_enum=False, length=10),
        nullable=False,
        default=IntegrationErrorSeverity.ERROR,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # No FK to users.id — matches AuditMixin's existing convention of a
    # plain, unenforced UUID column for "who did this."
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), nullable=True
    )
