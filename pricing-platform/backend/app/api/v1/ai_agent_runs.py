import math
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.user import User
from app.schemas.ai_agent import AgentRunListParams, AgentRunOut
from app.schemas.common import PaginationMeta
from app.services import agent_service

router = APIRouter(prefix="/ai-agent-runs", tags=["ai-agents"])


@router.get("", response_model=APIResponse[list[AgentRunOut]])
def list_runs(
    agent_id: uuid.UUID | None = None,
    params: AgentRunListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[AgentRunOut]]:
    items, total = agent_service.list_runs(
        db, organization_id=current_user.organization_id, agent_id=agent_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[AgentRunOut.model_validate(r) for r in items], meta=meta.model_dump())


@router.get("/{run_id}", response_model=APIResponse[AgentRunOut])
def get_run(
    run_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[AgentRunOut]:
    run = agent_service.get_run(db, organization_id=current_user.organization_id, run_id=run_id)
    return APIResponse(data=AgentRunOut.model_validate(run))
