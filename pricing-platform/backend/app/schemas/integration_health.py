import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.integration import IntegrationStatus
from app.models.integration_sync_job import IntegrationSyncJobStatus


class IntegrationHealthOut(BaseModel):
    """Aggregated status for the Integration Health tab/dashboard — reads
    from several tables (Integration, IntegrationSyncJob, IntegrationError,
    IntegrationReconciliation) rather than being its own persisted table,
    since every field here is cheaply derivable at read time.
    """

    integration_id: uuid.UUID
    status: IntegrationStatus
    last_successful_connection_at: datetime | None
    last_failed_connection_at: datetime | None
    last_sync_at: datetime | None
    last_job_status: IntegrationSyncJobStatus | None
    last_job_completed_at: datetime | None
    open_error_count: int
    open_reconciliation_count: int
    webhook_configured: bool
