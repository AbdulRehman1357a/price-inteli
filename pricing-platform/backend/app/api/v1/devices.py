import math
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.user import User
from app.repositories.device_sync_log_repository import DeviceSyncLogRepository
from app.schemas.common import PaginationMeta
from app.schemas.device import (
    DeviceCreate,
    DeviceHealthOut,
    DeviceListParams,
    DeviceOut,
    DeviceUpdate,
)
from app.schemas.device_assignment import (
    DeviceAssignmentCreate,
    DeviceAssignmentListParams,
    DeviceAssignmentOut,
)
from app.schemas.device_model import DeviceModelOut
from app.schemas.device_sync_log import DeviceSyncLogListParams, DeviceSyncLogOut
from app.schemas.device_vendor import DeviceVendorOut
from app.services import (
    device_assignment_service,
    device_catalog_service,
    device_service,
    device_sync_service,
)

router = APIRouter(prefix="/devices", tags=["devices"])


# --- Catalog and assignment routes are declared before "/{device_id}" —
# --- Starlette matches routes in registration order, so a literal segment
# --- like "/vendors" must come first or it would be swallowed as a
# --- device_id-shaped path parameter (see app/api/v1/pricing.py for the
# --- same convention).


@router.get("/vendors", response_model=APIResponse[list[DeviceVendorOut]])
def list_vendors(
    current_user: User = Depends(require_permission(PermissionCode.DEVICES_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[DeviceVendorOut]]:
    vendors = device_catalog_service.list_vendors(db)
    return APIResponse(data=[DeviceVendorOut.model_validate(v) for v in vendors])


@router.get("/models", response_model=APIResponse[list[DeviceModelOut]])
def list_models(
    vendor_id: uuid.UUID | None = None,
    current_user: User = Depends(require_permission(PermissionCode.DEVICES_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[DeviceModelOut]]:
    models = device_catalog_service.list_models(db, vendor_id=vendor_id)
    return APIResponse(data=[DeviceModelOut.model_validate(m) for m in models])


@router.get("/assignments", response_model=APIResponse[list[DeviceAssignmentOut]])
def list_assignments(
    params: DeviceAssignmentListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.DEVICES_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[DeviceAssignmentOut]]:
    items, total = device_assignment_service.list_assignments(
        db, organization_id=current_user.organization_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[DeviceAssignmentOut.model_validate(a) for a in items], meta=meta.model_dump())


@router.post(
    "/assignments", response_model=APIResponse[DeviceAssignmentOut], status_code=status.HTTP_201_CREATED
)
def create_assignment(
    payload: DeviceAssignmentCreate,
    current_user: User = Depends(require_permission(PermissionCode.DEVICES_MANAGE)),
    db: Session = Depends(get_db),
) -> APIResponse[DeviceAssignmentOut]:
    assignment = device_assignment_service.create_assignment(
        db, organization_id=current_user.organization_id, payload=payload
    )
    return APIResponse(data=DeviceAssignmentOut.model_validate(assignment))


@router.post("/assignments/{assignment_id}/unassign", response_model=APIResponse[DeviceAssignmentOut])
def unassign_device(
    assignment_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.DEVICES_MANAGE)),
    db: Session = Depends(get_db),
) -> APIResponse[DeviceAssignmentOut]:
    assignment = device_assignment_service.unassign(
        db, organization_id=current_user.organization_id, assignment_id=assignment_id
    )
    return APIResponse(data=DeviceAssignmentOut.model_validate(assignment))


@router.get("", response_model=APIResponse[list[DeviceOut]])
def list_devices(
    params: DeviceListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.DEVICES_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[DeviceOut]]:
    items, total = device_service.list_devices(
        db, organization_id=current_user.organization_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[DeviceOut.model_validate(d) for d in items], meta=meta.model_dump())


@router.post("", response_model=APIResponse[DeviceOut], status_code=status.HTTP_201_CREATED)
def create_device(
    payload: DeviceCreate,
    current_user: User = Depends(require_permission(PermissionCode.DEVICES_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[DeviceOut]:
    device = device_service.create_device(db, organization_id=current_user.organization_id, payload=payload)
    return APIResponse(data=DeviceOut.model_validate(device))


@router.get("/{device_id}", response_model=APIResponse[DeviceOut])
def get_device(
    device_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.DEVICES_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[DeviceOut]:
    device = device_service.get_device(db, organization_id=current_user.organization_id, device_id=device_id)
    return APIResponse(data=DeviceOut.model_validate(device))


@router.put("/{device_id}", response_model=APIResponse[DeviceOut])
def update_device(
    device_id: uuid.UUID,
    payload: DeviceUpdate,
    current_user: User = Depends(require_permission(PermissionCode.DEVICES_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[DeviceOut]:
    device = device_service.update_device(
        db, organization_id=current_user.organization_id, device_id=device_id, payload=payload
    )
    return APIResponse(data=DeviceOut.model_validate(device))


@router.delete("/{device_id}", response_model=APIResponse[dict[str, bool]])
def delete_device(
    device_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.DEVICES_MANAGE)),
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, bool]]:
    device_service.delete_device(db, organization_id=current_user.organization_id, device_id=device_id)
    return APIResponse(data={"deleted": True})


@router.get("/{device_id}/health", response_model=APIResponse[DeviceHealthOut])
def get_device_health(
    device_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.DEVICES_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[DeviceHealthOut]:
    health = device_service.get_device_health(
        db, organization_id=current_user.organization_id, device_id=device_id
    )
    return APIResponse(data=health)


@router.get("/{device_id}/assignment", response_model=APIResponse[DeviceAssignmentOut | None])
def get_active_assignment(
    device_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.DEVICES_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[DeviceAssignmentOut | None]:
    assignment = device_assignment_service.get_active_assignment(
        db, organization_id=current_user.organization_id, device_id=device_id
    )
    return APIResponse(data=DeviceAssignmentOut.model_validate(assignment) if assignment else None)


@router.post("/{device_id}/sync", response_model=APIResponse[DeviceSyncLogOut])
def sync_device(
    device_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.DEVICES_MANAGE)),
    db: Session = Depends(get_db),
) -> APIResponse[DeviceSyncLogOut]:
    log = device_sync_service.sync_device(
        db, organization_id=current_user.organization_id, device_id=device_id
    )
    return APIResponse(data=DeviceSyncLogOut.model_validate(log))


@router.get("/{device_id}/sync-logs", response_model=APIResponse[list[DeviceSyncLogOut]])
def list_sync_logs(
    device_id: uuid.UUID,
    params: DeviceSyncLogListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.DEVICES_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[DeviceSyncLogOut]]:
    device_service.get_device(db, organization_id=current_user.organization_id, device_id=device_id)
    offset = (params.page - 1) * params.page_size
    items, total = DeviceSyncLogRepository(db).search_for_device(
        device_id=device_id,
        organization_id=current_user.organization_id,
        status=params.status,
        offset=offset,
        limit=params.page_size,
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[DeviceSyncLogOut.model_validate(log) for log in items], meta=meta.model_dump())
