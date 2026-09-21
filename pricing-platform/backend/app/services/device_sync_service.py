import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.integrations.base import ESLSyncContext
from app.integrations.registry import get_esl_adapter
from app.models.device_sync_log import DeviceSyncLog, DeviceSyncStatus
from app.models.mixins import utcnow
from app.repositories.device_assignment_repository import DeviceAssignmentRepository
from app.repositories.device_repository import DeviceRepository
from app.repositories.device_sync_log_repository import DeviceSyncLogRepository
from app.repositories.device_vendor_repository import DeviceVendorRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository
from app.services import device_service, output_job_service


def sync_device(
    db: Session,
    *,
    organization_id: uuid.UUID,
    device_id: uuid.UUID,
    product_id: uuid.UUID | None = None,
    output_job_id: uuid.UUID | None = None,
) -> DeviceSyncLog:
    """The "Pricing Engine -> Output Job -> ESL Adapter -> MQTT -> ESL
    Simulator -> Acknowledgement" flow for one device. Called for a manual
    "Resync" action (product_id=None resolves the device's current active
    assignment) and automatically right after a new assignment is created
    (app.services.device_assignment_service.create_assignment).
    """
    device = device_service.get_device(db, organization_id=organization_id, device_id=device_id)

    if product_id is None:
        assignment = DeviceAssignmentRepository(db).get_active_for_device(device_id)
        if assignment is None:
            raise ConflictError(
                "This device has no assigned product to sync.", code="device_no_assignment"
            )
        product_id = assignment.product_id

    product = ProductRepository(db).get_by_id_for_organization(product_id, organization_id)
    if product is None:
        raise NotFoundError("Product not found.", code="product_not_found")

    log = DeviceSyncLogRepository(db).add(
        DeviceSyncLog(
            id=uuid.uuid4(),
            device_id=device.id,
            product_id=product.id,
            output_job_id=output_job_id,
            status=DeviceSyncStatus.PENDING,
        )
    )

    try:
        price, currency = output_job_service.resolve_display_price(
            db, organization_id=organization_id, product=product, store_id=device.store_id
        )
        store = StoreRepository(db).get_by_id(device.store_id)
        vendor = DeviceVendorRepository(db).get_by_id(device.vendor_id)
        adapter = get_esl_adapter(vendor.code)
        context = ESLSyncContext(
            device=device,
            product=product,
            price=price,
            currency=currency,
            store_name=store.name if store else None,
        )
        result = adapter.sync_device(context)

        now = utcnow()
        device.last_seen_at = now
        if result.success:
            device.last_sync_at = now
        for field in ("battery_level", "signal_strength", "firmware_version"):
            if field in result.device_status:
                setattr(device, field, result.device_status[field])
        DeviceRepository(db).add(device)

        log.status = DeviceSyncStatus.SUCCESS if result.success else DeviceSyncStatus.FAILED
        log.error_message = None if result.success else result.message
        log.completed_at = now
    except Exception as exc:  # noqa: BLE001 — isolate failures to this one sync attempt
        log.status = DeviceSyncStatus.FAILED
        log.error_message = str(exc)
        log.completed_at = utcnow()

    return DeviceSyncLogRepository(db).add(log)
