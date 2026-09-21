import math
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.user import User
from app.schemas.common import PaginationMeta
from app.schemas.device import DeviceOut
from app.schemas.esl_integration import (
    AdapterActionResult,
    DiscoverDevicesResult,
    ESLIntegrationCreate,
    ESLIntegrationListParams,
    ESLIntegrationOut,
    ESLIntegrationUpdate,
    ImportDevicesRequest,
    TestPriceUpdateRequest,
)
from app.services import esl_integration_service

router = APIRouter(prefix="/esl-integrations", tags=["esl-integrations"])


@router.get("", response_model=APIResponse[list[ESLIntegrationOut]])
def list_integrations(
    params: ESLIntegrationListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[ESLIntegrationOut]]:
    items, total = esl_integration_service.list_integrations(
        db, organization_id=current_user.organization_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[ESLIntegrationOut.model_validate(i) for i in items], meta=meta.model_dump())


@router.post("", response_model=APIResponse[ESLIntegrationOut], status_code=status.HTTP_201_CREATED)
def create_integration(
    payload: ESLIntegrationCreate,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[ESLIntegrationOut]:
    integration = esl_integration_service.create_integration(
        db, organization_id=current_user.organization_id, payload=payload
    )
    return APIResponse(data=ESLIntegrationOut.model_validate(integration))


@router.get("/{integration_id}", response_model=APIResponse[ESLIntegrationOut])
def get_integration(
    integration_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[ESLIntegrationOut]:
    integration = esl_integration_service.get_integration(
        db, organization_id=current_user.organization_id, integration_id=integration_id
    )
    return APIResponse(data=ESLIntegrationOut.model_validate(integration))


@router.put("/{integration_id}", response_model=APIResponse[ESLIntegrationOut])
def update_integration(
    integration_id: uuid.UUID,
    payload: ESLIntegrationUpdate,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[ESLIntegrationOut]:
    integration = esl_integration_service.update_integration(
        db, organization_id=current_user.organization_id, integration_id=integration_id, payload=payload
    )
    return APIResponse(data=ESLIntegrationOut.model_validate(integration))


@router.delete("/{integration_id}", response_model=APIResponse[dict[str, bool]])
def delete_integration(
    integration_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, bool]]:
    esl_integration_service.delete_integration(
        db, organization_id=current_user.organization_id, integration_id=integration_id
    )
    return APIResponse(data={"deleted": True})


@router.post("/{integration_id}/test-connection", response_model=APIResponse[AdapterActionResult])
async def test_connection(
    integration_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[AdapterActionResult]:
    result = await esl_integration_service.test_connection(
        db, organization_id=current_user.organization_id, integration_id=integration_id
    )
    return APIResponse(data=result)


@router.post("/{integration_id}/discover-devices", response_model=APIResponse[DiscoverDevicesResult])
async def discover_devices(
    integration_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[DiscoverDevicesResult]:
    result = await esl_integration_service.discover_devices(
        db, organization_id=current_user.organization_id, integration_id=integration_id
    )
    return APIResponse(data=result)


@router.post(
    "/{integration_id}/import-devices",
    response_model=APIResponse[list[DeviceOut]],
    status_code=status.HTTP_201_CREATED,
)
def import_devices(
    integration_id: uuid.UUID,
    payload: ImportDevicesRequest,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[list[DeviceOut]]:
    devices = esl_integration_service.import_devices(
        db, organization_id=current_user.organization_id, integration_id=integration_id, payload=payload
    )
    return APIResponse(data=[DeviceOut.model_validate(d) for d in devices])


@router.post("/{integration_id}/test-price-update", response_model=APIResponse[AdapterActionResult])
async def test_price_update(
    integration_id: uuid.UUID,
    payload: TestPriceUpdateRequest,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[AdapterActionResult]:
    result = await esl_integration_service.test_price_update(
        db, organization_id=current_user.organization_id, integration_id=integration_id, payload=payload
    )
    return APIResponse(data=result)


@router.get("/{integration_id}/sync-status", response_model=APIResponse[AdapterActionResult])
async def get_sync_status(
    integration_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[AdapterActionResult]:
    result = await esl_integration_service.get_sync_status(
        db, organization_id=current_user.organization_id, integration_id=integration_id
    )
    return APIResponse(data=result)
