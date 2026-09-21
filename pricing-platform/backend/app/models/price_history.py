import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class PriceHistory(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Audit trail entry for one price change. Written by PriceService on
    every create/update of a Price row — "every applied price must create
    price history" per the Phase 6 spec. change_type/source are plain
    strings rather than a DB enum since the spec gives no fixed value list
    for either; see app/services/price_service.py for the values this
    codebase actually writes (created/updated/expired/deactivated for
    change_type; "manual" or "rule:<rule name>" for source).
    """

    __tablename__ = "price_history"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("stores.id"), nullable=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("products.id"), nullable=False, index=True
    )
    old_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    new_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("users.id"), nullable=True
    )
