import uuid
from decimal import Decimal, InvalidOperation
from typing import Literal

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.integration_authority import AuthoritySource
from app.models.integration_mapping import CanonicalEntityType
from app.models.integration_reconciliation import IntegrationReconciliation, IntegrationReconciliationStatus
from app.models.inventory import Inventory
from app.models.mixins import utcnow
from app.repositories.external_inventory_repository import ExternalInventoryRepository
from app.repositories.external_price_repository import ExternalPriceRepository
from app.repositories.integration_authority_repository import IntegrationAuthorityRepository
from app.repositories.integration_reconciliation_repository import IntegrationReconciliationRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.price import PriceUpdate
from app.services import price_service
from app.services.integration_service import get_integration

# Reconciliation is implemented for the two entity types with a direct
# numeric PIP<->external comparison and a well-defined "apply the external
# value" action (spec section 21's own headline example is a price
# mismatch). Product/store/promotion/order reconciliation is left as a
# documented gap — a meaningful generic field-by-field diff for those
# would need re-fetching/re-mapping the raw source record, which is out
# of this pass's bounded scope.
_RECONCILABLE_ENTITY_TYPES = (CanonicalEntityType.PRICE, CanonicalEntityType.INVENTORY)


def run_reconciliation(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, entity_type: CanonicalEntityType
) -> list[IntegrationReconciliation]:
    get_integration(db, organization_id=organization_id, integration_id=integration_id)  # tenant check

    if entity_type == CanonicalEntityType.PRICE:
        return _reconcile_prices(db, organization_id=organization_id, integration_id=integration_id)
    if entity_type == CanonicalEntityType.INVENTORY:
        return _reconcile_inventory(db, organization_id=organization_id, integration_id=integration_id)
    return []


def _authority_for(
    db: Session, *, integration_id: uuid.UUID, entity_type: CanonicalEntityType, field_name: str
) -> AuthoritySource:
    authority = IntegrationAuthorityRepository(db).get_effective(
        integration_id, entity_type=entity_type, field_name=field_name
    )
    return authority.authority if authority is not None else AuthoritySource.EXTERNAL


def _reconcile_prices(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID
) -> list[IntegrationReconciliation]:
    repo = IntegrationReconciliationRepository(db)
    price_repo = PriceRepository(db)
    product_repo = ProductRepository(db)
    store_repo = StoreRepository(db)
    authority = _authority_for(
        db, integration_id=integration_id, entity_type=CanonicalEntityType.PRICE, field_name="selling_price"
    )
    created: list[IntegrationReconciliation] = []

    for ext_price in ExternalPriceRepository(db).list_for_integration(integration_id):
        if ext_price.external_selling_price is None:
            continue
        product = product_repo.get_by_sku(organization_id, ext_price.sku)
        if product is None:
            continue
        store_id = None
        if ext_price.store_code:
            store = store_repo.get_by_code(organization_id, ext_price.store_code)
            if store is None:
                continue
            store_id = store.id
        # Compare against PIP's *current* price for this product/store — not
        # the specific historical Price row external_prices.price_id points
        # to — since a plain (non-integration) price change moves PIP's
        # current price without ever touching that pointer.
        price = price_repo.get_latest_for_product_store(
            organization_id, product_id=product.id, store_id=store_id
        )
        if price is None or price.selling_price == ext_price.external_selling_price:
            continue
        created.append(
            repo.add(
                IntegrationReconciliation(
                    id=uuid.uuid4(),
                    integration_id=integration_id,
                    entity_type=CanonicalEntityType.PRICE,
                    external_id=f"{ext_price.sku}@{ext_price.store_code or ''}",
                    field_name="selling_price",
                    pip_value=str(price.selling_price),
                    external_value=str(ext_price.external_selling_price),
                    authority_at_detection=authority,
                    status=IntegrationReconciliationStatus.OPEN,
                )
            )
        )
    return created


def _reconcile_inventory(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID
) -> list[IntegrationReconciliation]:
    # Inventory rows are looked up by id directly; ExternalInventory already scopes by integration.
    del organization_id
    repo = IntegrationReconciliationRepository(db)
    inventory_repo = InventoryRepository(db)
    authority = _authority_for(
        db,
        integration_id=integration_id,
        entity_type=CanonicalEntityType.INVENTORY,
        field_name="quantity_on_hand",
    )
    created: list[IntegrationReconciliation] = []

    for ext_inv in ExternalInventoryRepository(db).list_for_integration(integration_id):
        if ext_inv.inventory_id is None or ext_inv.quantity_on_hand is None:
            continue
        inventory = inventory_repo.get_by_id(ext_inv.inventory_id)
        if inventory is None or inventory.quantity_on_hand == ext_inv.quantity_on_hand:
            continue
        created.append(
            repo.add(
                IntegrationReconciliation(
                    id=uuid.uuid4(),
                    integration_id=integration_id,
                    entity_type=CanonicalEntityType.INVENTORY,
                    external_id=f"{ext_inv.sku}@{ext_inv.store_code}",
                    field_name="quantity_on_hand",
                    pip_value=str(inventory.quantity_on_hand),
                    external_value=str(ext_inv.quantity_on_hand),
                    authority_at_detection=authority,
                    status=IntegrationReconciliationStatus.OPEN,
                )
            )
        )
    return created


