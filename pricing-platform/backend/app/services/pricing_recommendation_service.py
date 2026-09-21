import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.ai.guardrails import DeterministicPricingGuardrail
from app.ai.providers.base import PricingRecommendationInput
from app.ai.providers.registry import get_ai_provider
from app.core.exceptions import ConflictError, NotFoundError
from app.models.ai_pricing_recommendation import AIPricingRecommendation, RecommendationStatus
from app.models.mixins import utcnow
from app.models.pricing_rule import PricingRule
from app.models.product import Product
from app.repositories.ai_pricing_recommendation_repository import AIPricingRecommendationRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.ai_pricing_recommendation import AIPricingRecommendationListParams
from app.schemas.price import PriceCreate
from app.services import price_service, pricing_engine, sales_velocity

_MONEY = Decimal("0.0001")
_LOOKBACK_DAYS = 30
_IMPACT_HORIZON_DAYS = 30
_EXPIRE_AFTER_DAYS = 14


def _as_aware(value: datetime) -> datetime:
    """SQLite (tests) drops tzinfo on round-trip even for DateTime(timezone=True)
    columns; MySQL always returns values already normalized to UTC. Either
    way a naive value from the DB means UTC — mirrors price_service._as_aware.
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _aggregate_constraints(rules: list[PricingRule]) -> dict[str, Any]:
    """Combines every matched rule's constraints into the single most
    restrictive set — the same "Rule constraints" input the deterministic
    guardrail validates a recommendation against.
    """
    combined: dict[str, Any] = {}
    for rule in rules:
        c = rule.constraints_json or {}
        if "min_price" in c:
            new_min = Decimal(str(c["min_price"]))
            combined["min_price"] = max(new_min, combined.get("min_price", new_min))
        if "max_price" in c:
            new_max = Decimal(str(c["max_price"]))
            combined["max_price"] = min(new_max, combined.get("max_price", new_max))
        if "min_margin_percentage" in c:
            combined["min_margin_percentage"] = max(
                Decimal(str(c["min_margin_percentage"])),
                combined.get("min_margin_percentage", Decimal(str(c["min_margin_percentage"]))),
            )
        if "max_discount_percentage" in c:
            combined["max_discount_percentage"] = min(
                Decimal(str(c["max_discount_percentage"])),
                combined.get("max_discount_percentage", Decimal(str(c["max_discount_percentage"]))),
            )
        if "rounding" in c and "rounding" not in combined:
            combined["rounding"] = c["rounding"]
    return {k: str(v) for k, v in combined.items()}


def _margin_percentage(price: Decimal, cost_price: Decimal | None) -> Decimal | None:
    if cost_price is None or price <= 0:
        return None
    return ((price - cost_price) / price * Decimal("100")).quantize(Decimal("0.01"))


def _gather_input(
    db: Session, *, organization_id: uuid.UUID, product: Product, store_id: uuid.UUID | None
) -> tuple[PricingRecommendationInput, dict[str, Any]]:
    category = CategoryRepository(db).get_by_id_for_organization(product.category_id, organization_id)
    store = StoreRepository(db).get_by_id_for_organization(store_id, organization_id) if store_id else None

    velocity = sales_velocity.resolve(
        db,
        organization_id=organization_id,
        product_id=product.id,
        store_id=store_id,
        lookback_days=_LOOKBACK_DAYS,
    )
    quantity_on_hand = velocity.quantity_on_hand
    quantity_available = velocity.quantity_available
    reorder_point = velocity.reorder_point
    units_sold = velocity.units_sold_lookback
    sales_velocity_per_day = velocity.sales_velocity_per_day

    now = utcnow()
    evaluation = pricing_engine.evaluate_for_product(
        db, organization_id=organization_id, product=product, store_id=store_id, now=now
    )
    current_price = evaluation.current_price
    matched_rules = [trace.rule for trace in evaluation.matched]

    data = PricingRecommendationInput(
        product_id=str(product.id),
        product_name=product.product_name,
        sku=product.sku,
        category_name=category.name if category else "Unknown",
        store_id=str(store_id) if store_id else None,
        store_name=store.name if store else None,
        cost_price=product.cost_price,
        current_price=current_price,
        current_margin_percentage=_margin_percentage(current_price, product.cost_price),
        quantity_on_hand=quantity_on_hand,
        quantity_available=quantity_available,
        reorder_point=reorder_point,
        sales_velocity_per_day=sales_velocity_per_day,
        units_sold_lookback=units_sold,
        lookback_days=_LOOKBACK_DAYS,
        applicable_rule_names=[rule.name for rule in matched_rules],
    )

    snapshot: dict[str, Any] = {
        "cost_price": str(product.cost_price) if product.cost_price is not None else None,
        "current_price": str(current_price),
        "current_margin_percentage": str(data.current_margin_percentage)
        if data.current_margin_percentage is not None
        else None,
        "category": {"id": str(category.id), "name": category.name} if category else None,
        "store": {"id": str(store.id), "name": store.name} if store else None,
        "inventory": {
            "quantity_on_hand": str(quantity_on_hand),
            "quantity_available": str(quantity_available),
            "reorder_point": str(reorder_point) if reorder_point is not None else None,
        },
        "sales_history": {
            "lookback_days": _LOOKBACK_DAYS,
            "units_sold": str(units_sold),
            "sales_velocity_per_day": str(sales_velocity_per_day),
        },
        "existing_pricing_rules": [
            {"id": str(rule.id), "name": rule.name, "rule_type": rule.rule_type.value}
            for rule in matched_rules
        ],
        "rule_constraints": _aggregate_constraints(matched_rules),
    }

    return data, snapshot


def generate_recommendation(
    db: Session,
    *,
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    store_id: uuid.UUID | None,
    provider_name: str | None,
) -> AIPricingRecommendation:
    product = ProductRepository(db).get_by_id_for_organization(product_id, organization_id)
    if product is None:
        raise NotFoundError("Product not found.", code="product_not_found")
    if store_id is not None:
        store = StoreRepository(db).get_by_id_for_organization(store_id, organization_id)
        if store is None:
            raise NotFoundError("Store not found.", code="store_not_found")

    data, snapshot = _gather_input(db, organization_id=organization_id, product=product, store_id=store_id)

    provider = get_ai_provider(provider_name)
    raw = provider.recommend(data)

    guardrail = DeterministicPricingGuardrail()
    result = guardrail.evaluate(
        proposed_price=raw.recommended_price,
        current_price=data.current_price,
        cost_price=data.cost_price,
        constraints=snapshot["rule_constraints"],
    )

    projected_units = (
        data.sales_velocity_per_day * _IMPACT_HORIZON_DAYS
        if data.sales_velocity_per_day > 0
        else Decimal("0")
    )
    price_delta = result.adjusted_price - data.current_price
    expected_revenue_impact = (price_delta * projected_units).quantize(_MONEY)
    expected_margin_impact = (
        (price_delta * projected_units).quantize(_MONEY) if data.cost_price is not None else None
    )
    recommended_margin = _margin_percentage(result.adjusted_price, data.cost_price)

    snapshot["provider_raw_output"] = raw.raw_output
    snapshot["provider_raw_recommended_price"] = str(raw.recommended_price)
    snapshot["guardrail"] = {
        "passed": result.passed,
        "proposed_price": str(result.proposed_price),
        "adjusted_price": str(result.adjusted_price),
        "notes": result.notes,
    }
    snapshot["expected_impact"] = {
        "horizon_days": _IMPACT_HORIZON_DAYS,
        "projected_units": str(projected_units),
        "revenue_impact": str(expected_revenue_impact),
        "margin_impact": str(expected_margin_impact) if expected_margin_impact is not None else None,
        "current_margin_percentage": str(data.current_margin_percentage)
        if data.current_margin_percentage is not None
        else None,
        "recommended_margin_percentage": str(recommended_margin) if recommended_margin is not None else None,
    }

    reason = raw.reason
    if result.notes:
        reason = f"{reason} [Guardrail adjustments: {'; '.join(result.notes)}]"

    recommendation = AIPricingRecommendation(
        id=uuid.uuid4(),
        organization_id=organization_id,
        store_id=store_id,
        product_id=product.id,
        current_price=data.current_price,
        recommended_price=result.adjusted_price,
        confidence_score=raw.confidence_score,
        recommendation_reason=reason,
        input_snapshot=snapshot,
        status=RecommendationStatus.PENDING,
        created_by_agent=provider.name,
    )
    return AIPricingRecommendationRepository(db).add(recommendation)


def get_recommendation(
    db: Session, *, organization_id: uuid.UUID, recommendation_id: uuid.UUID
) -> AIPricingRecommendation:
    recommendation = AIPricingRecommendationRepository(db).get_by_id_for_organization(
        recommendation_id, organization_id
    )
    if recommendation is None:
        raise NotFoundError("Recommendation not found.", code="recommendation_not_found")
    return recommendation


def list_recommendations(
    db: Session, *, organization_id: uuid.UUID, params: AIPricingRecommendationListParams
) -> tuple[list[AIPricingRecommendation], int]:
    offset = (params.page - 1) * params.page_size
    return AIPricingRecommendationRepository(db).search(
        organization_id,
        status=params.status,
        product_id=params.product_id,
        store_id=params.store_id,
        offset=offset,
        limit=params.page_size,
    )


def _require_pending(recommendation: AIPricingRecommendation) -> None:
    if recommendation.status != RecommendationStatus.PENDING:
        raise ConflictError(
            f"Only pending recommendations can be reviewed (current status: {recommendation.status.value}).",
            code="recommendation_not_pending",
        )


def approve_recommendation(
    db: Session, *, organization_id: uuid.UUID, recommendation_id: uuid.UUID, reviewer_id: uuid.UUID
) -> AIPricingRecommendation:
    recommendation = get_recommendation(
        db, organization_id=organization_id, recommendation_id=recommendation_id
    )
    _require_pending(recommendation)
    recommendation.status = RecommendationStatus.APPROVED
    recommendation.reviewed_by = reviewer_id
    recommendation.reviewed_at = utcnow()
    return AIPricingRecommendationRepository(db).add(recommendation)


def reject_recommendation(
    db: Session, *, organization_id: uuid.UUID, recommendation_id: uuid.UUID, reviewer_id: uuid.UUID
) -> AIPricingRecommendation:
    recommendation = get_recommendation(
        db, organization_id=organization_id, recommendation_id=recommendation_id
    )
    _require_pending(recommendation)
    recommendation.status = RecommendationStatus.REJECTED
    recommendation.reviewed_by = reviewer_id
    recommendation.reviewed_at = utcnow()
    return AIPricingRecommendationRepository(db).add(recommendation)


def modify_recommendation(
    db: Session,
    *,
    organization_id: uuid.UUID,
    recommendation_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    new_price: Decimal,
) -> AIPricingRecommendation:
    """A reviewer's override still has to clear the same deterministic
    guardrails — modifying a recommendation isn't a way around them.
    Stays PENDING: approving is still a separate, explicit step.
    """
    recommendation = get_recommendation(
        db, organization_id=organization_id, recommendation_id=recommendation_id
    )
    _require_pending(recommendation)

    constraints = recommendation.input_snapshot.get("rule_constraints", {})
    cost_price = recommendation.input_snapshot.get("cost_price")
    guardrail = DeterministicPricingGuardrail()
    result = guardrail.evaluate(
        proposed_price=new_price,
        current_price=recommendation.current_price,
        cost_price=Decimal(cost_price) if cost_price is not None else None,
        constraints=constraints,
    )

    snapshot = dict(recommendation.input_snapshot)
    snapshot["manual_modification"] = {
        "modified_by": str(reviewer_id),
        "proposed_price": str(result.proposed_price),
        "adjusted_price": str(result.adjusted_price),
        "notes": result.notes,
    }
    recommendation.input_snapshot = snapshot
    recommendation.recommended_price = result.adjusted_price
    if result.notes:
        note_suffix = f" [Manually modified; guardrail adjustments: {'; '.join(result.notes)}]"
    else:
        note_suffix = " [Manually modified]"
    recommendation.recommendation_reason = f"{recommendation.recommendation_reason}{note_suffix}"
    return AIPricingRecommendationRepository(db).add(recommendation)


def _apply(
    db: Session,
    *,
    organization_id: uuid.UUID,
    recommendation: AIPricingRecommendation,
    actor_id: uuid.UUID | None,
) -> AIPricingRecommendation:
    """Writes the real Price row. actor_id is None for an agent's
    auto-execute path (price_service.create_price already supports a
    system-triggered, user-less creation) — see apply_recommendation and
    app.services.agent_service for the two callers.
    """
    product = ProductRepository(db).get_by_id_for_organization(recommendation.product_id, organization_id)
    if product is None:
        raise NotFoundError("Product not found.", code="product_not_found")

    price_service.create_price(
        db,
        organization_id=organization_id,
        user_id=actor_id,
        payload=PriceCreate(
            store_id=recommendation.store_id,
            product_id=recommendation.product_id,
            base_price=product.base_price or product.selling_price,
            selling_price=recommendation.recommended_price,
            currency=product.currency or "USD",
            source=f"ai_recommendation:{recommendation.id}",
            reason=recommendation.recommendation_reason,
        ),
    )

    recommendation.status = RecommendationStatus.APPLIED
    return AIPricingRecommendationRepository(db).add(recommendation)


def apply_recommendation(
    db: Session, *, organization_id: uuid.UUID, recommendation_id: uuid.UUID, actor_id: uuid.UUID
) -> AIPricingRecommendation:
    """The only human-facing function that ever writes a real Price row —
    and only once a human has already approved the recommendation. Goes
    through price_service.create_price(), the same deterministic path a
    manually-entered price uses; AI never writes pricing data itself.
    """
    recommendation = get_recommendation(
        db, organization_id=organization_id, recommendation_id=recommendation_id
    )
    if recommendation.status != RecommendationStatus.APPROVED:
        raise ConflictError(
            f"Only approved recommendations can be applied (current status: {recommendation.status.value}).",
            code="recommendation_not_approved",
        )
    return _apply(db, organization_id=organization_id, recommendation=recommendation, actor_id=actor_id)


def auto_approve_and_apply(
    db: Session, *, organization_id: uuid.UUID, recommendation_id: uuid.UUID
) -> AIPricingRecommendation:
    """The agent auto-execute path (app.services.agent_service) — only
    reached when an AIPolicy in AUTO_EXECUTE_WITHIN_LIMITS mode, with
    approval_required=False and auto_execute=True, decides a specific
    recommendation's confidence/price-change/margin are within the
    org-configured limits. reviewed_by stays NULL (no human reviewer) —
    created_by_agent on the row already records which agent decided this.
    Still goes through the exact same _apply() as a human-triggered apply;
    the guardrail was already enforced when the recommendation was
    generated (see pricing_recommendation_service.generate_recommendation)
    and is never re-checked or bypassed here.
    """
    recommendation = get_recommendation(
        db, organization_id=organization_id, recommendation_id=recommendation_id
    )
    _require_pending(recommendation)
    recommendation.status = RecommendationStatus.APPROVED
    recommendation.reviewed_at = utcnow()
    AIPricingRecommendationRepository(db).add(recommendation)
    return _apply(db, organization_id=organization_id, recommendation=recommendation, actor_id=None)


def get_dashboard_summary(db: Session, *, organization_id: uuid.UUID) -> dict[str, Any]:
    repo = AIPricingRecommendationRepository(db)
    counts = repo.status_counts(organization_id)

    potential_revenue_impact = Decimal("0")
    potential_margin_impact = Decimal("0")
    for recommendation in repo.list_pending(organization_id):
        impact = (recommendation.input_snapshot or {}).get("expected_impact") or {}
        if impact.get("revenue_impact") is not None:
            potential_revenue_impact += Decimal(impact["revenue_impact"])
        if impact.get("margin_impact") is not None:
            potential_margin_impact += Decimal(impact["margin_impact"])

    return {
        "pending_count": counts.get(RecommendationStatus.PENDING.value, 0),
        "approved_count": counts.get(RecommendationStatus.APPROVED.value, 0),
        "rejected_count": counts.get(RecommendationStatus.REJECTED.value, 0),
        "applied_count": counts.get(RecommendationStatus.APPLIED.value, 0),
        "expired_count": counts.get(RecommendationStatus.EXPIRED.value, 0),
        "potential_revenue_impact": potential_revenue_impact.quantize(_MONEY),
        "potential_margin_impact": potential_margin_impact.quantize(_MONEY),
    }


def expire_stale_recommendations(db: Session, *, organization_id: uuid.UUID) -> int:
    """Marks PENDING recommendations older than _EXPIRE_AFTER_DAYS as
    EXPIRED — the data they were based on (inventory, sales velocity) is
    stale by then. No scheduler wires this up automatically (this codebase
    has no Celery-beat/periodic-task infra anywhere yet); it's a plain
    function a future scheduled task or management command can call.
    """
    cutoff = utcnow() - timedelta(days=_EXPIRE_AFTER_DAYS)
    repo = AIPricingRecommendationRepository(db)
    expired = 0
    for recommendation in repo.list_pending(organization_id):
        if _as_aware(recommendation.created_at) < cutoff:
            recommendation.status = RecommendationStatus.EXPIRED
            repo.add(recommendation)
            expired += 1
    return expired
