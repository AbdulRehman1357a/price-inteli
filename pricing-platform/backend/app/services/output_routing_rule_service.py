import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.output_routing_rule import OutputRoutingRule
from app.repositories.output_routing_rule_repository import OutputRoutingRuleRepository
from app.schemas.output_routing_rule import (
    OutputRoutingRuleCreate,
    OutputRoutingRuleListParams,
    OutputRoutingRuleUpdate,
)


def create_rule(
    db: Session, *, organization_id: uuid.UUID, payload: OutputRoutingRuleCreate
) -> OutputRoutingRule:
    rule = OutputRoutingRule(
        id=uuid.uuid4(),
        organization_id=organization_id,
        name=payload.name,
        priority=payload.priority,
        conditions_json=payload.conditions_json,
        target_outputs_json=[t.value for t in payload.target_outputs_json],
        status=payload.status,
    )
    return OutputRoutingRuleRepository(db).add(rule)


def get_rule(db: Session, *, organization_id: uuid.UUID, rule_id: uuid.UUID) -> OutputRoutingRule:
    rule = OutputRoutingRuleRepository(db).get_by_id_for_organization(rule_id, organization_id)
    if rule is None:
        raise NotFoundError("Output routing rule not found.", code="output_routing_rule_not_found")
    return rule


def list_rules(
    db: Session, *, organization_id: uuid.UUID, params: OutputRoutingRuleListParams
) -> tuple[list[OutputRoutingRule], int]:
    offset = (params.page - 1) * params.page_size
    return OutputRoutingRuleRepository(db).search(
        organization_id, status=params.status, offset=offset, limit=params.page_size
    )


def update_rule(
    db: Session, *, organization_id: uuid.UUID, rule_id: uuid.UUID, payload: OutputRoutingRuleUpdate
) -> OutputRoutingRule:
    rule = get_rule(db, organization_id=organization_id, rule_id=rule_id)
    data = payload.model_dump(exclude_unset=True)

    if "name" in data:
        rule.name = data["name"]
    if "priority" in data:
        rule.priority = data["priority"]
    if "conditions_json" in data:
        rule.conditions_json = data["conditions_json"]
    if "target_outputs_json" in data:
        rule.target_outputs_json = [
            t.value if hasattr(t, "value") else t for t in data["target_outputs_json"]
        ]
    if "status" in data:
        rule.status = data["status"]

    return OutputRoutingRuleRepository(db).add(rule)
