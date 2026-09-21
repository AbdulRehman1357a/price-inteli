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
from app.schemas.output_channel import (
    OutputChannelCreate,
    OutputChannelListParams,
    OutputChannelOut,
    OutputChannelUpdate,
)
from app.schemas.output_job import (
    OutputJobBulkCreate,
    OutputJobCreate,
    OutputJobDashboardSummary,
    OutputJobListParams,
    OutputJobOut,
)
from app.schemas.output_routing_rule import (
    OutputRoutingRuleCreate,
    OutputRoutingRuleListParams,
    OutputRoutingRuleOut,
    OutputRoutingRuleUpdate,
)
from app.services import output_channel_service, output_job_service, output_routing_rule_service

router = APIRouter(prefix="/outputs", tags=["outputs"])


@router.get("/channels", response_model=APIResponse[list[OutputChannelOut]])
def list_channels(
    params: OutputChannelListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[OutputChannelOut]]:
    items, total = output_channel_service.list_channels(
        db, organization_id=current_user.organization_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[OutputChannelOut.model_validate(c) for c in items], meta=meta.model_dump())


@router.post("/channels", response_model=APIResponse[OutputChannelOut], status_code=status.HTTP_201_CREATED)
def create_channel(
    payload: OutputChannelCreate,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[OutputChannelOut]:
    channel = output_channel_service.create_channel(
        db, organization_id=current_user.organization_id, payload=payload
    )
    return APIResponse(data=OutputChannelOut.model_validate(channel))


@router.get("/channels/{channel_id}", response_model=APIResponse[OutputChannelOut])
def get_channel(
    channel_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[OutputChannelOut]:
    channel = output_channel_service.get_channel(
        db, organization_id=current_user.organization_id, channel_id=channel_id
    )
    return APIResponse(data=OutputChannelOut.model_validate(channel))


@router.put("/channels/{channel_id}", response_model=APIResponse[OutputChannelOut])
def update_channel(
    channel_id: uuid.UUID,
    payload: OutputChannelUpdate,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[OutputChannelOut]:
    channel = output_channel_service.update_channel(
        db, organization_id=current_user.organization_id, channel_id=channel_id, payload=payload
    )
    return APIResponse(data=OutputChannelOut.model_validate(channel))


@router.get("/jobs", response_model=APIResponse[list[OutputJobOut]])
def list_jobs(
    params: OutputJobListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[OutputJobOut]]:
    items, total = output_job_service.list_jobs(
        db, organization_id=current_user.organization_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[OutputJobOut.model_validate(j) for j in items], meta=meta.model_dump())


@router.post("/jobs", response_model=APIResponse[OutputJobOut], status_code=status.HTTP_201_CREATED)
def create_job(
    payload: OutputJobCreate,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_MANAGE)),
    db: Session = Depends(get_db),
) -> APIResponse[OutputJobOut]:
    job = output_job_service.create_job(db, organization_id=current_user.organization_id, payload=payload)
    return APIResponse(data=OutputJobOut.model_validate(job))


@router.post(
    "/jobs/bulk", response_model=APIResponse[list[OutputJobOut]], status_code=status.HTTP_201_CREATED
)
def create_jobs_bulk(
    payload: OutputJobBulkCreate,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_MANAGE)),
    db: Session = Depends(get_db),
) -> APIResponse[list[OutputJobOut]]:
    jobs = output_job_service.create_bulk_jobs(
        db, organization_id=current_user.organization_id, payload=payload
    )
    return APIResponse(data=[OutputJobOut.model_validate(j) for j in jobs])


@router.get("/jobs/summary", response_model=APIResponse[OutputJobDashboardSummary])
def get_jobs_summary(
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[OutputJobDashboardSummary]:
    """Registered before /jobs/{job_id} — "summary" would otherwise be
    swallowed by that parameterized route and fail UUID parsing.
    """
    summary = output_job_service.get_dashboard_summary(db, organization_id=current_user.organization_id)
    return APIResponse(data=summary)


@router.get("/jobs/{job_id}", response_model=APIResponse[OutputJobOut])
def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[OutputJobOut]:
    job = output_job_service.get_job(db, organization_id=current_user.organization_id, job_id=job_id)
    return APIResponse(data=OutputJobOut.model_validate(job))


@router.post("/jobs/{job_id}/retry", response_model=APIResponse[OutputJobOut])
def retry_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_MANAGE)),
    db: Session = Depends(get_db),
) -> APIResponse[OutputJobOut]:
    job = output_job_service.retry_job(db, organization_id=current_user.organization_id, job_id=job_id)
    return APIResponse(data=OutputJobOut.model_validate(job))


@router.post("/jobs/{job_id}/cancel", response_model=APIResponse[OutputJobOut])
def cancel_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_MANAGE)),
    db: Session = Depends(get_db),
) -> APIResponse[OutputJobOut]:
    job = output_job_service.cancel_job(db, organization_id=current_user.organization_id, job_id=job_id)
    return APIResponse(data=OutputJobOut.model_validate(job))


@router.get("/routing-rules", response_model=APIResponse[list[OutputRoutingRuleOut]])
def list_routing_rules(
    params: OutputRoutingRuleListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[OutputRoutingRuleOut]]:
    items, total = output_routing_rule_service.list_rules(
        db, organization_id=current_user.organization_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(
        data=[OutputRoutingRuleOut.model_validate(r) for r in items], meta=meta.model_dump()
    )


@router.post(
    "/routing-rules", response_model=APIResponse[OutputRoutingRuleOut], status_code=status.HTTP_201_CREATED
)
def create_routing_rule(
    payload: OutputRoutingRuleCreate,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[OutputRoutingRuleOut]:
    rule = output_routing_rule_service.create_rule(
        db, organization_id=current_user.organization_id, payload=payload
    )
    return APIResponse(data=OutputRoutingRuleOut.model_validate(rule))


@router.get("/routing-rules/{rule_id}", response_model=APIResponse[OutputRoutingRuleOut])
def get_routing_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[OutputRoutingRuleOut]:
    rule = output_routing_rule_service.get_rule(
        db, organization_id=current_user.organization_id, rule_id=rule_id
    )
    return APIResponse(data=OutputRoutingRuleOut.model_validate(rule))


@router.put("/routing-rules/{rule_id}", response_model=APIResponse[OutputRoutingRuleOut])
def update_routing_rule(
    rule_id: uuid.UUID,
    payload: OutputRoutingRuleUpdate,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[OutputRoutingRuleOut]:
    rule = output_routing_rule_service.update_rule(
        db, organization_id=current_user.organization_id, rule_id=rule_id, payload=payload
    )
    return APIResponse(data=OutputRoutingRuleOut.model_validate(rule))
