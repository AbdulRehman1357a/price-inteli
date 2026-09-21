from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.ai.base import PricingGuardrail
from app.services.pricing_engine import apply_constraints

_MONEY = Decimal("0.0001")


@dataclass
class GuardrailResult:
    """What the frontend's "Guardrail results" detail-view section shows.
    passed=False means the proposed price needed to be clamped —
    adjusted_price is always what actually gets stored/applied, never the
    provider's raw, unvalidated number.
    """

    passed: bool
    proposed_price: Decimal
    adjusted_price: Decimal
    notes: list[str] = field(default_factory=list)


class DeterministicPricingGuardrail(PricingGuardrail):
    """Rule: AI must not bypass deterministic pricing guardrails. Reuses the
    exact same constraint math the Pricing Engine applies to rule-driven
    price changes (app.services.pricing_engine.apply_constraints) — margin,
    min/max price, max discount, rounding — plus one AI-specific floor: a
    recommendation is never allowed to clear guardrails at or below cost,
    even if no explicit pricing-rule constraint would have caught that.

    validate() satisfies the PricingGuardrail ABC for interface
    compatibility; evaluate() is what the service actually calls, since it
    needs the adjusted price and human-readable notes back, not just a bool.
    """

    def validate(self, proposed_price: float, context: dict[str, Any]) -> bool:
        result = self.evaluate(
            proposed_price=Decimal(str(proposed_price)),
            current_price=Decimal(str(context["current_price"])),
            cost_price=Decimal(str(context["cost_price"])) if context.get("cost_price") else None,
            constraints=context.get("constraints"),
        )
        return result.passed

    def evaluate(
        self,
        *,
        proposed_price: Decimal,
        current_price: Decimal,
        cost_price: Decimal | None,
        constraints: dict[str, Any] | None,
    ) -> GuardrailResult:
        adjusted, notes = apply_constraints(
            proposed_price, base_price=current_price, cost_price=cost_price, constraints=constraints or {}
        )

        if cost_price is not None and cost_price > 0 and adjusted <= cost_price:
            floor = (cost_price * Decimal("1.01")).quantize(_MONEY)
            notes.append(f"At or below cost price {cost_price}; raised to {floor} (1% minimum margin floor).")
            adjusted = floor

        if adjusted <= 0:
            notes.append("Proposed price was zero or negative; rejected.")
            return GuardrailResult(
                passed=False, proposed_price=proposed_price, adjusted_price=current_price, notes=notes
            )

        return GuardrailResult(
            passed=len(notes) == 0,
            proposed_price=proposed_price,
            adjusted_price=adjusted.quantize(_MONEY),
            notes=notes,
        )
