import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.pricing_rule import RuleStatus, RuleType
from app.schemas.common import PaginationParams


class ActionKind(enum.StrEnum):
    """What the engine actually computes — decoupled from RuleType, which is
    just a categorization label. actions_json must have one of these as its
    "kind", plus the matching value field(s):
      fixed_price:          {"kind": "fixed_price", "value": "19.99"}
      percentage_discount:  {"kind": "percentage_discount", "value": "10"}   (% off base_price)
      fixed_discount:       {"kind": "fixed_discount", "value": "5.00"}      (amount off base_price)
      margin_based:         {"kind": "margin_based", "margin_percentage": "40"}  (% of selling price)
      cost_plus:            {"kind": "cost_plus", "markup_percentage": "50"}     (% of cost price)
    """

    FIXED_PRICE = "fixed_price"
    PERCENTAGE_DISCOUNT = "percentage_discount"
    FIXED_DISCOUNT = "fixed_discount"
    MARGIN_BASED = "margin_based"
    COST_PLUS = "cost_plus"


_ACTION_VALUE_KEYS: dict[ActionKind, str] = {
    ActionKind.FIXED_PRICE: "value",
    ActionKind.PERCENTAGE_DISCOUNT: "value",
    ActionKind.FIXED_DISCOUNT: "value",
    ActionKind.MARGIN_BASED: "margin_percentage",
    ActionKind.COST_PLUS: "markup_percentage",
}


def validate_actions_json(actions: dict[str, Any]) -> dict[str, Any]:
    kind_raw = actions.get("kind")
    if kind_raw not in {k.value for k in ActionKind}:
        raise ValueError(
            f"actions_json.kind must be one of {[k.value for k in ActionKind]}, got {kind_raw!r}."
        )
    kind = ActionKind(kind_raw)
    value_key = _ACTION_VALUE_KEYS[kind]
    if value_key not in actions:
        raise ValueError(f"actions_json for kind '{kind}' requires a '{value_key}' field.")
    try:
        Decimal(str(actions[value_key]))
    except Exception as exc:
        raise ValueError(f"actions_json.{value_key} must be a valid number.") from exc
    return actions


class PricingRuleBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    rule_type: RuleType
    priority: int = Field(default=100, description="Lower runs first.")
    conditions_json: dict[str, Any] | None = None
    actions_json: dict[str, Any]
    constraints_json: dict[str, Any] | None = None
    approval_required: bool = False
    status: RuleStatus = RuleStatus.DRAFT
    effective_from: datetime | None = None
    effective_to: datetime | None = None

    @field_validator("actions_json")
    @classmethod
    def _check_actions(cls, value: dict[str, Any]) -> dict[str, Any]:
        return validate_actions_json(value)


class PricingRuleCreate(PricingRuleBase):
    pass


class PricingRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    rule_type: RuleType | None = None
    priority: int | None = None
    conditions_json: dict[str, Any] | None = None
    actions_json: dict[str, Any] | None = None
    constraints_json: dict[str, Any] | None = None
    approval_required: bool | None = None
    status: RuleStatus | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None

    @field_validator("actions_json")
    @classmethod
    def _check_actions(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        return validate_actions_json(value) if value is not None else None


class PricingRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None
    rule_type: RuleType
    priority: int
    conditions_json: dict[str, Any] | None
    actions_json: dict[str, Any]
    constraints_json: dict[str, Any] | None
    approval_required: bool
    status: RuleStatus
    effective_from: datetime | None
    effective_to: datetime | None
    created_at: datetime
    updated_at: datetime


class PricingRuleListParams(PaginationParams):
    rule_type: RuleType | None = None
    status: RuleStatus | None = None


class RuleTestRequest(BaseModel):
    product_id: uuid.UUID
    store_id: uuid.UUID | None = None


class MatchedRuleTrace(BaseModel):
    rule_id: uuid.UUID
    rule_name: str
    rule_type: RuleType
    priority: int
    price_before: Decimal
    price_after_action: Decimal
    price_after_constraints: Decimal
    constraint_notes: list[str]
    approval_required: bool


class RuleTestResult(BaseModel):
    product_id: uuid.UUID
    store_id: uuid.UUID | None
    current_price: Decimal
    matched_rules: list[MatchedRuleTrace]
    rule_execution_order: list[uuid.UUID]
    calculated_price: Decimal
    constraint_validation: list[str]
    final_price: Decimal
    approval_required: bool
