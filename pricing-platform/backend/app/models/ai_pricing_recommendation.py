import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RecommendationStatus(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    EXPIRED = "expired"


class AIPricingRecommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One AI-generated pricing suggestion for a product (optionally scoped
    to one store), always human-reviewed before it can affect a real price.

    Recommendation-only by design: nothing in this model or the service that
    writes it ever touches the `prices` table directly. Only an explicit,
    separately-authorized "apply" action (requiring status=APPROVED) creates
    a real Price row, and it does so through the existing deterministic
    price_service.create_price() — the same path a human manually setting a
    price uses. AI never bypasses that.

    updated_at (via TimestampMixin) isn't in the literal Phase 11 column
    list but is required here — unlike most audit-trail tables in this
    codebase, this row is genuinely mutated in place by review actions
    (status/reviewed_by/reviewed_at, and recommended_price on "modify").
    """

    __tablename__ = "ai_pricing_recommendations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("stores.id"), nullable=True, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("products.id"), nullable=False, index=True
    )
    current_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    recommended_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    recommendation_reason: Mapped[str] = mapped_column(Text, nullable=False)
    # Snapshot of every input the recommendation was computed from (cost,
    # inventory, sales-velocity proxy, margin, category, store, in-force
    # pricing rules), plus the guardrail evaluation and expected-impact
    # figures computed alongside it — kept together here since there's no
    # separate column for either and both belong to "what this
    # recommendation was based on" for audit/detail-view purposes.
    input_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus, native_enum=False, length=20),
        nullable=False,
        default=RecommendationStatus.PENDING,
        index=True,
    )
    created_by_agent: Mapped[str] = mapped_column(String(100), nullable=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
