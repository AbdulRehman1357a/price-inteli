import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.ai_agent import AgentType
from app.models.ai_policy import PolicyMode


class AIPolicyUpdate(BaseModel):
    mode: PolicyMode | None = None
    min_confidence: Decimal | None = Field(default=None, ge=0, le=1, max_digits=5, decimal_places=4)
    max_price_change_percent: Decimal | None = Field(default=None, ge=0, max_digits=6, decimal_places=2)
    min_margin_percent: Decimal | None = Field(default=None, max_digits=6, decimal_places=2)
    approval_required: bool | None = None
    auto_execute: bool | None = None


class AIPolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    agent_type: AgentType
    mode: PolicyMode
    min_confidence: Decimal
    max_price_change_percent: Decimal
    min_margin_percent: Decimal
    approval_required: bool
    auto_execute: bool
    created_at: datetime
    updated_at: datetime
