import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.device_vendor import DeviceVendorStatus


class DeviceVendorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    website: str | None
    status: DeviceVendorStatus
    created_at: datetime
    updated_at: datetime
