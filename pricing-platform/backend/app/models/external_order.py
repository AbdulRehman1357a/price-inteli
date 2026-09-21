import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class ExternalOrder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Staged sales/order data (Phase 10 upgrade scope decision: sales
    velocity/order sync has no persisted domain Order entity to reconcile
    into — see app.services.integration_apply_service.apply_order — so
    synced orders live here, queryable for future analytics use, without
    inventing a pricing-engine-integrated Order model. line_items is
    inlined JSON (a list of {sku, external_variant_id, quantity,
    unit_price, line_total} dicts) rather than a normalized child table,
    since nothing else in the platform queries order lines relationally —
    same precedent as IntegrationSyncJob.error_details/pushed_records. No
    organization_id column — tenant scoping joins through integration_id.
    """

    __tablename__ = "external_orders"
    __table_args__ = (
        UniqueConstraint(
            "integration_id", "external_order_id", name="uq_external_orders_integration_external_order"
        ),
    )

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    external_order_id: Mapped[str] = mapped_column(String(255), nullable=False)
    store_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    tax_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    total: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    line_items: Mapped[list] = mapped_column(JSON, nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
