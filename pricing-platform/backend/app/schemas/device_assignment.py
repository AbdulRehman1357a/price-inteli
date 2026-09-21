import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.device_assignment import DeviceAssignmentStatus
from app.schemas.common import PaginationParams


class DeviceAssignmentCreate(BaseModel):
    device_id: uuid.UUID
    store_id: uuid.UUID
    product_id: uuid.UUID


class DeviceAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    device_id: uuid.UUID
    product_id: uuid.UUID
    store_id: uuid.UUID
    assigned_at: datetime
    unassigned_at: datetime | None
    status: DeviceAssignmentStatus


class DeviceAssignmentListParams(PaginationParams):
    device_id: uuid.UUID | None = None
    status: DeviceAssignmentStatus | None = None
