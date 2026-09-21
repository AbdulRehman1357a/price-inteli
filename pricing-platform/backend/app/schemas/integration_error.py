import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.integration_error import IntegrationErrorSeverity
from app.schemas.common import PaginationParams


class IntegrationErrorListParams(PaginationParams):
    is_resolved: bool | None = None


class IntegrationErrorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    integration_id: uuid.UUID
    sync_job_id: uuid.UUID | None
    error_type: str
    severity: IntegrationErrorSeverity
    message: str
    context: dict[str, Any] | None
    is_resolved: bool
    resolved_at: datetime | None
    resolved_by: uuid.UUID | None
    created_at: datetime