def list_reconciliations(
    db: Session,
    *,
    organization_id: uuid.UUID,
    integration_id: uuid.UUID,
    status: IntegrationReconciliationStatus | None,
    offset: int,
    limit: int,
) -> tuple[list[IntegrationReconciliation], int]:
    get_integration(db, organization_id=organization_id, integration_id=integration_id)  # tenant check
    return IntegrationReconciliationRepository(db).search_for_integration(
        integration_id=integration_id,
        organization_id=organization_id,
        status=status,
        offset=offset,
        limit=limit,
    )


def resolve_reconciliation(
    db: Session,
    *,
    organization_id: uuid.UUID,
    reconciliation_id: uuid.UUID,
    resolution: Literal["keep_pip", "apply_external"],
    resolved_by: uuid.UUID,
) -> IntegrationReconciliation:
    repo = IntegrationReconciliationRepository(db)
    recon = repo.get_by_id_for_organization(reconciliation_id, organization_id)
    if recon is None:
        raise NotFoundError(
            "Integration reconciliation record not found.", code="integration_reconciliation_not_found"
        )

    if resolution == "keep_pip":
        recon.status = IntegrationReconciliationStatus.RESOLVED_PIP_KEPT
    else:
        if recon.entity_type not in _RECONCILABLE_ENTITY_TYPES:
            raise ValidationError(
                f"Applying the external value is not yet supported for entity_type={recon.entity_type.value}."
            )
        _apply_external_value(db, organization_id=organization_id, recon=recon, resolved_by=resolved_by)
        recon.status = IntegrationReconciliationStatus.RESOLVED_EXTERNAL_APPLIED

    recon.resolved_at = utcnow()
    recon.resolved_by = resolved_by
    return repo.add(recon)


def _apply_external_value(
    db: Session, *, organization_id: uuid.UUID, recon: IntegrationReconciliation, resolved_by: uuid.UUID
) -> None:
    """The explicit manual override this reconciliation action represents —
    bypasses authority checking entirely (an admin resolving a flagged
    mismatch has already made the call), unlike the automatic inbound sync
    path in integration_apply_service.
    """
    try:
        external_value = Decimal(recon.external_value) if recon.external_value is not None else None
    except InvalidOperation as exc:
        raise ValidationError("Stored external_value is not a valid number.") from exc
    if external_value is None:
        raise ValidationError("No external_value recorded for this mismatch.")

    if recon.entity_type == CanonicalEntityType.PRICE:
        sku, _, store_code = recon.external_id.partition("@")
        ext_price = ExternalPriceRepository(db).get_by_sku_store(
            recon.integration_id, sku=sku, store_code=store_code or None
        )
        if ext_price is None or ext_price.price_id is None:
            raise NotFoundError("Could not find the price this mismatch refers to.", code="price_not_found")
        price_service.update_price(
            db,
            organization_id=organization_id,
            user_id=resolved_by,
            price_id=ext_price.price_id,
            payload=PriceUpdate(selling_price=external_value, source="integration_reconciliation"),
        )
        return

    if recon.entity_type == CanonicalEntityType.INVENTORY:
        sku, _, store_code = recon.external_id.partition("@")
        ext_inv = ExternalInventoryRepository(db).get_by_sku_store(
            recon.integration_id, sku=sku, store_code=store_code
        )
        if ext_inv is None or ext_inv.inventory_id is None:
            raise NotFoundError(
                "Could not find the inventory row this mismatch refers to.", code="inventory_not_found"
            )
        inventory_repo = InventoryRepository(db)
        inventory: Inventory | None = inventory_repo.get_by_id(ext_inv.inventory_id)
        if inventory is None:
            raise NotFoundError(
                "Could not find the inventory row this mismatch refers to.", code="inventory_not_found"
            )
        inventory.quantity_on_hand = external_value
        inventory.quantity_available = external_value - inventory.quantity_reserved
        inventory.last_stock_update_at = utcnow()
        inventory_repo.add(inventory)
