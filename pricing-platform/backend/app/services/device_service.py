import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.integrations.registry import get_esl_adapter
from app.models.device import Device
from app.repositories.device_assignment_repository import DeviceAssignmentRepository
from app.repositories.device_model_repository import DeviceModelRepository
from app.repositories.device_repository import DeviceRepository
from app.repositories.device_sync_log_repository import DeviceSyncLogRepository
from app.repositories.device_vendor_repository import DeviceVendorRepository
from app.repositories.esl_integration_repository import ESLIntegrationRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.device import DeviceCreate, DeviceHealthOut, DeviceListParams, DeviceUpdate


def _get_vendor(db: Session, vendor_id: uuid.UUID):
    vendor = DeviceVendorRepository(db).get_by_id(vendor_id)
    if vendor is None:
        raise NotFoundError("Device vendor not found.", code="device_vendor_not_found")
    return vendor


def _get_model(db: Session, device_model_id: uuid.UUID, *, vendor_id: uuid.UUID):
    device_model = DeviceModelRepository(db).get_by_id(device_model_id)
    if device_model is None:
        raise NotFoundError("Device model not found.", code="device_model_not_found")
    if device_model.vendor_id != vendor_id:
        raise ConflictError(
            "This device model does not belong to the selected vendor.", code="device_model_vendor_mismatch"
        )
    return device_model


def create_device(db: Session, *, organization_id: uuid.UUID, payload: DeviceCreate) -> Device:
    esl_integration_id = payload.esl_integration_id
    store_id = payload.store_id
    vendor_id = payload.vendor_id

    if esl_integration_id is not None:
        # Plugging a device into an existing vendor integration — store and
        # vendor are server-derived from it, not client-sent (same
        # precedent as esl_integration_service.import_devices), so the two
        # can never drift apart.
        integration = ESLIntegrationRepository(db).get_by_id_for_organization(
            esl_integration_id, organization_id
        )
        if integration is None:
            raise NotFoundError("ESL integration not found.", code="esl_integration_not_found")
        if integration.store_id is None:
            raise ConflictError(
                "Set a store on this integration before adding devices.",
                code="esl_integration_missing_store",
            )
        store_id = integration.store_id
        vendor_id = integration.vendor_id

    if StoreRepository(db).get_by_id_for_organization(store_id, organization_id) is None:
        raise NotFoundError("Store not found.", code="store_not_found")
    vendor = _get_vendor(db, vendor_id)
    _get_model(db, payload.device_model_id, vendor_id=vendor.id)

    device_repo = DeviceRepository(db)
    if device_repo.get_by_identifier(organization_id, payload.device_identifier) is not None:
        raise ConflictError(
            "A device with this identifier already exists.", code="device_identifier_taken"
        )

    device = Device(
        id=uuid.uuid4(),
        organization_id=organization_id,
        store_id=store_id,
        vendor_id=vendor_id,
        esl_integration_id=esl_integration_id,
        device_model_id=payload.device_model_id,
        device_identifier=payload.device_identifier,
        device_name=payload.device_name,
        status=payload.status,
        battery_level=100,
        signal_strength=95,
        firmware_version="1.0.0-sim",
    )
    device = device_repo.add(device)

    adapter = get_esl_adapter(vendor.code)
    adapter.register_device(device)

    return device


def get_device(db: Session, *, organization_id: uuid.UUID, device_id: uuid.UUID) -> Device:
    device = DeviceRepository(db).get_by_id_for_organization(device_id, organization_id)
    if device is None:
        raise NotFoundError("Device not found.", code="device_not_found")
    return device


def list_devices(
    db: Session, *, organization_id: uuid.UUID, params: DeviceListParams
) -> tuple[list[Device], int]:
    offset = (params.page - 1) * params.page_size
    return DeviceRepository(db).search(
        organization_id,
        store_id=params.store_id,
        vendor_id=params.vendor_id,
        esl_integration_id=params.esl_integration_id,
        device_model_id=params.device_model_id,
        status=params.status,
        search=params.search,
        offset=offset,
        limit=params.page_size,
    )


def update_device(
    db: Session, *, organization_id: uuid.UUID, device_id: uuid.UUID, payload: DeviceUpdate
) -> Device:
    device = get_device(db, organization_id=organization_id, device_id=device_id)
    data = payload.model_dump(exclude_unset=True)

    if "store_id" in data:
        if StoreRepository(db).get_by_id_for_organization(data["store_id"], organization_id) is None:
            raise NotFoundError("Store not found.", code="store_not_found")
        device.store_id = data["store_id"]
    if "device_name" in data:
        device.device_name = data["device_name"]
    if "status" in data:
        device.status = data["status"]

    return DeviceRepository(db).add(device)


def delete_device(db: Session, *, organization_id: uuid.UUID, device_id: uuid.UUID) -> None:
    device = get_device(db, organization_id=organization_id, device_id=device_id)

    # Assignments and sync logs only make sense attached to their device
    # (and their FK to devices.id has no ON DELETE CASCADE), so they go with it.
    DeviceAssignmentRepository(db).delete_for_device(device.id)
    DeviceSyncLogRepository(db).delete_for_device(device.id)
    DeviceRepository(db).delete(device)


def get_device_health(db: Session, *, organization_id: uuid.UUID, device_id: uuid.UUID) -> DeviceHealthOut:
    device = get_device(db, organization_id=organization_id, device_id=device_id)
    vendor = _get_vendor(db, device.vendor_id)
    adapter = get_esl_adapter(vendor.code)
    return DeviceHealthOut(**adapter.get_health(device))
