import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.mixins import utcnow
from app.models.pricing_rule import PricingRule
from app.models.product import Product
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.price_repository import PriceRepository
from app.repositories.pricing_rule_repository import PricingRuleRepository

# Every intermediate calculation is quantized to this precision: "all
# financial calculations must use Decimal, not float" per the Phase 6 spec.
_MONEY = Decimal("0.0001")


class PricingEngineError(Exception):
    """A rule can't be applied as configured (e.g. margin_based on a
    product with no cost_price). The engine skips that rule and notes why,
    rather than failing the whole evaluation.
    """


@dataclass
class RuleTrace:
    rule: PricingRule
    price_before: Decimal
    price_after_action: Decimal
    price_after_constraints: Decimal
    constraint_notes: list[str] = field(default_factory=list)


@dataclass
class EvaluationResult:
    current_price: Decimal
    matched: list[RuleTrace]
    calculated_price: Decimal
    final_price: Decimal
    constraint_notes: list[str]
    approval_required: bool


def apply_action(
    action: dict[str, Any], *, current_price: Decimal, cost_price: Decimal | None
) -> Decimal:
    """Relative actions (percentage/fixed discount) operate on current_price
    so multiple matched rules stack in priority order. Absolute actions
    (fixed_price, margin_based, cost_plus) set a new price outright,
    intentionally overriding whatever came before — a margin target isn't
    "10% off the previous rule's result", it's "this must be the margin".
    """
    kind = action.get("kind")
    if kind == "fixed_price":
        return Decimal(str(action["value"])).quantize(_MONEY)
    if kind == "percentage_discount":
        pct = Decimal(str(action["value"]))
        return (current_price * (Decimal("100") - pct) / Decimal("100")).quantize(_MONEY)
    if kind == "fixed_discount":
        return (current_price - Decimal(str(action["value"]))).quantize(_MONEY)
    if kind == "margin_based":
        if not cost_price or cost_price <= 0:
            raise PricingEngineError("margin_based requires the product to have a cost_price.")
        margin = Decimal(str(action["margin_percentage"]))
        if margin >= 100:
            raise PricingEngineError("margin_percentage must be less than 100.")
        return (cost_price / (Decimal("1") - margin / Decimal("100"))).quantize(_MONEY)
    if kind == "cost_plus":
        if cost_price is None:
            raise PricingEngineError("cost_plus requires the product to have a cost_price.")
        markup = Decimal(str(action["markup_percentage"]))
        return (cost_price * (Decimal("1") + markup / Decimal("100"))).quantize(_MONEY)
    raise PricingEngineError(f"Unknown action kind: {kind!r}")


def apply_rounding(price: Decimal, rounding: str) -> Decimal:
    """rounding is either a decimal increment ("0.05" -> nearest nickel,
    "1.00" -> nearest dollar) or the literal "charm_99" (round down to the
    nearest X.99, e.g. 19.45 -> 18.99, 20.00 -> 19.99 — charm pricing never
    rounds up).
    """
    if not rounding or rounding == "none":
        return price
    if rounding == "charm_99":
        floor = price.to_integral_value(rounding=ROUND_FLOOR)
        result = floor - Decimal("0.01")
        return result if result > 0 else Decimal("0.99")
    try:
        increment = Decimal(str(rounding))
    except InvalidOperation:
        return price
    if increment <= 0:
        return price
    return (price / increment).to_integral_value(rounding=ROUND_HALF_UP) * increment


def apply_constraints(
    price: Decimal, *, base_price: Decimal, cost_price: Decimal | None, constraints: dict[str, Any] | None
) -> tuple[Decimal, list[str]]:
    """The 5 constraint types from the Phase 6 spec: Minimum Price, Maximum
    Price, Minimum Margin, Maximum Discount, Price Rounding. Applied in
    that order; each one that actually changes the price is noted so the
    test/preview endpoint can show exactly what was clamped and why.
    """
    if not constraints:
        return price.quantize(_MONEY), []

    notes: list[str] = []
    result = price

    if "min_price" in constraints:
        min_price = Decimal(str(constraints["min_price"]))
        if result < min_price:
            notes.append(f"Below minimum price {min_price}; raised from {result}.")
            result = min_price

    if "max_price" in constraints:
        max_price = Decimal(str(constraints["max_price"]))
        if result > max_price:
            notes.append(f"Above maximum price {max_price}; lowered from {result}.")
            result = max_price

    if "min_margin_percentage" in constraints and cost_price and cost_price > 0:
        min_margin = Decimal(str(constraints["min_margin_percentage"]))
        if min_margin < 100:
            min_allowed = (cost_price / (Decimal("1") - min_margin / Decimal("100"))).quantize(_MONEY)
            if result < min_allowed:
                notes.append(f"Margin below {min_margin}%; raised from {result} to {min_allowed}.")
                result = min_allowed

    if "max_discount_percentage" in constraints:
        max_discount = Decimal(str(constraints["max_discount_percentage"]))
        floor_price = (base_price * (Decimal("100") - max_discount) / Decimal("100")).quantize(_MONEY)
        if result < floor_price:
            notes.append(
                f"Discount exceeds {max_discount}% off base price; raised from {result} to {floor_price}."
            )
            result = floor_price

    if "rounding" in constraints:
        rounded = apply_rounding(result, str(constraints["rounding"]))
        if rounded != result:
            notes.append(f"Rounded {result} to {rounded}.")
        result = rounded

    return result.quantize(_MONEY), notes


