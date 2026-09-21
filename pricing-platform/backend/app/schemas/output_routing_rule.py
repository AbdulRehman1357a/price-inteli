import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.output_channel import OutputType
from app.models.output_routing_rule import RoutingRuleStatus
from app.schemas.common import PaginationParams


class OutputRoutingRuleBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    priority: int = Field(default=100, description="Lower runs first.")
    conditions_json: dict[str, Any] | None = None
    target_outputs_json: list[OutputType] = Field(min_length=1)
    status: RoutingRuleStatus = RoutingRuleStatus.ACTIVE

    @field_validator("target_outputs_json")
    @classmethod
    def _dedupe_targets(cls, value: list[OutputType]) -> list[OutputType]:
        seen: list[OutputType] = []
        for item in value:
            if item not in seen:
                seen.append(item)
        return seen


class OutputRoutingRuleCreate(OutputRoutingRuleBase):
    pass


class OutputRoutingRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    priority: int | None = None
    conditions_json: dict[str, Any] | None = None
    target_outputs_json: list[OutputType] | None = Field(default=None, min_length=1)
    status: RoutingRuleStatus | None = None


class OutputRoutingRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    priority: int
    conditions_json: dict[str, Any] | None
    target_outputs_json: list[OutputType]
    status: RoutingRuleStatus
    created_at: datetime
    updated_at: datetime


class OutputRoutingRuleListParams(PaginationParams):
    status: RoutingRuleStatus | None = None
