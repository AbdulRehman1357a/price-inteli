import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.integration_sync_job import IntegrationSyncDirection
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class ExternalPrice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """External-ID mapping for prices, keyed by (integration, sku,
    store_code). price_id points at the most recent Price row
    apply_price() created for this external record — apply_price always
    inserts a new Price row (never updates in place, per Phase 6's price
    *timeline* model), so this column is repointed on every applied
    change. direction records whether the last write here was an inbound
    apply or an outbound push (app.services.integration_push_service), for
    the health dashboard/reconciliation to distinguish "we pulled this"
    from "we pushed this." No organization_id column — tenant scoping
    joins through integration_id.
    """

    __tablename__ = "external_prices"
    __table_args__ = (
        UniqueConstraint(
            "integration_id", "sku", "store_code", name="uq_external_prices_integration_sku_store"
        ),
    )

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    store_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    price_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("prices.id"), nullable=True, index=True
    )
    external_selling_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    direction: Mapped[IntegrationSyncDirection] = mapped_column(
        Enum(IntegrationSyncDirection, native_enum=False, length=10), nullable=False
    )
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
