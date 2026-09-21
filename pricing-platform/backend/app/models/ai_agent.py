import enum
import uuid

from sqlalchemy import JSON, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AgentType(enum.StrEnum):
    """The 5 agents from the Phase 12 spec. Only PRICING_OPTIMIZATION has a
    real implementation in this phase (app/ai/agents/pricing_optimization_agent.py)
    — the other 4 are valid, configurable catalog entries (an AIAgent row
    can be created with any of them, same as Phase 9's ESL vendor stubs or
    Phase 10's SAP/Oracle catalog entries), but app/ai/agents/registry.py
    has no Agent implementation registered for them yet, so running one
    fails with an explicit "not implemented" error rather than pretending
    to do something. "Implement one agent at a time. Start with Pricing
    Optimization Agent" per the spec.
    """

    PRICING_OPTIMIZATION = "pricing_optimization"
    INVENTORY_HEALTH = "inventory_health"
    PROMOTION = "promotion"
    DEVICE_OPERATIONS = "device_operations"
    INTEGRATION_MONITORING = "integration_monitoring"


class AgentStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class AIAgent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One configured agent instance for an organization — e.g. "Nightly
    Price Optimizer" of type pricing_optimization. configuration_json holds
    the scope an agent run evaluates (product/category/store filters, a max
    products per run) and a "schedule" value (e.g. "manual"/"daily") that is
    stored for display/future use only — this codebase has no periodic-task
    scheduler anywhere yet (see pricing_recommendation_service.expire_stale_recommendations'
    docstring for the same honest limitation), so every run in this phase is
    triggered manually via POST /ai-agents/{id}/run; nothing executes on a
    timer.

    updated_at (via TimestampMixin) isn't in the literal Phase 12 column
    list but is required — the Agent Management UI edits name/status/
    configuration in place, same precedent as AIPricingRecommendation.
    """

    __tablename__ = "ai_agents"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    agent_type: Mapped[AgentType] = mapped_column(
        Enum(AgentType, native_enum=False, length=30), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, native_enum=False, length=20), nullable=False, default=AgentStatus.ACTIVE
    )
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
