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
from app.schemas.integration import (
    IntegrationCreate,
    IntegrationListParams,
    IntegrationOut,
    IntegrationUpdate,
    TestConnectionResult,
)
from app.schemas.integration_authority import IntegrationAuthorityCreate, IntegrationAuthorityOut
from app.schemas.integration_error import IntegrationErrorListParams, IntegrationErrorOut
from app.schemas.integration_health import IntegrationHealthOut
from app.schemas.integration_location import IntegrationLocationOut, IntegrationLocationUpdate
from app.schemas.integration_mapping import IntegrationMappingCreate, IntegrationMappingOut
from app.schemas.integration_push import IntegrationPricePushRequest
from app.schemas.integration_reconciliation import (
    IntegrationReconciliationListParams,
    IntegrationReconciliationOut,
    IntegrationReconciliationResolveRequest,
    IntegrationReconciliationRunRequest,
)
from app.schemas.integration_sync_job import (
    IntegrationSyncJobListParams,
    IntegrationSyncJobOut,
    IntegrationSyncRequest,
)
from app.schemas.integration_sync_schedule import (
    IntegrationSyncScheduleCreate,
    IntegrationSyncScheduleOut,
    IntegrationSyncScheduleUpdate,
)
from app.schemas.integration_webhook_event import IntegrationWebhookEventOut
from app.services import (
    integration_authority_service,
    integration_error_service,
    integration_location_service,
    integration_mapping_service,
    integration_push_service,
    integration_reconciliation_service,
    integration_schedule_service,
    integration_service,
    integration_sync_service,
    integration_webhook_service,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("", response_model=APIResponse[list[IntegrationOut]])
def list_integrations(
    params: IntegrationListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[IntegrationOut]]:
    items, total = integration_service.list_integrations(
        db, organization_id=current_user.organization_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[integration_service.to_out(i) for i in items], meta=meta.model_dump())


@router.post("", response_model=APIResponse[IntegrationOut], status_code=status.HTTP_201_CREATED)
def create_integration(
    payload: IntegrationCreate,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[IntegrationOut]:
    integration = integration_service.create_integration(
        db, organization_id=current_user.organization_id, payload=payload
    )
    return APIResponse(data=integration_service.to_out(integration))


@router.get("/{integration_id}", response_model=APIResponse[IntegrationOut])
def get_integration(
    integration_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[IntegrationOut]:
    integration = integration_service.get_integration(
        db, organization_id=current_user.organization_id, integration_id=integration_id
    )
    return APIResponse(data=integration_service.to_out(integration))


@router.put("/{integration_id}", response_model=APIResponse[IntegrationOut])
def update_integration(
    integration_id: uuid.UUID,
    payload: IntegrationUpdate,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[IntegrationOut]:
    integration = integration_service.update_integration(
        db, organization_id=current_user.organization_id, integration_id=integration_id, payload=payload
    )
    return APIResponse(data=integration_service.to_out(integration))


@router.post("/{integration_id}/test", response_model=APIResponse[TestConnectionResult])
def test_connection(
    integration_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[TestConnectionResult]:
    result = integration_service.test_connection(
        db, organization_id=current_user.organization_id, integration_id=integration_id
    )
    return APIResponse(data=result)


@router.post(
    "/{integration_id}/sync",
    response_model=APIResponse[IntegrationSyncJobOut],
    status_code=status.HTTP_201_CREATED,
)
def start_sync(
    integration_id: uuid.UUID,
    payload: IntegrationSyncRequest,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[IntegrationSyncJobOut]:
    job = integration_sync_service.create_sync_job(
        db, organization_id=current_user.organization_id, integration_id=integration_id, payload=payload
    )
    return APIResponse(data=IntegrationSyncJobOut.model_validate(job))


@router.get("/{integration_id}/jobs", response_model=APIResponse[list[IntegrationSyncJobOut]])
def list_jobs(
    integration_id: uuid.UUID,
    params: IntegrationSyncJobListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[IntegrationSyncJobOut]]:
    items, total = integration_sync_service.list_jobs(
        db, organization_id=current_user.organization_id, integration_id=integration_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[IntegrationSyncJobOut.model_validate(j) for j in items], meta=meta.model_dump())


@router.post("/{integration_id}/jobs/{job_id}/retry", response_model=APIResponse[IntegrationSyncJobOut])
def retry_job(
    integration_id: uuid.UUID,
    job_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[IntegrationSyncJobOut]:
    del integration_id  # job_id alone is enough to look the job up tenant-scoped
    job = integration_sync_service.retry_job(
        db, organization_id=current_user.organization_id, job_id=job_id
    )
    return APIResponse(data=IntegrationSyncJobOut.model_validate(job))


@router.post(
    "/{integration_id}/mappings",
    response_model=APIResponse[IntegrationMappingOut],
    status_code=status.HTTP_201_CREATED,
)
def create_mapping(
    integration_id: uuid.UUID,
    payload: IntegrationMappingCreate,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[IntegrationMappingOut]:
    mapping = integration_mapping_service.create_mapping(
        db, organization_id=current_user.organization_id, integration_id=integration_id, payload=payload
    )
    return APIResponse(data=IntegrationMappingOut.model_validate(mapping))


@router.get("/{integration_id}/mappings", response_model=APIResponse[list[IntegrationMappingOut]])
def list_mappings(
    integration_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[IntegrationMappingOut]]:
    mappings = integration_mapping_service.list_mappings(
        db, organization_id=current_user.organization_id, integration_id=integration_id
    )
    return APIResponse(data=[IntegrationMappingOut.model_validate(m) for m in mappings])


@router.delete("/{integration_id}/mappings/{mapping_id}", response_model=APIResponse[dict[str, bool]])
def delete_mapping(
    integration_id: uuid.UUID,
    mapping_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, bool]]:
    del integration_id
    integration_mapping_service.delete_mapping(
        db, organization_id=current_user.organization_id, mapping_id=mapping_id
    )
    return APIResponse(data={"deleted": True})


# --- Phase 10 upgrade: locations (multi-location support) ---


@router.get("/{integration_id}/locations", response_model=APIResponse[list[IntegrationLocationOut]])
def list_locations(
    integration_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[IntegrationLocationOut]]:
    locations = integration_location_service.list_locations(
        db, organization_id=current_user.organization_id, integration_id=integration_id
    )
    return APIResponse(data=[IntegrationLocationOut.model_validate(loc) for loc in locations])


@router.post("/{integration_id}/locations/discover", response_model=APIResponse[list[IntegrationLocationOut]])
def discover_locations(
    integration_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[list[IntegrationLocationOut]]:
    locations = integration_location_service.discover_locations(
        db, organization_id=current_user.organization_id, integration_id=integration_id
    )
    return APIResponse(data=[IntegrationLocationOut.model_validate(loc) for loc in locations])


@router.put("/{integration_id}/locations/{location_id}", response_model=APIResponse[IntegrationLocationOut])
def update_location(
    integration_id: uuid.UUID,
    location_id: uuid.UUID,
    payload: IntegrationLocationUpdate,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[IntegrationLocationOut]:
    del integration_id
    location = integration_location_service.update_location(
        db, organization_id=current_user.organization_id, location_id=location_id, payload=payload
    )
    return APIResponse(data=IntegrationLocationOut.model_validate(location))


# --- Phase 10 upgrade: authority (source-of-truth) configuration ---


@router.get("/{integration_id}/authorities", response_model=APIResponse[list[IntegrationAuthorityOut]])
def list_authorities(
    integration_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[IntegrationAuthorityOut]]:
    authorities = integration_authority_service.list_authorities(
        db, organization_id=current_user.organization_id, integration_id=integration_id
    )
    return APIResponse(data=[IntegrationAuthorityOut.model_validate(a) for a in authorities])


@router.post(
    "/{integration_id}/authorities",
    response_model=APIResponse[IntegrationAuthorityOut],
    status_code=status.HTTP_201_CREATED,
)
def create_authority(
    integration_id: uuid.UUID,
    payload: IntegrationAuthorityCreate,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_MANAGE)),
    db: Session = Depends(get_db),
) -> APIResponse[IntegrationAuthorityOut]:
    authority = integration_authority_service.create_authority(
        db, organization_id=current_user.organization_id, integration_id=integration_id, payload=payload
    )
    return APIResponse(data=IntegrationAuthorityOut.model_validate(authority))


@router.delete("/{integration_id}/authorities/{authority_id}", response_model=APIResponse[dict[str, bool]])
def delete_authority(
    integration_id: uuid.UUID,
    authority_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_MANAGE)),
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, bool]]:
    del integration_id
    integration_authority_service.delete_authority(
        db, organization_id=current_user.organization_id, authority_id=authority_id
    )
    return APIResponse(data={"deleted": True})


# --- Phase 10 upgrade: scheduled synchronization ---


@router.get("/{integration_id}/schedules", response_model=APIResponse[list[IntegrationSyncScheduleOut]])
def list_schedules(
    integration_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[IntegrationSyncScheduleOut]]:
    schedules = integration_schedule_service.list_schedules(
        db, organization_id=current_user.organization_id, integration_id=integration_id
    )
    return APIResponse(data=[IntegrationSyncScheduleOut.model_validate(s) for s in schedules])


@router.post(
    "/{integration_id}/schedules",
    response_model=APIResponse[IntegrationSyncScheduleOut],
    status_code=status.HTTP_201_CREATED,
)
def create_schedule(
    integration_id: uuid.UUID,
    payload: IntegrationSyncScheduleCreate,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[IntegrationSyncScheduleOut]:
    schedule = integration_schedule_service.create_schedule(
        db, organization_id=current_user.organization_id, integration_id=integration_id, payload=payload
    )
    return APIResponse(data=IntegrationSyncScheduleOut.model_validate(schedule))


@router.put(
    "/{integration_id}/schedules/{schedule_id}", response_model=APIResponse[IntegrationSyncScheduleOut]
)
def update_schedule(
    integration_id: uuid.UUID,
    schedule_id: uuid.UUID,
    payload: IntegrationSyncScheduleUpdate,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[IntegrationSyncScheduleOut]:
    del integration_id
    schedule = integration_schedule_service.update_schedule(
        db, organization_id=current_user.organization_id, schedule_id=schedule_id, payload=payload
    )
    return APIResponse(data=IntegrationSyncScheduleOut.model_validate(schedule))


# --- Phase 10 upgrade: webhook events (observability only — the actual
# receiver is the unauthenticated app/api/v1/integration_webhooks.py) ---


@router.get("/{integration_id}/webhook-events", response_model=APIResponse[list[IntegrationWebhookEventOut]])
def list_webhook_events(
    integration_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[IntegrationWebhookEventOut]]:
    offset = (page - 1) * page_size
    items, total = integration_webhook_service.list_webhook_events(
        db,
        organization_id=current_user.organization_id,
        integration_id=integration_id,
        offset=offset,
        limit=page_size,
    )
    meta = PaginationMeta(
        page=page, page_size=page_size, total=total, total_pages=math.ceil(total / page_size) if total else 0
    )
    return APIResponse(
        data=[IntegrationWebhookEventOut.model_validate(e) for e in items], meta=meta.model_dump()
    )


@router.post("/{integration_id}/webhook-secret/rotate", response_model=APIResponse[dict[str, str]])
def rotate_webhook_secret(
    integration_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_MANAGE)),
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, str]]:
    integration = integration_service.get_integration(
        db, organization_id=current_user.organization_id, integration_id=integration_id
    )
    secret = integration_webhook_service.rotate_webhook_secret(db, integration=integration)
    return APIResponse(data={"webhook_secret": secret})


# --- Phase 10 upgrade: structured error log ---


@router.get("/{integration_id}/errors", response_model=APIResponse[list[IntegrationErrorOut]])
def list_errors(
    integration_id: uuid.UUID,
    params: IntegrationErrorListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[IntegrationErrorOut]]:
    offset = (params.page - 1) * params.page_size
    items, total = integration_error_service.list_errors(
        db,
        organization_id=current_user.organization_id,
        integration_id=integration_id,
        is_resolved=params.is_resolved,
        offset=offset,
        limit=params.page_size,
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[IntegrationErrorOut.model_validate(e) for e in items], meta=meta.model_dump())


@router.post("/{integration_id}/errors/{error_id}/resolve", response_model=APIResponse[IntegrationErrorOut])
def resolve_error(
    integration_id: uuid.UUID,
    error_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[IntegrationErrorOut]:
    del integration_id
    error = integration_error_service.resolve_error(
        db, organization_id=current_user.organization_id, error_id=error_id, resolved_by=current_user.id
    )
    return APIResponse(data=IntegrationErrorOut.model_validate(error))


# --- Phase 10 upgrade: reconciliation ---


@router.post("/{integration_id}/reconcile", response_model=APIResponse[list[IntegrationReconciliationOut]])
def run_reconciliation(
    integration_id: uuid.UUID,
    payload: IntegrationReconciliationRunRequest,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_RECONCILE)),
    db: Session = Depends(get_db),
) -> APIResponse[list[IntegrationReconciliationOut]]:
    records = integration_reconciliation_service.run_reconciliation(
        db,
        organization_id=current_user.organization_id,
        integration_id=integration_id,
        entity_type=payload.entity_type,
    )
    return APIResponse(data=[IntegrationReconciliationOut.model_validate(r) for r in records])


@router.get(
    "/{integration_id}/reconciliation", response_model=APIResponse[list[IntegrationReconciliationOut]]
)
def list_reconciliation(
    integration_id: uuid.UUID,
    params: IntegrationReconciliationListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[IntegrationReconciliationOut]]:
    offset = (params.page - 1) * params.page_size
    items, total = integration_reconciliation_service.list_reconciliations(
        db,
        organization_id=current_user.organization_id,
        integration_id=integration_id,
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
    return APIResponse(
        data=[IntegrationReconciliationOut.model_validate(r) for r in items], meta=meta.model_dump()
    )


@router.post(
    "/{integration_id}/reconciliation/{recon_id}/resolve",
    response_model=APIResponse[IntegrationReconciliationOut],
)
def resolve_reconciliation(
    integration_id: uuid.UUID,
    recon_id: uuid.UUID,
    payload: IntegrationReconciliationResolveRequest,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_RECONCILE)),
    db: Session = Depends(get_db),
) -> APIResponse[IntegrationReconciliationOut]:
    del integration_id
    record = integration_reconciliation_service.resolve_reconciliation(
        db,
        organization_id=current_user.organization_id,
        reconciliation_id=recon_id,
        resolution=payload.resolution,
        resolved_by=current_user.id,
    )
    return APIResponse(data=IntegrationReconciliationOut.model_validate(record))


# --- Phase 10 upgrade: outbound price execution ---


@router.post(
    "/{integration_id}/push",
    response_model=APIResponse[IntegrationSyncJobOut],
    status_code=status.HTTP_201_CREATED,
)
def push_prices(
    integration_id: uuid.UUID,
    payload: IntegrationPricePushRequest,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[IntegrationSyncJobOut]:
    job = integration_push_service.create_push_job(
        db,
        organization_id=current_user.organization_id,
        integration_id=integration_id,
        price_ids=payload.price_ids,
    )
    return APIResponse(data=IntegrationSyncJobOut.model_validate(job))


# --- Phase 10 upgrade: integration health ---


@router.get("/{integration_id}/health", response_model=APIResponse[IntegrationHealthOut])
def get_health(
    integration_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INTEGRATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[IntegrationHealthOut]:
    health = integration_service.get_health(
        db, organization_id=current_user.organization_id, integration_id=integration_id
    )
    return APIResponse(data=health)
