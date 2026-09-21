import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.user import User
from app.schemas.ai_agent import AgentCreate, AgentOut, AgentRunOut, AgentUpdate
from app.services import agent_service

router = APIRouter(prefix="/ai-agents", tags=["ai-agents"])


@router.post("", response_model=APIResponse[AgentOut], status_code=status.HTTP_201_CREATED)
def create_agent(
    payload: AgentCreate,
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_APPLY)),
    db: Session = Depends(get_db),
) -> APIResponse[AgentOut]:
    agent = agent_service.create_agent(db, organization_id=current_user.organization_id, payload=payload)
    return APIResponse(data=AgentOut.model_validate(agent))


@router.get("", response_model=APIResponse[list[AgentOut]])
def list_agents(
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[AgentOut]]:
    agents = agent_service.list_agents(db, organization_id=current_user.organization_id)
    return APIResponse(data=[AgentOut.model_validate(a) for a in agents])


@router.get("/{agent_id}", response_model=APIResponse[AgentOut])
def get_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[AgentOut]:
    agent = agent_service.get_agent(db, organization_id=current_user.organization_id, agent_id=agent_id)
    return APIResponse(data=AgentOut.model_validate(agent))


@router.put("/{agent_id}", response_model=APIResponse[AgentOut])
def update_agent(
    agent_id: uuid.UUID,
    payload: AgentUpdate,
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_APPLY)),
    db: Session = Depends(get_db),
) -> APIResponse[AgentOut]:
    agent = agent_service.update_agent(
        db, organization_id=current_user.organization_id, agent_id=agent_id, payload=payload
    )
    return APIResponse(data=AgentOut.model_validate(agent))


@router.delete("/{agent_id}", response_model=APIResponse[dict[str, bool]])
def delete_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_APPLY)),
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, bool]]:
    agent_service.delete_agent(db, organization_id=current_user.organization_id, agent_id=agent_id)
    return APIResponse(data={"deleted": True})


@router.post("/{agent_id}/run", response_model=APIResponse[AgentRunOut], status_code=status.HTTP_201_CREATED)
def run_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[AgentRunOut]:
    run = agent_service.trigger_run(db, organization_id=current_user.organization_id, agent_id=agent_id)
    return APIResponse(data=AgentRunOut.model_validate(run))
