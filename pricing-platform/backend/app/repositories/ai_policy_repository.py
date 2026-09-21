import uuid

from sqlalchemy import select

from app.models.ai_agent import AgentType
from app.models.ai_policy import AIPolicy
from app.repositories.base import BaseRepository


class AIPolicyRepository(BaseRepository[AIPolicy]):
    model = AIPolicy

    def get_for_organization_and_type(
        self, organization_id: uuid.UUID, agent_type: AgentType
    ) -> AIPolicy | None:
        stmt = select(AIPolicy).where(
            AIPolicy.organization_id == organization_id, AIPolicy.agent_type == agent_type
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_organization(self, organization_id: uuid.UUID) -> list[AIPolicy]:
        stmt = select(AIPolicy).where(AIPolicy.organization_id == organization_id)
        return list(self.db.execute(stmt).scalars().all())
