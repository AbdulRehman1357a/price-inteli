import uuid

from sqlalchemy.orm import Session

from app.models.ai_agent import AgentType
from app.models.ai_policy import AIPolicy
from app.repositories.ai_policy_repository import AIPolicyRepository
from app.schemas.ai_policy import AIPolicyUpdate


def get_or_create_policy(db: Session, *, organization_id: uuid.UUID, agent_type: AgentType) -> AIPolicy:
    """Every agent_type effectively has a policy — organizations just haven't
    necessarily saved one yet. Auto-creating the (safe, conservative)
    default on first access means the UI and agent_service always have a
    real row to read/edit rather than needing "does one exist" branching
    everywhere it's used.
    """
    repo = AIPolicyRepository(db)
    policy = repo.get_for_organization_and_type(organization_id, agent_type)
    if policy is not None:
        return policy

    return repo.add(AIPolicy(id=uuid.uuid4(), organization_id=organization_id, agent_type=agent_type))


def list_policies(db: Session, *, organization_id: uuid.UUID) -> list[AIPolicy]:
    return [
        get_or_create_policy(db, organization_id=organization_id, agent_type=agent_type)
        for agent_type in AgentType
    ]


def update_policy(
    db: Session, *, organization_id: uuid.UUID, agent_type: AgentType, payload: AIPolicyUpdate
) -> AIPolicy:
    policy = get_or_create_policy(db, organization_id=organization_id, agent_type=agent_type)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(policy, field, value)
    return AIPolicyRepository(db).add(policy)
