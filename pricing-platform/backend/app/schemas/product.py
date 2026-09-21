import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.product import ProductStatus
from app.schemas.common import PaginationParams


class ProductBase(BaseModel):
    """organization_id is deliberately absent — it always comes from the
    authenticated tenant context, never the request body.
    """

    category_id: uuid.UUID
    sku: str = Field(min_length=1, max_length=150)
    barcode: str | None = Field(default=None, max_length=150)
    product_name: str = Field(min_length=1, max_length=255)
    short_description: str | None = Field(default=None, max_length=500)
    description: str | None = None
    brand: str | None = Field(default=None, max_length=255)
    manufacturer: str | None = Field(default=None, max_length=255)
    cost_price: Decimal | None = Field(default=None, max_digits=15, decimal_places=4, ge=0)
    base_price: Decimal | None = Field(default=None, max_digits=15, decimal_places=4, ge=0)
    selling_price: Decimal = Field(max_digits=15, decimal_places=4, ge=0)
    currency: str | None = Field(default=None, max_length=10)
    tax_rate: Decimal | None = Field(default=None, max_digits=8, decimal_places=4, ge=0)
    status: ProductStatus = ProductStatus.ACTIVE
    product_image_url: str | None = Field(default=None, max_length=500)
    product_url: str | None = Field(default=None, max_length=500)
    qr_id: str | None = Field(default=None, max_length=150)
    shelf_id: str | None = Field(default=None, max_length=150)
    weight: Decimal | None = Field(default=None, max_digits=15, decimal_places=4, ge=0)
    weight_unit: str | None = Field(default=None, max_length=20)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    """All fields optional: only keys present in the request body are applied
    (service uses model_dump(exclude_unset=True)).
    """

    category_id: uuid.UUID | None = None
    sku: str | None = Field(default=None, min_length=1, max_length=150)
    barcode: str | None = Field(default=None, max_length=150)
    product_name: str | None = Field(default=None, min_length=1, max_length=255)
    short_description: str | None = Field(default=None, max_length=500)
    description: str | None = None
    brand: str | None = Field(default=None, max_length=255)
    manufacturer: str | None = Field(default=None, max_length=255)
    cost_price: Decimal | None = Field(default=None, max_digits=15, decimal_places=4, ge=0)
    base_price: Decimal | None = Field(default=None, max_digits=15, decimal_places=4, ge=0)
    selling_price: Decimal | None = Field(default=None, max_digits=15, decimal_places=4, ge=0)
    currency: str | None = Field(default=None, max_length=10)
    tax_rate: Decimal | None = Field(default=None, max_digits=8, decimal_places=4, ge=0)
    status: ProductStatus | None = None
    product_image_url: str | None = Field(default=None, max_length=500)
    product_url: str | None = Field(default=None, max_length=500)
    qr_id: str | None = Field(default=None, max_length=150)
    shelf_id: str | None = Field(default=None, max_length=150)
    weight: Decimal | None = Field(default=None, max_digits=15, decimal_places=4, ge=0)
    weight_unit: str | None = Field(default=None, max_length=20)


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    category_id: uuid.UUID
    sku: str
    barcode: str | None
    product_name: str
    short_description: str | None
    description: str | None
    brand: str | None
    manufacturer: str | None
    cost_price: Decimal | None
    base_price: Decimal | None
    selling_price: Decimal
    currency: str | None
    tax_rate: Decimal | None
    status: ProductStatus
    product_image_url: str | None
    product_url: str | None
    qr_id: str | None
    shelf_id: str | None
    weight: Decimal | None
    weight_unit: str | None
    created_at: datetime
    updated_at: datetime


class ProductListParams(PaginationParams):
    search: str | None = Field(default=None, description="Matches sku, barcode, or product_name")
    category_id: uuid.UUID | None = None
    status: ProductStatus | None = None
    sort: str | None = Field(
        default=None,
        description="One of: product_name, -product_name, sku, -sku, selling_price, "
        "-selling_price, created_at, -created_at (default)",
    )


class ProductUrlFetchRequest(BaseModel):
    """A product page URL to pull structured data from (e.g. a Walmart item page).

    Plain str, not HttpUrl, so a user can paste "www.walmart.com/..." without a
    scheme — the fetcher service normalizes it.
    """

    url: str = Field(min_length=1, max_length=1000)


class ProductUrlSuggestion(BaseModel):
    """Best-effort fields extracted from a product page — never applied to the
    database automatically; the user reviews them in the form before saving."""

    url: str | None = None
    # Set when the page couldn't be fetched or yielded no product data — lets the
    # UI show a specific message instead of a generic empty result.
    error: str | None = None
    product_name: str | None = None
    selling_price: str | None = None
    currency: str | None = None
    brand: str | None = None
    sku: str | None = None
    barcode: str | None = None
    product_image_url: str | None = None
    short_description: str | None = None
    description: str | None = None
