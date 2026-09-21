import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.inventory import Inventory
from app.models.inventory_adjustment import AdjustmentType, InventoryAdjustment
from app.models.mixins import utcnow
from app.models.product import Product
from app.models.store import Store
from app.repositories.inventory_adjustment_repository import InventoryAdjustmentRepository
from app.repositories.inventory_repository import OVERSTOCK_MULTIPLIER, InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.inventory import (
    BulkInventoryUpdateRequest,
    InventoryCreate,
    InventoryListParams,
    InventoryStatus,
    InventorySummary,
    InventoryUpdate,
)


def compute_status(item: Inventory) -> InventoryStatus:
    if item.quantity_available <= 0:
        return "out_of_stock"
    if item.reorder_point is not None and item.quantity_available <= item.reorder_point:
        return "low_stock"
    if item.reorder_point is not None and item.quantity_on_hand > item.reorder_point * OVERSTOCK_MULTIPLIER:
        return "overstock"
    return "in_stock"


def _recompute_available(item: Inventory) -> None:
    item.quantity_available = item.quantity_on_hand - item.quantity_reserved


def get_display_details(db: Session, items: list[Inventory]) -> dict[uuid.UUID, dict[str, str]]:
    """Batch-loads the product/store display fields InventoryOut needs
    (product_name, product_sku, store_name, store_code), in two queries
    total regardless of how many inventory rows are being rendered —
    avoids an N+1 lookup per row in the inventory table.
    """
    if not items:
        return {}

    product_ids = {item.product_id for item in items}
    store_ids = {item.store_id for item in items}
    products = {
        p.id: p for p in db.execute(select(Product).where(Product.id.in_(product_ids))).scalars()
    }
    stores = {s.id: s for s in db.execute(select(Store).where(Store.id.in_(store_ids))).scalars()}

    details: dict[uuid.UUID, dict[str, str]] = {}
    for item in items:
        product = products.get(item.product_id)
        store = stores.get(item.store_id)
        if product is None or store is None:
            continue
        details[item.id] = {
            "product_name": product.product_name,
            "product_sku": product.sku,
            "store_name": store.name,
            "store_code": store.store_code,
        }
    return details


def _validate_store_and_product(
    db: Session, *, organization_id: uuid.UUID, store_id: uuid.UUID, product_id: uuid.UUID
) -> None:
    if StoreRepository(db).get_by_id_for_organization(store_id, organization_id) is None:
        raise NotFoundError("Store not found.", code="store_not_found")
    if ProductRepository(db).get_by_id_for_organization(product_id, organization_id) is None:
        raise NotFoundError("Product not found.", code="product_not_found")


def create_inventory(db: Session, *, organization_id: uuid.UUID, payload: InventoryCreate) -> Inventory:
    repo = InventoryRepository(db)
    _validate_store_and_product(
        db, organization_id=organization_id, store_id=payload.store_id, product_id=payload.product_id
    )
    if repo.get_by_store_and_product(organization_id, payload.store_id, payload.product_id) is not None:
        raise ConflictError(
            "Inventory is already tracked for this store and product.", code="inventory_exists"
        )

    inventory = Inventory(
        id=uuid.uuid4(),
        organization_id=organization_id,
        last_stock_update_at=utcnow(),
        **payload.model_dump(),
    )
    _recompute_available(inventory)
    return repo.add(inventory)


def get_inventory(db: Session, *, organization_id: uuid.UUID, inventory_id: uuid.UUID) -> Inventory:
    inventory = InventoryRepository(db).get_by_id_for_organization(inventory_id, organization_id)
    if inventory is None:
        raise NotFoundError("Inventory record not found.", code="inventory_not_found")
    return inventory


def list_inventory(
    db: Session, *, organization_id: uuid.UUID, params: InventoryListParams
) -> tuple[list[Inventory], int]:
    repo = InventoryRepository(db)
    offset = (params.page - 1) * params.page_size
    return repo.search(
        organization_id,
        store_id=params.store_id,
        category_id=params.category_id,
        product_id=params.product_id,
        low_stock=params.low_stock,
        out_of_stock=params.out_of_stock,
        offset=offset,
        limit=params.page_size,
    )


def get_summary(
    db: Session,
    *,
    organization_id: uuid.UUID,
    store_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
) -> InventorySummary:
    counts = InventoryRepository(db).summary_counts(
        organization_id, store_id=store_id, category_id=category_id, product_id=product_id
    )
    return InventorySummary(**counts)


def update_inventory(
    db: Session, *, organization_id: uuid.UUID, inventory_id: uuid.UUID, payload: InventoryUpdate
) -> Inventory:
    inventory = get_inventory(db, organization_id=organization_id, inventory_id=inventory_id)
    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(inventory, field, value)
    if "quantity_reserved" in updates:
        _recompute_available(inventory)

    return InventoryRepository(db).add(inventory)


def bulk_update(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: BulkInventoryUpdateRequest,
) -> list[Inventory]:
    """Applies every item atomically: if any one fails (unknown store/
    product, missing inventory record, or a would-be-negative on-hand
    quantity without allow_negative), the whole request rolls back — this
    is one database transaction, same as every other write in the app.
    """
    inventory_repo = InventoryRepository(db)
    adjustment_repo = InventoryAdjustmentRepository(db)
    updated: list[Inventory] = []

    for item in payload.items:
        inventory = inventory_repo.get_by_store_and_product(organization_id, item.store_id, item.product_id)
        if inventory is None:
            raise NotFoundError(
                "No inventory record exists for this store and product — create one first.",
                code="inventory_not_found",
            )

        quantity_before: Decimal = inventory.quantity_on_hand
        if item.adjustment_type == AdjustmentType.INCREASE:
            new_on_hand = quantity_before + item.adjustment_quantity
        elif item.adjustment_type == AdjustmentType.DECREASE:
            new_on_hand = quantity_before - item.adjustment_quantity
        else:  # CORRECTION: an absolute recount value, not a delta
            new_on_hand = item.adjustment_quantity

        if new_on_hand < 0 and not item.allow_negative:
            raise ConflictError(
                "This adjustment would make on-hand quantity negative.",
                code="negative_inventory_not_allowed",
            )

        inventory.quantity_on_hand = new_on_hand
        _recompute_available(inventory)
        inventory.last_stock_update_at = utcnow()
        inventory_repo.add(inventory)

        adjustment_repo.add(
            InventoryAdjustment(
                id=uuid.uuid4(),
                organization_id=organization_id,
                inventory_id=inventory.id,
                adjustment_type=item.adjustment_type,
                adjustment_quantity=item.adjustment_quantity,
                quantity_before=quantity_before,
                quantity_after=new_on_hand,
                reason=item.reason,
                notes=item.notes,
                created_by_user_id=user_id,
            )
        )
        updated.append(inventory)

    return updated
