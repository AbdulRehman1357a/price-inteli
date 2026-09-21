import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.integration_mapping import CanonicalEntityType
from app.models.mixins import UUIDPrimaryKeyMixin, utcnow


class IntegrationSyncJobType(enum.StrEnum):
    FULL_SYNC = "full_sync"
    INCREMENTAL_SYNC = "incremental_sync"


class IntegrationSyncJobStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class IntegrationSyncDirection(enum.StrEnum):
    """Which way data moved for this job. Inbound (External -> PIP) is the
    only direction the original Phase 10 implementation supported;
    outbound (PIP -> External, see app.services.integration_push_service)
    is added in the Phase 10 upgrade for approved-price execution.
    """

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class IntegrationSyncJob(UUIDPrimaryKeyMixin, Base):
    """One background sync run (app/services/integration_sync_service.py,
    dispatched via app/tasks/integrations.py). No organization_id column
    per the literal Phase 10 spec — tenant scoping joins through
    integration_id to Integration.organization_id, same pattern as Phase
    8/9's device_sync_logs/esl_integrations. No created_at column either —
    started_at is set at job-creation time and serves as it.
    """

    __tablename__ = "integration_sync_jobs"

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    job_type: Mapped[IntegrationSyncJobType] = mapped_column(
        Enum(IntegrationSyncJobType, native_enum=False, length=20), nullable=False
    )
    # Not in the literal Phase 10 DB spec — added because a sync job
    # genuinely can't run (or be retried) without knowing which canonical
    # entity type to fetch/apply: CSV/REST adapters pull from one
    # entity-shaped source per call (app/integrations/base.py's
    # fetch_records(entity_type=...)), so "sync everything at once" isn't
    # meaningful the way it is for, say, a full ERP export. Same additive
    # precedent as Device.esl_integration_id in Phase 9.
    entity_type: Mapped[CanonicalEntityType] = mapped_column(
        Enum(CanonicalEntityType, native_enum=False, length=20), nullable=False
    )
    status: Mapped[IntegrationSyncJobStatus] = mapped_column(
        Enum(IntegrationSyncJobStatus, native_enum=False, length=25),
        nullable=False,
        default=IntegrationSyncJobStatus.PENDING,
    )
    records_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # A list of {"record": ..., "field": ..., "message": ...} entries — one
    # per failed record, mirroring Phase 5's ImportRowError but inlined as
    # JSON rather than a separate table, since the literal spec names this
    # column directly on integration_sync_jobs rather than a child table.
    error_details: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Not in the literal Phase 10 DB spec — added because a webhook-type
    # integration's fetch_records() has nothing to pull on its own (data
    # arrives by push, see app/integrations/hub/webhook_adapter.py); the
    # records pushed in on POST /integrations/{id}/sync must be durably
    # readable by the Celery worker process that actually runs the sync,
    # which is a *separate OS process* from the API server that created the
    # row — an in-memory dict keyed by job id (the first approach tried)
    # does not survive that process boundary. Left in place after
    # processing (not cleared) so retrying a webhook job re-uses the same
    # payload by default unless the retry request supplies a fresh one.
    pushed_records: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # --- Phase 10 upgrade columns (all additive/nullable-or-defaulted —
    # existing rows and the original 11 test_integrations.py tests are
    # unaffected) ---
    direction: Mapped[IntegrationSyncDirection] = mapped_column(
        Enum(IntegrationSyncDirection, native_enum=False, length=10),
        nullable=False,
        default=IntegrationSyncDirection.INBOUND,
        server_default=IntegrationSyncDirection.INBOUND.name,
    )
    records_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    records_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    records_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # Only incremented by a whole-job retry_job() call — distinct from the
    # per-call exponential-backoff retries in
    # app.services.integration_retry_policy, which never touch this field.
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # Set only for jobs created as a *consequence* of something else (a
    # webhook event, a due schedule) — traces the chain for loop-prevention
    # auditing. NULL for ordinary manually-triggered jobs.
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), nullable=True, index=True
    )
    # Coarse category for the UI/health dashboard to group failures by —
    # connection/auth/mapping/validation/apply/rate_limited/
    # webhook_signature/unknown. Not DB-enforced (plain string), mirroring
    # error_details' own philosophy of staying a loose, additive field.
    error_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
