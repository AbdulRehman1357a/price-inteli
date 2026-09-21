import enum
import uuid

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RoutingRuleStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class OutputRoutingRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A deterministic dispatch rule: when a price change matches
    conditions_json (product/category/store scope — same shape as
    PricingRule.conditions_json), every output_type listed in
    target_outputs_json gets a job created against each of that org's
    active OutputChannels of that type. See app/services/output_router_service.py
    for the full Observe->Route->Create Jobs pipeline.

    updated_at (via TimestampMixin) isn't in the literal Phase 14 column
    list but is required — rules are editable, same precedent as every
    other rule/policy table in this codebase (PricingRule, AIPolicy).
    """

    __tablename__ = "output_routing_rules"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    conditions_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    target_outputs_json: Mapped[list] = mapped_column(JSON, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    status: Mapped[RoutingRuleStatus] = mapped_column(
        Enum(RoutingRuleStatus, native_enum=False, length=20),
        nullable=False,
        default=RoutingRuleStatus.ACTIVE,
    )
