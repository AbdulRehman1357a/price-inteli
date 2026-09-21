import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.pricing_rule import PricingRule
from app.repositories.pricing_rule_repository import PricingRuleRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.pricing_rule import (
    MatchedRuleTrace,
    PricingRuleCreate,
    PricingRuleListParams,
    PricingRuleUpdate,
    RuleTestRequest,
    RuleTestResult,
)
from app.services import pricing_engine


def create_rule(db: Session, *, organization_id: uuid.UUID, payload: PricingRuleCreate) -> PricingRule:
    rule = PricingRule(id=uuid.uuid4(), organization_id=organization_id, **payload.model_dump())
    return PricingRuleRepository(db).add(rule)


def get_rule(db: Session, *, organization_id: uuid.UUID, rule_id: uuid.UUID) -> PricingRule:
    rule = PricingRuleRepository(db).get_by_id_for_organization(rule_id, organization_id)
    if rule is None:
        raise NotFoundError("Pricing rule not found.", code="pricing_rule_not_found")
    return rule


def list_rules(
    db: Session, *, organization_id: uuid.UUID, params: PricingRuleListParams
) -> tuple[list[PricingRule], int]:
    offset = (params.page - 1) * params.page_size
    return PricingRuleRepository(db).search(
        organization_id,
        rule_type=params.rule_type,
        status=params.status,
        offset=offset,
        limit=params.page_size,
    )


def update_rule(
    db: Session, *, organization_id: uuid.UUID, rule_id: uuid.UUID, payload: PricingRuleUpdate
) -> PricingRule:
    rule = get_rule(db, organization_id=organization_id, rule_id=rule_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    return PricingRuleRepository(db).add(rule)


def test_rule(
    db: Session, *, organization_id: uuid.UUID, rule_id: uuid.UUID, payload: RuleTestRequest
) -> RuleTestResult:
    """Evaluates this rule (even if DRAFT / outside its effective window)
    together with every other currently in-force rule, against one product
    — the "Current Price / Matched Rules / Rule Execution Order /
    Calculated Price / Constraint Validation / Final Price" preview.
    """
    get_rule(db, organization_id=organization_id, rule_id=rule_id)  # tenant check + existence

    product = ProductRepository(db).get_by_id_for_organization(payload.product_id, organization_id)
    if product is None:
        raise NotFoundError("Product not found.", code="product_not_found")
    if payload.store_id is not None:
        if StoreRepository(db).get_by_id_for_organization(payload.store_id, organization_id) is None:
            raise NotFoundError("Store not found.", code="store_not_found")

    result = pricing_engine.evaluate_for_product(
        db,
        organization_id=organization_id,
        product=product,
        store_id=payload.store_id,
        include_rule_id=rule_id,
    )

    return RuleTestResult(
        product_id=product.id,
        store_id=payload.store_id,
        current_price=result.current_price,
        matched_rules=[
            MatchedRuleTrace(
                rule_id=trace.rule.id,
                rule_name=trace.rule.name,
                rule_type=trace.rule.rule_type,
                priority=trace.rule.priority,
                price_before=trace.price_before,
                price_after_action=trace.price_after_action,
                price_after_constraints=trace.price_after_constraints,
                constraint_notes=trace.constraint_notes,
                approval_required=trace.rule.approval_required,
            )
            for trace in result.matched
        ],
        rule_execution_order=[trace.rule.id for trace in result.matched],
        calculated_price=result.calculated_price,
        constraint_validation=result.constraint_notes,
        final_price=result.final_price,
        approval_required=result.approval_required,
    )
