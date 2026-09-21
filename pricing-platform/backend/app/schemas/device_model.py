import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.device_model import DeviceModelStatus


class DeviceModelOut(BaseModel):
    # protected_namespaces=() — model_code is a legitimate field name from
    # the literal Phase 8 spec, not a Pydantic model-namespace clash.
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: uuid.UUID
    vendor_id: uuid.UUID
    name: str
    model_code: str
    screen_size: str | None
    resolution: str | None
    color_capabilities: dict[str, Any] | None
    battery_type: str | None
    communication_type: str | None
    status: DeviceModelStatus
    created_at: datetime
    updated_at: datetime
