import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.ai.agents.base import Agent
from app.models.ai_agent import AgentType, AIAgent
from app.models.ai_policy import AIPolicy, PolicyMode
from app.models.product import Product, ProductStatus
from app.repositories.product_repository import ProductRepository
from app.services import pricing_recommendation_service


def _candidate_products(db: Session, *, organization_id: uuid.UUID, agent: AIAgent) -> list[Product]:
    config = agent.configuration or {}
    scope = config.get("scope", "all")
    limit = int(config.get("max_products_per_run", 50))
    repo = ProductRepository(db)

    if scope == "products":
        product_ids = [uuid.UUID(pid) for pid in (config.get("product_ids") or [])]
        products = [repo.get_by_id_for_organization(pid, organization_id) for pid in product_ids]
        return [p for p in products if p is not None][:limit]

    category_id = None
    if scope == "category" and config.get("category_id"):
        category_id = uuid.UUID(config["category_id"])
    items, _ = repo.search(organization_id, category_id=category_id, status=ProductStatus.ACTIVE, limit=limit)
    return items


def _should_auto_execute(
    *, policy: AIPolicy, recommendation, current_price: Decimal
) -> tuple[bool, str | None]:
    """The three independent policy signals (see AIPolicy's docstring) plus
    the numeric limits, evaluated against the guardrail-clamped price that's
    already on the recommendation — never the provider's raw candidate.
    Returns (should_auto_execute, reason_if_not).
    """
    if policy.mode != PolicyMode.AUTO_EXECUTE_WITHIN_LIMITS:
        return False, f"Policy mode is {policy.mode.value}, not auto-execute."
    if policy.approval_required:
        return False, "Policy requires approval regardless of mode."
    if not policy.auto_execute:
        return False, "Policy has auto_execute disabled."

    if recommendation.confidence_score < policy.min_confidence:
        return False, (
            f"Confidence {recommendation.confidence_score} is below the policy minimum "
            f"{policy.min_confidence}."
        )

    if current_price > 0:
        change_pct = abs((recommendation.recommended_price - current_price) / current_price * Decimal("100"))
    else:
        change_pct = Decimal("0")
    if change_pct > policy.max_price_change_percent:
        return False, (
            f"Price change {change_pct.quantize(Decimal('0.01'))}% exceeds the policy maximum "
            f"{policy.max_price_change_percent}%."
        )

    impact = (recommendation.input_snapshot or {}).get("expected_impact") or {}
    recommended_margin = impact.get("recommended_margin_percentage")
    if recommended_margin is not None and Decimal(recommended_margin) < policy.min_margin_percent:
        return False, (
            f"Resulting margin {recommended_margin}% is below the policy minimum "
            f"{policy.min_margin_percent}%."
        )

    return True, None


class PricingOptimizationAgent(Agent):
    """Observe (candidate product selection) -> Analyze/Recommend/Validate
    (delegates entirely to pricing_recommendation_service.generate_recommendation,
    which already runs the heuristic provider and DeterministicPricingGuardrail)
    -> Request Approval / Execute if authorized (policy-driven, per
    candidate) -> Record Result (one AIAgentRun.output entry per candidate).
    """

    agent_type = AgentType.PRICING_OPTIMIZATION

    def run(
        self, db: Session, *, organization_id: uuid.UUID, agent: AIAgent, policy: AIPolicy
    ) -> dict[str, Any]:
        config = agent.configuration or {}
        store_id = uuid.UUID(config["store_id"]) if config.get("store_id") else None

        candidates = _candidate_products(db, organization_id=organization_id, agent=agent)
        items: list[dict[str, Any]] = []
        auto_applied = 0
        created_pending = 0
        no_change = 0

        for product in candidates:
            recommendation = pricing_recommendation_service.generate_recommendation(
                db,
                organization_id=organization_id,
                product_id=product.id,
                store_id=store_id,
                provider_name=None,
            )

            if recommendation.recommended_price == recommendation.current_price:
                no_change += 1
                items.append(
                    {
                        "product_id": str(product.id),
                        "product_name": product.product_name,
                        "sku": product.sku,
                        "recommendation_id": str(recommendation.id),
                        "reasoning_summary": recommendation.recommendation_reason,
                        "recommendation": {
                            "current_price": str(recommendation.current_price),
                            "recommended_price": str(recommendation.recommended_price),
                            "confidence_score": str(recommendation.confidence_score),
                        },
                        "guardrail_result": recommendation.input_snapshot.get("guardrail"),
                        "action": "no_change_recommended",
                        "execution_result": None,
                    }
                )
                continue

            should_execute, skip_reason = _should_auto_execute(
                policy=policy, recommendation=recommendation, current_price=recommendation.current_price
            )

            if should_execute:
                recommendation = pricing_recommendation_service.auto_approve_and_apply(
                    db, organization_id=organization_id, recommendation_id=recommendation.id
                )
                auto_applied += 1
                action = "auto_approved_and_applied"
                execution_result = {
                    "applied": True,
                    "selling_price": str(recommendation.recommended_price),
                }
            else:
                created_pending += 1
                action = "created_pending_recommendation"
                execution_result = {"applied": False, "reason": skip_reason}

            items.append(
                {
                    "product_id": str(product.id),
                    "product_name": product.product_name,
                    "sku": product.sku,
                    "recommendation_id": str(recommendation.id),
                    "reasoning_summary": recommendation.recommendation_reason,
                    "recommendation": {
                        "current_price": str(recommendation.current_price),
                        "recommended_price": str(recommendation.recommended_price),
                        "confidence_score": str(recommendation.confidence_score),
                    },
                    "guardrail_result": recommendation.input_snapshot.get("guardrail"),
                    "action": action,
                    "execution_result": execution_result,
                }
            )

        return {
            "candidates_evaluated": len(candidates),
            "recommendations_created": created_pending + auto_applied,
            "auto_applied": auto_applied,
            "no_change": no_change,
            "items": items,
        }
