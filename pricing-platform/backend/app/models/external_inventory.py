import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class ExternalInventory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """External-ID mapping + last-known external quantity for inventory,
    keyed by (integration, sku, store_code) rather than a single
    external_id — some providers have no distinct per-record inventory id,
    only a (product, location) quantity. quantity_on_hand here is the last
    value *the external system* reported, used by
    app.services.integration_reconciliation_service to compare against
    PIP's own Inventory.quantity_on_hand. No organization_id column —
    tenant scoping joins through integration_id.
    """

    __tablename__ = "external_inventory"
    __table_args__ = (
        UniqueConstraint(
            "integration_id", "sku", "store_code", name="uq_external_inventory_integration_sku_store"
        ),
    )

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    store_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    inventory_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("inventory.id"), nullable=True, index=True
    )
    quantity_on_hand: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
