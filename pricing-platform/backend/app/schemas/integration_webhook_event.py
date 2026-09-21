import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.integration_mapping import CanonicalEntityType
from app.models.integration_webhook_event import IntegrationWebhookEventStatus


class IntegrationWebhookEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    integration_id: uuid.UUID
    provider_event_id: str
    entity_type: CanonicalEntityType | None
    payload: dict[str, Any]
    signature_valid: bool
    status: IntegrationWebhookEventStatus
    sync_job_id: uuid.UUID | None
    received_at: datetime
    processed_at: datetime | None
    error_message: str | None
