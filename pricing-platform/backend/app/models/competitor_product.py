import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CompetitorProductStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class CompetitorProduct(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Links one of our products to its equivalent listing at a competitor.

    No organization_id column (not in the literal spec) — tenant scoping is
    enforced by joining through competitor_id -> Competitor.organization_id,
    same precedent as Phase 8's device_assignments/device_sync_logs.
    updated_at is additive for the same reason as Competitor (match_confidence
    and status are both editable).
    """

    __tablename__ = "competitor_products"

    competitor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("competitors.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("products.id"), nullable=False, index=True
    )
    external_product_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    match_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    status: Mapped[CompetitorProductStatus] = mapped_column(
        Enum(CompetitorProductStatus, native_enum=False, length=20),
        nullable=False,
        default=CompetitorProductStatus.ACTIVE,
    )
