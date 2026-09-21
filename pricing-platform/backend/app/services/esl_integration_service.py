import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.crypto import decrypt_credentials, encrypt_credentials
from app.core.exceptions import ConflictError, NotFoundError
from app.integrations.esl.base import ESLIntegrationAdapter
from app.integrations.esl.registry import get_integration_adapter
from app.models.device import Device
from app.models.device_sync_log import DeviceSyncLog, DeviceSyncStatus
from app.models.esl_integration import ESLIntegration, ESLIntegrationStatus
from app.models.mixins import utcnow
from app.repositories.device_assignment_repository import DeviceAssignmentRepository
from app.repositories.device_repository import DeviceRepository
from app.repositories.device_sync_log_repository import DeviceSyncLogRepository
from app.repositories.device_vendor_repository import DeviceVendorRepository
from app.repositories.esl_integration_repository import ESLIntegrationRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.device import DeviceCreate
from app.schemas.esl_integration import (
    AdapterActionResult,
    DiscoverDevicesResult,
    DiscoveredDevice,
    ESLIntegrationCreate,
    ESLIntegrationListParams,
    ESLIntegrationUpdate,
    ImportDevicesRequest,
    TestPriceUpdateRequest,
)
from app.services import device_service, output_job_service


def _get_vendor(db: Session, vendor_id: uuid.UUID):
    vendor = DeviceVendorRepository(db).get_by_id(vendor_id)
    if vendor is None:
        raise NotFoundError("Device vendor not found.", code="device_vendor_not_found")
    return vendor


def create_integration(
    db: Session, *, organization_id: uuid.UUID, payload: ESLIntegrationCreate
) -> ESLIntegration:
    _get_vendor(db, payload.vendor_id)  # validates the vendor exists
    if StoreRepository(db).get_by_id_for_organization(payload.store_id, organization_id) is None:
        raise NotFoundError("Store not found.", code="store_not_found")

    integration = ESLIntegration(
        id=uuid.uuid4(),
        organization_id=organization_id,
        vendor_id=payload.vendor_id,
        name=payload.name,
        integration_type=payload.integration_type,
        store_id=payload.store_id,
        base_url=payload.base_url,
        configuration_encrypted=encrypt_credentials(payload.credentials) if payload.credentials else None,
        status=ESLIntegrationStatus.PENDING,
    )
    return ESLIntegrationRepository(db).add(integration)


def get_integration(db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID) -> ESLIntegration:
    integration = ESLIntegrationRepository(db).get_by_id_for_organization(integration_id, organization_id)
    if integration is None:
        raise NotFoundError("ESL integration not found.", code="esl_integration_not_found")
    return integration


def list_integrations(
    db: Session, *, organization_id: uuid.UUID, params: ESLIntegrationListParams
) -> tuple[list[ESLIntegration], int]:
    offset = (params.page - 1) * params.page_size
    return ESLIntegrationRepository(db).search(
        organization_id,
        vendor_id=params.vendor_id,
        integration_type=params.integration_type,
        status=params.status,
        offset=offset,
        limit=params.page_size,
    )


def update_integration(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, payload: ESLIntegrationUpdate
) -> ESLIntegration:
    integration = get_integration(db, organization_id=organization_id, integration_id=integration_id)
    data = payload.model_dump(exclude_unset=True)

    if "name" in data:
        integration.name = data["name"]
    if "base_url" in data:
        integration.base_url = data["base_url"]
    if "store_id" in data:
        if StoreRepository(db).get_by_id_for_organization(data["store_id"], organization_id) is None:
            raise NotFoundError("Store not found.", code="store_not_found")
        integration.store_id = data["store_id"]
    if "status" in data:
        integration.status = data["status"]
    if data.get("credentials") is not None:
        integration.configuration_encrypted = encrypt_credentials(data["credentials"])

    return ESLIntegrationRepository(db).add(integration)


def delete_integration(db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID) -> None:
    integration = get_integration(db, organization_id=organization_id, integration_id=integration_id)

    if DeviceRepository(db).count_by_esl_integration(integration.id) > 0:
        raise ConflictError(
            "This integration has devices imported through it — reassign or remove them first.",
            code="esl_integration_has_devices",
        )

    ESLIntegrationRepository(db).delete(integration)


