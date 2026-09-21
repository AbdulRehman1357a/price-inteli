import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.inventory_adjustment import AdjustmentType
from app.schemas.common import PaginationParams

InventoryStatus = Literal["out_of_stock", "low_stock", "overstock", "in_stock"]


class InventoryCreate(BaseModel):
    """organization_id is deliberately absent — it always comes from the
    authenticated tenant context, never the request body.
    """

    store_id: uuid.UUID
    product_id: uuid.UUID
    quantity_on_hand: Decimal = Field(default=Decimal("0"), max_digits=15, decimal_places=4, ge=0)
    quantity_reserved: Decimal = Field(default=Decimal("0"), max_digits=15, decimal_places=4, ge=0)
    reorder_point: Decimal | None = Field(default=None, max_digits=15, decimal_places=4, ge=0)
    safety_stock: Decimal | None = Field(default=None, max_digits=15, decimal_places=4, ge=0)


class InventoryUpdate(BaseModel):
    """Settings-only update — quantity_on_hand is never changed here.

    Stock movements go through POST /inventory/bulk-update instead, which
    records an audited reason and enforces the no-negative-stock rule.
    Only keys present in the request body are applied (service uses
    model_dump(exclude_unset=True)).
    """

    quantity_reserved: Decimal | None = Field(default=None, max_digits=15, decimal_places=4, ge=0)
    reorder_point: Decimal | None = Field(default=None, max_digits=15, decimal_places=4, ge=0)
    safety_stock: Decimal | None = Field(default=None, max_digits=15, decimal_places=4, ge=0)


class InventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    store_id: uuid.UUID
    product_id: uuid.UUID
    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    quantity_available: Decimal
    reorder_point: Decimal | None
    safety_stock: Decimal | None
    last_stock_update_at: datetime | None
    created_at: datetime
    updated_at: datetime
    status: InventoryStatus
    # Denormalized for the inventory table's Product/SKU/Store columns, so
    # the frontend doesn't need an N+1 lookup per row.
    product_name: str
    product_sku: str
    store_name: str
    store_code: str


class InventoryListParams(PaginationParams):
    store_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    low_stock: bool | None = None
    out_of_stock: bool | None = None


class InventoryAdjustmentItem(BaseModel):
    store_id: uuid.UUID
    product_id: uuid.UUID
    adjustment_type: AdjustmentType
    adjustment_quantity: Decimal = Field(max_digits=15, decimal_places=4, ge=0)
    reason: str = Field(min_length=1, max_length=255)
    notes: str | None = None
    allow_negative: bool = Field(
        default=False,
        description="Explicitly permit this specific adjustment to drive quantity_on_hand negative.",
    )


class BulkInventoryUpdateRequest(BaseModel):
    items: list[InventoryAdjustmentItem] = Field(min_length=1)


class InventorySummary(BaseModel):
    total_products: int
    low_stock: int
    out_of_stock: int
    overstock: int
