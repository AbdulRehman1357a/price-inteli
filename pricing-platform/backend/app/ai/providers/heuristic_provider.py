from decimal import Decimal

from app.ai.providers.base import AIPricingProvider, PricingRecommendationInput, RawPricingRecommendation

_MONEY = Decimal("0.0001")

# Days-of-supply thresholds a store manager would recognize: under 2 weeks
# of stock at current sell-through is scarcity, over 2 months is overstock.
_LOW_SUPPLY_DAYS = Decimal("14")
_HIGH_SUPPLY_DAYS = Decimal("60")

_MAX_SCARCITY_INCREASE_PCT = Decimal("8")
_MAX_OVERSTOCK_DISCOUNT_PCT = Decimal("15")
_TARGET_MARGIN_PCT = Decimal("35")
_MAX_MARGIN_NUDGE_PCT = Decimal("5")

_MIN_OBSERVED_UNITS_FOR_SIGNAL = Decimal("5")


class HeuristicPricingProvider(AIPricingProvider):
    """The only provider implemented in this phase: a fully deterministic,
    rule-based scorer — not an LLM call. "Do not use LLM calculations as the
    source of truth" is satisfied trivially here (there's no LLM in the
    loop at all), and this same honesty applies to a future LLM-backed
    provider too: whatever it outputs still has to clear
    DeterministicPricingGuardrail like everything from this provider does.

    Logic, in priority order:
      1. Not enough sales-velocity signal -> a small margin-correction
         nudge only, with low confidence.
      2. Low days-of-supply (selling faster than it can be restocked)
         -> recommend a price increase, scaled by how scarce.
      3. High days-of-supply (overstocked) -> recommend a discount toward
         sell-through, scaled by how overstocked, never below cost.
      4. Otherwise -> nudge toward a target margin.
    """

    name = "heuristic-v1"

    def recommend(self, data: PricingRecommendationInput) -> RawPricingRecommendation:
        velocity = data.sales_velocity_per_day

        has_signal = data.units_sold_lookback >= _MIN_OBSERVED_UNITS_FOR_SIGNAL
        days_of_supply = (data.quantity_available / velocity) if velocity > 0 else None

        confidence = Decimal("0.4")
        if data.cost_price is not None:
            confidence += Decimal("0.2")
        if has_signal:
            confidence += Decimal("0.25")
        if data.reorder_point is not None:
            confidence += Decimal("0.1")
        confidence = min(confidence, Decimal("0.95"))

        if not has_signal or days_of_supply is None:
            price, reason = self._margin_nudge(data)
            confidence = min(confidence, Decimal("0.55"))  # capped: acting on thin data
        elif days_of_supply < _LOW_SUPPLY_DAYS:
            price, reason = self._scarcity_increase(data, days_of_supply)
        elif days_of_supply > _HIGH_SUPPLY_DAYS:
            price, reason = self._overstock_discount(data, days_of_supply)
        else:
            price, reason = self._margin_nudge(data)

        return RawPricingRecommendation(
            recommended_price=price.quantize(_MONEY),
            confidence_score=confidence.quantize(Decimal("0.0001")),
            reason=reason,
            raw_output={
                "days_of_supply": str(days_of_supply) if days_of_supply is not None else None,
                "has_sales_signal": has_signal,
            },
        )

    def _scarcity_increase(
        self, data: PricingRecommendationInput, days_of_supply: Decimal
    ) -> tuple[Decimal, str]:
        # Scarcer stock (relative to the threshold) -> closer to the max increase.
        scarcity_ratio = max(Decimal("0"), (_LOW_SUPPLY_DAYS - days_of_supply) / _LOW_SUPPLY_DAYS)
        pct = (_MAX_SCARCITY_INCREASE_PCT * scarcity_ratio).quantize(Decimal("0.01"))
        price = data.current_price * (Decimal("100") + pct) / Decimal("100")
        reason = (
            f"Only ~{days_of_supply.quantize(Decimal('0.1'))} days of supply left at the current "
            f"sales velocity ({data.sales_velocity_per_day.quantize(Decimal('0.01'))} units/day, "
            f"{data.units_sold_lookback.normalize()} units over the last {data.lookback_days} days). "
            f"Demand is outpacing available stock — recommending a {pct}% increase."
        )
        return price, reason

    def _overstock_discount(
        self, data: PricingRecommendationInput, days_of_supply: Decimal
    ) -> tuple[Decimal, str]:
        excess_ratio = min(Decimal("1"), (days_of_supply - _HIGH_SUPPLY_DAYS) / _HIGH_SUPPLY_DAYS)
        pct = (_MAX_OVERSTOCK_DISCOUNT_PCT * excess_ratio).quantize(Decimal("0.01"))
        price = data.current_price * (Decimal("100") - pct) / Decimal("100")
        reason = (
            f"~{days_of_supply.quantize(Decimal('0.1'))} days of supply on hand at the current sales "
            f"velocity ({data.sales_velocity_per_day.quantize(Decimal('0.01'))} units/day) — stock is "
            f"moving slower than it's being held. Recommending a {pct}% discount to accelerate sell-through."
        )
        return price, reason

    def _margin_nudge(self, data: PricingRecommendationInput) -> tuple[Decimal, str]:
        if data.cost_price is None or data.cost_price <= 0:
            return data.current_price, (
                "No cost price on file and no strong sales-velocity signal — "
                "recommending no change until more data is available."
            )

        target_price = (
            data.cost_price / (Decimal("1") - _TARGET_MARGIN_PCT / Decimal("100"))
        ).quantize(_MONEY)
        current_margin = data.current_margin_percentage
        if current_margin is not None and abs(current_margin - _TARGET_MARGIN_PCT) < Decimal("2"):
            return data.current_price, (
                f"Current margin (~{current_margin.quantize(Decimal('0.1'))}%) is already close to the "
                f"{_TARGET_MARGIN_PCT}% target and sales velocity is unremarkable — no change recommended."
            )

        # Move at most _MAX_MARGIN_NUDGE_PCT of the way toward the target in one recommendation.
        delta = target_price - data.current_price
        capped_delta = max(
            -data.current_price * _MAX_MARGIN_NUDGE_PCT / Decimal("100"),
            min(data.current_price * _MAX_MARGIN_NUDGE_PCT / Decimal("100"), delta),
        )
        price = data.current_price + capped_delta
        direction = "increase" if capped_delta > 0 else "decrease"
        margin_text = (
            f"~{current_margin.quantize(Decimal('0.1'))}%" if current_margin is not None else "unknown"
        )
        reason = (
            f"Sales velocity is steady (no scarcity or overstock signal). Current margin is {margin_text} "
            f"against a {_TARGET_MARGIN_PCT}% target — recommending a small {direction} toward target margin."
        )
        return price, reason
