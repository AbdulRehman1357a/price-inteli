import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ProductStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"


class Product(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A product belonging to one organization (tenant) and one category."""

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_products_organization_id_sku"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("categories.id"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(150), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(150), nullable=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Not in the original Phase 3 DB spec — added because the "Product UI
    # Fields" list explicitly asks for a Brand field distinct from
    # Manufacturer (e.g. "Nike" the brand vs. the contract manufacturer).
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    base_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus, native_enum=False, length=20), nullable=False, default=ProductStatus.ACTIVE
    )
    product_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    weight_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Product URL is the retailer product page the item was pulled from (e.g. a
    # Walmart item page) — see app/services/product_url_fetcher.py. QR ID / Shelf
    # ID are plain identifiers added for the QR/shelf-label follow-up work.
    product_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    qr_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    shelf_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