def _resolve_quantity(
    db: Session, *, organization_id: uuid.UUID, product_id: uuid.UUID, store_id: uuid.UUID | None
) -> Decimal:
    if store_id is not None:
        inv = InventoryRepository(db).get_by_store_and_product(organization_id, store_id, product_id)
        return inv.quantity_available if inv else Decimal("0")
    stmt = select(func.coalesce(func.sum(Inventory.quantity_available), 0)).where(
        Inventory.organization_id == organization_id, Inventory.product_id == product_id
    )
    return Decimal(str(db.execute(stmt).scalar_one()))


def _conditions_match(
    db: Session,
    rule: PricingRule,
    *,
    organization_id: uuid.UUID,
    product: Product,
    store_id: uuid.UUID | None,
) -> bool:
    conditions = rule.conditions_json or {}

    product_ids = conditions.get("product_ids")
    if product_ids and str(product.id) not in {str(p) for p in product_ids}:
        return False

    category_ids = conditions.get("category_ids")
    if category_ids and str(product.category_id) not in {str(c) for c in category_ids}:
        return False

    store_ids = conditions.get("store_ids")
    if store_ids and (store_id is None or str(store_id) not in {str(s) for s in store_ids}):
        return False

    min_quantity = conditions.get("min_quantity")
    max_quantity = conditions.get("max_quantity")
    if min_quantity is not None or max_quantity is not None:
        quantity = _resolve_quantity(
            db, organization_id=organization_id, product_id=product.id, store_id=store_id
        )
        if min_quantity is not None and quantity < Decimal(str(min_quantity)):
            return False
        if max_quantity is not None and quantity > Decimal(str(max_quantity)):
            return False

    return True


def evaluate_for_product(
    db: Session,
    *,
    organization_id: uuid.UUID,
    product: Product,
    store_id: uuid.UUID | None,
    now: datetime | None = None,
    include_rule_id: uuid.UUID | None = None,
) -> EvaluationResult:
    """Runs every in-force rule (plus include_rule_id's rule even if it's
    DRAFT/out of window, for previewing a not-yet-active rule) against one
    product, in priority order, each rule's output feeding the next.
    """
    now = now or utcnow()
    current = PriceRepository(db).get_current_effective(
        organization_id, product_id=product.id, store_id=store_id, now=now
    )
    current_price = (current.selling_price if current else product.selling_price).quantize(_MONEY)
    base_price = (product.base_price or product.selling_price).quantize(_MONEY)
    cost_price = product.cost_price

    rules = PricingRuleRepository(db).list_in_force(organization_id, now=now, include_rule_id=include_rule_id)

    running_price = current_price
    traces: list[RuleTrace] = []
    all_notes: list[str] = []
    approval_required = False

    for rule in rules:
        matches = _conditions_match(
            db, rule, organization_id=organization_id, product=product, store_id=store_id
        )
        if not matches:
            continue

        price_before = running_price
        try:
            after_action = apply_action(rule.actions_json, current_price=running_price, cost_price=cost_price)
        except PricingEngineError as exc:
            all_notes.append(f"Rule '{rule.name}' skipped: {exc}")
            continue

        after_constraints, notes = apply_constraints(
            after_action, base_price=base_price, cost_price=cost_price, constraints=rule.constraints_json
        )
        traces.append(
            RuleTrace(
                rule=rule,
                price_before=price_before,
                price_after_action=after_action,
                price_after_constraints=after_constraints,
                constraint_notes=notes,
            )
        )
        all_notes.extend(f"[{rule.name}] {note}" for note in notes)
        running_price = after_constraints
        if rule.approval_required:
            approval_required = True

    calculated_price = traces[-1].price_after_action if traces else current_price
    final_price = running_price

    return EvaluationResult(
        current_price=current_price,
        matched=traces,
        calculated_price=calculated_price,
        final_price=final_price,
        constraint_notes=all_notes,
        approval_required=approval_required,
    )
