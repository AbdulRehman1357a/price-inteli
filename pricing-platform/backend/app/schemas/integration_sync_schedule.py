import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.integration_mapping import CanonicalEntityType
from app.models.integration_sync_job import IntegrationSyncJobType


class IntegrationSyncScheduleCreate(BaseModel):
    entity_type: CanonicalEntityType
    job_type: IntegrationSyncJobType = IntegrationSyncJobType.INCREMENTAL_SYNC
    interval_minutes: int = Field(ge=1, le=10080)  # 1 minute .. 7 days


class IntegrationSyncScheduleUpdate(BaseModel):
    interval_minutes: int | None = Field(default=None, ge=1, le=10080)
    is_enabled: bool | None = None


class IntegrationSyncScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    integration_id: uuid.UUID
    entity_type: CanonicalEntityType
    job_type: IntegrationSyncJobType
    interval_minutes: int
    is_enabled: bool
    next_run_at: datetime
    last_dispatched_job_id: uuid.UUID | None
    created_at: datetime
