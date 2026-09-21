import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class ExternalPromotionStatus(enum.StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ExternalPromotion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Staged promotion data (Phase 10 upgrade scope decision: the platform
    has no persisted, pricing-engine-integrated Promotion entity —
    pricing_rules.rule_type="promotion" is a categorization label, not a
    table, see Phase 6 — so synced promotions live here, queryable, but do
    not create/drive a live pricing_rules row. See
    app.services.integration_apply_service.apply_promotion. status is
    computed from start_date/end_date at apply time, not synced verbatim
    from the provider (providers don't agree on a status vocabulary). No
    organization_id column — tenant scoping joins through integration_id.
    """

    __tablename__ = "external_promotions"
    __table_args__ = (
        UniqueConstraint(
            "integration_id",
            "external_promotion_id",
            name="uq_external_promotions_integration_external_promo",
        ),
    )

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    external_promotion_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    discount_percentage: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ExternalPromotionStatus] = mapped_column(
        Enum(ExternalPromotionStatus, native_enum=False, length=20),
        nullable=False,
        default=ExternalPromotionStatus.PENDING,
    )
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
