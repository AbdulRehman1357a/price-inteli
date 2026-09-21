import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IntegrationLocationUpdate(BaseModel):
    store_id: uuid.UUID | None = None
    is_active: bool | None = None


class IntegrationLocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    integration_id: uuid.UUID
    store_id: uuid.UUID | None
    external_location_id: str
    external_location_name: str
    is_active: bool
    discovered_at: datetime
    linked_at: datetime | None
