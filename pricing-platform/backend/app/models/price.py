import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class PriceType(enum.StrEnum):
    REGULAR = "regular"
    PROMOTIONAL = "promotional"
    CLEARANCE = "clearance"
    CONTRACT = "contract"


class PriceStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SCHEDULED = "scheduled"
    EXPIRED = "expired"


class Price(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One priced period for a product (optionally store-specific). Multiple
    rows per product are expected and normal — this is a price *timeline*
    (past/current/future periods), not a single mutable "the price" field.
    Every create/update writes a PriceHistory row (see price_history.py).
    No soft delete — not in the Phase 6 spec, and an expired/superseded
    price period is still meaningful history, not something to hide.
    """

    __tablename__ = "prices"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("stores.id"), nullable=True, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("products.id"), nullable=False, index=True
    )
    price_type: Mapped[PriceType] = mapped_column(
        Enum(PriceType, native_enum=False, length=20), nullable=False, default=PriceType.REGULAR
    )
    base_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[PriceStatus] = mapped_column(
        Enum(PriceStatus, native_enum=False, length=20), nullable=False, default=PriceStatus.ACTIVE
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("users.id"), nullable=True
    )
