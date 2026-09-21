from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class PricingRecommendationInput:
    """Every input the Phase 11 spec lists, gathered by
    pricing_recommendation_service before a provider is called — a provider
    never queries the database directly (same separation as
    app/outputs/base.py's OutputRenderContext / app/integrations/base.py).
    """

    product_id: str
    product_name: str
    sku: str
    category_name: str
    store_id: str | None
    store_name: str | None
    cost_price: Decimal | None
    current_price: Decimal
    current_margin_percentage: Decimal | None
    quantity_on_hand: Decimal
    quantity_available: Decimal
    reorder_point: Decimal | None
    sales_velocity_per_day: Decimal
    units_sold_lookback: Decimal
    lookback_days: int
    applicable_rule_names: list[str]


@dataclass
class RawPricingRecommendation:
    """A provider's candidate output, BEFORE deterministic guardrail
    validation — never persisted or shown to a user as-is. See
    app/ai/guardrails.py and pricing_recommendation_service.generate_recommendation,
    which always clamps this through DeterministicPricingGuardrail before
    building the AIPricingRecommendation row.
    """

    recommended_price: Decimal
    confidence_score: Decimal  # 0..1
    reason: str
    raw_output: dict[str, Any]


class AIPricingProvider(ABC):
    """Rule: the system must support different providers later (e.g. a real
    LLM-backed one) without changing calling code — same adapter/registry
    pattern as OutputAdapter, ESLIntegrationAdapter, IntegrationAdapter.
    Whatever a provider returns is a *candidate* only: "Do not use LLM
    calculations as the source of truth" is enforced structurally by never
    letting a provider's output reach the database without first passing
    through DeterministicPricingGuardrail in the service layer.
    """

    name: str

    @abstractmethod
    def recommend(self, data: PricingRecommendationInput) -> RawPricingRecommendation: ...
