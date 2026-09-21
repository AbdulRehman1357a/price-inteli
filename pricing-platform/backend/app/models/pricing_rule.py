import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RuleType(enum.StrEnum):
    FIXED_PRICE = "fixed_price"
    PERCENTAGE_DISCOUNT = "percentage_discount"
    FIXED_DISCOUNT = "fixed_discount"
    MARGIN_BASED = "margin_based"
    COST_PLUS = "cost_plus"
    INVENTORY_BASED = "inventory_based"
    TIME_BASED = "time_based"
    STORE_SPECIFIC = "store_specific"
    PROMOTION = "promotion"
    CLEARANCE = "clearance"


class RuleStatus(enum.StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


class PricingRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A deterministic pricing rule. rule_type is descriptive/categorization
    (for the UI and filtering) — the actual calculation the engine performs
    is read from actions_json.kind, decoupling "why this rule exists" from
    "what math it runs" (a Promotion can be a percentage discount OR a fixed
    price, etc.). See app/services/pricing_engine.py for the full contract
    of conditions_json / actions_json / constraints_json.

    Only ACTIVE rules whose effective window covers "now" are matched
    during normal evaluation; DRAFT rules can still be evaluated explicitly
    via POST /pricing/rules/{id}/test to preview a not-yet-active rule.
    """

    __tablename__ = "pricing_rules"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_type: Mapped[RuleType] = mapped_column(Enum(RuleType, native_enum=False, length=30), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    conditions_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    actions_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    constraints_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    approval_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[RuleStatus] = mapped_column(
        Enum(RuleStatus, native_enum=False, length=20), nullable=False, default=RuleStatus.DRAFT
    )
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
