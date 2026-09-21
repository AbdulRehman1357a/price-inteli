import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.ai_agent import AgentStatus, AgentType
from app.models.ai_agent_run import AgentRunStatus, TriggerType
from app.schemas.common import PaginationParams


class AgentConfiguration(BaseModel):
    """What one agent run evaluates, plus a display-only schedule value.

    schedule is stored and shown in the UI but doesn't trigger anything —
    this codebase has no periodic-task scheduler yet (see AIAgent's
    model docstring); every run in this phase is manually triggered via
    POST /ai-agents/{id}/run.
    """

    scope: Literal["all", "category", "products"] = "all"
    category_id: uuid.UUID | None = None
    store_id: uuid.UUID | None = None
    product_ids: list[uuid.UUID] | None = None
    max_products_per_run: int = Field(default=50, ge=1, le=500)
    schedule: Literal["manual", "hourly", "daily", "weekly"] = "manual"


class AgentCreate(BaseModel):
    agent_type: AgentType
    name: str = Field(min_length=1, max_length=255)
    status: AgentStatus = AgentStatus.ACTIVE
    configuration: AgentConfiguration = Field(default_factory=AgentConfiguration)


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    status: AgentStatus | None = None
    configuration: AgentConfiguration | None = None


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    agent_type: AgentType
    name: str
    status: AgentStatus
    configuration: dict
    created_at: datetime
    updated_at: datetime


class AgentListParams(PaginationParams):
    pass


class AgentRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    organization_id: uuid.UUID
    trigger_type: TriggerType
    input_snapshot: dict
    output: dict | None
    status: AgentRunStatus
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None


class AgentRunListParams(PaginationParams):
    pass
