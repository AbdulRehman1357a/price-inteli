import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin, utcnow


class CompetitorPrice(UUIDPrimaryKeyMixin, Base):
    """One observed price point for a competitor_product — an append-only
    timeline (many rows per competitor_product over time), never updated in
    place, so there's no updated_at and captured_at (not created_at) is the
    literal spec's timestamp column. source is a free string ("manual" |
    "api") rather than a DB enum, same precedent as PriceHistory.source.
    """

    __tablename__ = "competitor_prices"

    competitor_product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("competitor_products.id"),
        nullable=False,
        index=True,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    availability: Mapped[str | None] = mapped_column(String(50), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
