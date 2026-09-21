import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Inventory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stock level for one product at one store. One row per (store, product)
    — quantity_available is maintained by the service layer as
    quantity_on_hand - quantity_reserved on every write, not a DB-computed
    column, to keep it portable across the SQLite test DB and MySQL. No
    deleted_at — not in the Phase 4 spec, and a store/product combination is
    either tracked or not (there's no DELETE endpoint in this phase either).
    """

    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "store_id", "product_id", name="uq_inventory_org_store_product"
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("stores.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("products.id"), nullable=False, index=True
    )
    quantity_on_hand: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=0)
    quantity_reserved: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=0)
    quantity_available: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=0)
    reorder_point: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    safety_stock: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    last_stock_update_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
