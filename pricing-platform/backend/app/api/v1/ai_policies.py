from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.ai_agent import AgentType
from app.models.user import User
from app.schemas.ai_policy import AIPolicyOut, AIPolicyUpdate
from app.services import ai_policy_service

router = APIRouter(prefix="/ai-policies", tags=["ai-agents"])


@router.get("", response_model=APIResponse[list[AIPolicyOut]])
def list_policies(
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[AIPolicyOut]]:
    policies = ai_policy_service.list_policies(db, organization_id=current_user.organization_id)
    return APIResponse(data=[AIPolicyOut.model_validate(p) for p in policies])


@router.put("/{agent_type}", response_model=APIResponse[AIPolicyOut])
def update_policy(
    agent_type: AgentType,
    payload: AIPolicyUpdate,
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_APPLY)),
    db: Session = Depends(get_db),
) -> APIResponse[AIPolicyOut]:
    policy = ai_policy_service.update_policy(
        db, organization_id=current_user.organization_id, agent_type=agent_type, payload=payload
    )
    return APIResponse(data=AIPolicyOut.model_validate(policy))
