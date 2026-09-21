import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.device_sync_log import DeviceSyncStatus
from app.schemas.common import PaginationParams


class DeviceSyncLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    device_id: uuid.UUID
    product_id: uuid.UUID
    output_job_id: uuid.UUID | None
    status: DeviceSyncStatus
    error_message: str | None
    attempted_at: datetime
    completed_at: datetime | None


class DeviceSyncLogListParams(PaginationParams):
    status: DeviceSyncStatus | None = None
