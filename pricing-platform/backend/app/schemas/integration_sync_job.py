import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.integration_mapping import CanonicalEntityType
from app.models.integration_sync_job import (
    IntegrationSyncDirection,
    IntegrationSyncJobStatus,
    IntegrationSyncJobType,
)
from app.schemas.common import PaginationParams


class IntegrationSyncRequest(BaseModel):
    entity_type: CanonicalEntityType
    job_type: IntegrationSyncJobType = IntegrationSyncJobType.FULL_SYNC
    # Only meaningful for provider="webhook" integrations — CSV/REST
    # adapters pull their own data in fetch_records() and ignore this.
    records: list[dict[str, Any]] | None = None


class IntegrationSyncJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    integration_id: uuid.UUID
    job_type: IntegrationSyncJobType
    entity_type: CanonicalEntityType
    status: IntegrationSyncJobStatus
    records_processed: int
    records_failed: int
    started_at: datetime
    completed_at: datetime | None
    error_details: list[dict[str, Any]] | None
    # --- Phase 10 upgrade ---
    direction: IntegrationSyncDirection
    records_created: int
    records_updated: int
    records_skipped: int
    retry_count: int
    correlation_id: uuid.UUID | None
    error_type: str | None


class IntegrationSyncJobListParams(PaginationParams):
    status: IntegrationSyncJobStatus | None = None
