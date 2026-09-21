import enum
import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.ai_agent import AgentType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PolicyMode(enum.StrEnum):
    RECOMMENDATION_ONLY = "recommendation_only"
    APPROVAL_REQUIRED = "approval_required"
    AUTO_EXECUTE_WITHIN_LIMITS = "auto_execute_within_limits"


class AIPolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The governance settings for one agent_type within one organization —
    at most one row per (organization_id, agent_type). Read by
    agent_service.run_agent to decide, per candidate recommendation,
    whether to leave it PENDING for a human or auto-approve-and-apply it.

    Three independent safety signals must ALL agree before an agent is
    allowed to auto-execute anything: mode == AUTO_EXECUTE_WITHIN_LIMITS,
    approval_required == False, and auto_execute == True — redundant by
    design (each is literally in the Phase 12 spec's column list, so each
    has to actually do something) rather than folding them into one flag.
    None of this ever substitutes for DeterministicPricingGuardrail — see
    app/ai/guardrails.py — which every recommendation still passes through
    regardless of policy mode: "Do not allow an agent to bypass pricing
    guardrails."
    """

    __tablename__ = "ai_policies"
    __table_args__ = (
        UniqueConstraint("organization_id", "agent_type", name="uq_ai_policies_organization_id_agent_type"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    agent_type: Mapped[AgentType] = mapped_column(
        Enum(AgentType, native_enum=False, length=30), nullable=False, index=True
    )
    mode: Mapped[PolicyMode] = mapped_column(
        Enum(PolicyMode, native_enum=False, length=30), nullable=False, default=PolicyMode.RECOMMENDATION_ONLY
    )
    min_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0.7"))
    max_price_change_percent: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), nullable=False, default=Decimal("10")
    )
    min_margin_percent: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=Decimal("15"))
    approval_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_execute: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