def _decrypt(integration: ESLIntegration) -> dict[str, Any]:
    if not integration.configuration_encrypted:
        return {}
    return decrypt_credentials(integration.configuration_encrypted)


def _adapter_for(db: Session, integration: ESLIntegration) -> ESLIntegrationAdapter:
    vendor = _get_vendor(db, integration.vendor_id)
    return get_integration_adapter(integration.integration_type, vendor.code)


async def test_connection(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID
) -> AdapterActionResult:
    integration = get_integration(db, organization_id=organization_id, integration_id=integration_id)
    adapter = _adapter_for(db, integration)
    result = await adapter.test_connection(integration, _decrypt(integration))

    integration.status = (
        ESLIntegrationStatus.ACTIVE if result.get("success") else ESLIntegrationStatus.ERROR
    )
    ESLIntegrationRepository(db).add(integration)

    return AdapterActionResult(success=bool(result.get("success")), message=result.get("message"))


async def discover_devices(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID
) -> DiscoverDevicesResult:
    integration = get_integration(db, organization_id=organization_id, integration_id=integration_id)
    adapter = _adapter_for(db, integration)
    result = await adapter.discover_devices(integration, _decrypt(integration))

    return DiscoverDevicesResult(
        success=bool(result.get("success")),
        message=result.get("message"),
        devices=[DiscoveredDevice(**d) for d in result.get("devices", [])],
    )


def import_devices(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, payload: ImportDevicesRequest
) -> list[Device]:
    integration = get_integration(db, organization_id=organization_id, integration_id=integration_id)
    if integration.store_id is None:
        raise ConflictError(
            "Set a store on this integration before importing devices.",
            code="esl_integration_missing_store",
        )

    created: list[Device] = []
    for item in payload.devices:
        device = device_service.create_device(
            db,
            organization_id=organization_id,
            payload=DeviceCreate(
                store_id=integration.store_id,
                vendor_id=integration.vendor_id,
                device_model_id=payload.device_model_id,
                device_identifier=item.device_identifier,
                device_name=item.device_name,
            ),
        )
        device.esl_integration_id = integration.id
        DeviceRepository(db).add(device)
        created.append(device)

    return created


async def test_price_update(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, payload: TestPriceUpdateRequest
) -> AdapterActionResult:
    integration = get_integration(db, organization_id=organization_id, integration_id=integration_id)
    device = device_service.get_device(db, organization_id=organization_id, device_id=payload.device_id)

    product_id = payload.product_id
    if product_id is None:
        assignment = DeviceAssignmentRepository(db).get_active_for_device(device.id)
        if assignment is None:
            raise ConflictError(
                "This device has no assigned product to test.", code="device_no_assignment"
            )
        product_id = assignment.product_id

    product = ProductRepository(db).get_by_id_for_organization(product_id, organization_id)
    if product is None:
        raise NotFoundError("Product not found.", code="product_not_found")

    price, currency = output_job_service.resolve_display_price(
        db, organization_id=organization_id, product=product, store_id=device.store_id
    )
    adapter = _adapter_for(db, integration)
    result = await adapter.push_price(
        integration,
        _decrypt(integration),
        device_identifier=device.device_identifier,
        payload={
            "product_name": product.product_name,
            "sku": product.sku,
            "price": str(price),
            "currency": currency,
            "store_id": str(device.store_id),
        },
    )

    now = utcnow()
    integration.last_sync_at = now
    ESLIntegrationRepository(db).add(integration)

    success = bool(result.get("success"))
    DeviceSyncLogRepository(db).add(
        DeviceSyncLog(
            id=uuid.uuid4(),
            device_id=device.id,
            product_id=product.id,
            output_job_id=None,
            status=DeviceSyncStatus.SUCCESS if success else DeviceSyncStatus.FAILED,
            error_message=None if success else result.get("message"),
            completed_at=now,
        )
    )

    return AdapterActionResult(success=success, message=result.get("message"))


async def get_sync_status(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID
) -> AdapterActionResult:
    integration = get_integration(db, organization_id=organization_id, integration_id=integration_id)
    adapter = _adapter_for(db, integration)
    result = await adapter.get_sync_status(integration, _decrypt(integration))

    extra = {k: v for k, v in result.items() if k not in ("success", "message")}
    return AdapterActionResult(
        success=bool(result.get("success")), message=result.get("message"), extra=extra
    )
