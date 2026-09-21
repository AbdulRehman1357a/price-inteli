import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.output_job import OutputJobStatus
from app.schemas.common import PaginationParams


class OutputJobCreate(BaseModel):
    output_channel_id: uuid.UUID
    product_id: uuid.UUID
    store_id: uuid.UUID | None = None


class OutputJobBulkCreate(BaseModel):
    output_channel_id: uuid.UUID
    product_ids: list[uuid.UUID]
    store_id: uuid.UUID | None = None


class OutputJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    output_channel_id: uuid.UUID
    product_id: uuid.UUID
    store_id: uuid.UUID | None
    payload: dict[str, Any] | None
    status: OutputJobStatus
    attempts: int
    last_error: str | None
    idempotency_key: str | None
    routing_rule_id: uuid.UUID | None
    source_price_id: uuid.UUID | None
    created_at: datetime
    completed_at: datetime | None


class OutputJobListParams(PaginationParams):
    output_channel_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    store_id: uuid.UUID | None = None
    status: OutputJobStatus | None = None


class OutputJobDashboardSummary(BaseModel):
    """Counts for the Phase 14 execution dashboard. total is the sum of all
    statuses (including cancelled), not just the four called out by name.
    """

    total: int
    pending: int
    processing: int
    successful: int
    failed: int
    cancelled: int
