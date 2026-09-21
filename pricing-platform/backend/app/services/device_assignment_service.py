import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.integrations.registry import get_esl_adapter
from app.models.device_assignment import DeviceAssignment, DeviceAssignmentStatus
from app.models.mixins import utcnow
from app.repositories.device_assignment_repository import DeviceAssignmentRepository
from app.repositories.device_vendor_repository import DeviceVendorRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.device_assignment import DeviceAssignmentCreate, DeviceAssignmentListParams
from app.services import device_service, device_sync_service


def create_assignment(
    db: Session, *, organization_id: uuid.UUID, payload: DeviceAssignmentCreate
) -> DeviceAssignment:
    device = device_service.get_device(db, organization_id=organization_id, device_id=payload.device_id)
    if device.store_id != payload.store_id:
        raise ConflictError(
            "The selected store does not match this device's store.", code="device_store_mismatch"
        )
    product = ProductRepository(db).get_by_id_for_organization(payload.product_id, organization_id)
    if product is None:
        raise NotFoundError("Product not found.", code="product_not_found")

    assignment_repo = DeviceAssignmentRepository(db)
    existing = assignment_repo.get_active_for_device(device.id)
    if existing is not None:
        existing.status = DeviceAssignmentStatus.ENDED
        existing.unassigned_at = utcnow()
        assignment_repo.add(existing)

    assignment = assignment_repo.add(
        DeviceAssignment(
            id=uuid.uuid4(),
            device_id=device.id,
            product_id=product.id,
            store_id=payload.store_id,
            status=DeviceAssignmentStatus.ACTIVE,
        )
    )

    vendor = DeviceVendorRepository(db).get_by_id(device.vendor_id)
    get_esl_adapter(vendor.code).assign_product(device, product)
    device_sync_service.sync_device(
        db, organization_id=organization_id, device_id=device.id, product_id=product.id
    )

    return assignment


def get_active_assignment(
    db: Session, *, organization_id: uuid.UUID, device_id: uuid.UUID
) -> DeviceAssignment | None:
    device_service.get_device(db, organization_id=organization_id, device_id=device_id)  # tenant check
    return DeviceAssignmentRepository(db).get_active_for_device(device_id)


def list_assignments(
    db: Session, *, organization_id: uuid.UUID, params: DeviceAssignmentListParams
) -> tuple[list[DeviceAssignment], int]:
    offset = (params.page - 1) * params.page_size
    return DeviceAssignmentRepository(db).search(
        organization_id,
        device_id=params.device_id,
        status=params.status,
        offset=offset,
        limit=params.page_size,
    )


def unassign(db: Session, *, organization_id: uuid.UUID, assignment_id: uuid.UUID) -> DeviceAssignment:
    assignment_repo = DeviceAssignmentRepository(db)
    assignment = assignment_repo.get_by_id_for_organization(assignment_id, organization_id)
    if assignment is None:
        raise NotFoundError("Device assignment not found.", code="device_assignment_not_found")
    if assignment.status != DeviceAssignmentStatus.ACTIVE:
        raise ConflictError("This assignment has already ended.", code="device_assignment_already_ended")

    assignment.status = DeviceAssignmentStatus.ENDED
    assignment.unassigned_at = utcnow()
    assignment_repo.add(assignment)

    device = device_service.get_device(db, organization_id=organization_id, device_id=assignment.device_id)
    vendor = DeviceVendorRepository(db).get_by_id(device.vendor_id)
    get_esl_adapter(vendor.code).unassign_product(device)

    return assignment
