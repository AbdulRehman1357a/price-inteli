import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.ai_pricing_recommendation import RecommendationStatus
from app.schemas.common import PaginationParams
from app.schemas.price import PriceHistoryOut


class GenerateRecommendationRequest(BaseModel):
    product_id: uuid.UUID
    store_id: uuid.UUID | None = None
    provider: str | None = Field(default=None, description="Defaults to the heuristic provider.")


class ModifyRecommendationRequest(BaseModel):
    """A reviewer's proposed replacement price. Still re-validated through
    the same DeterministicPricingGuardrail as the AI's original candidate —
    a human overriding the number doesn't bypass the guardrails either.
    """

    recommended_price: Decimal = Field(max_digits=15, decimal_places=4, gt=0)


class AIPricingRecommendationListParams(PaginationParams):
    status: RecommendationStatus | None = None
    product_id: uuid.UUID | None = None
    store_id: uuid.UUID | None = None


class AIPricingRecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    store_id: uuid.UUID | None
    product_id: uuid.UUID
    current_price: Decimal
    recommended_price: Decimal
    confidence_score: Decimal
    recommendation_reason: str
    status: RecommendationStatus
    created_by_agent: str
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AIPricingRecommendationListItem(AIPricingRecommendationOut):
    product_name: str
    sku: str
    store_name: str | None
    price_difference: Decimal
    price_difference_percentage: Decimal | None


class AIPricingRecommendationDetail(AIPricingRecommendationListItem):
    category_name: str
    input_snapshot: dict
    price_history: list[PriceHistoryOut]
