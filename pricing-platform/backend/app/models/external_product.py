import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class ExternalProduct(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The general External ID Mapping mechanism (Phase 10 upgrade spec
    section 5) for products: one row per (integration, external product
    id), pointing at the real PIP Product apply_product upserted. raw_payload
    keeps the untransformed source record for reconciliation/debugging. No
    organization_id column — tenant scoping joins through integration_id.
    """

    __tablename__ = "external_products"
    __table_args__ = (
        UniqueConstraint("integration_id", "external_id", name="uq_external_products_integration_external"),
    )

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_variant_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("products.id"), nullable=True, index=True
    )
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
