import uuid

from sqlalchemy import select

from app.models.ai_agent import AIAgent
from app.repositories.base import BaseRepository


class AIAgentRepository(BaseRepository[AIAgent]):
    model = AIAgent

    def get_by_id_for_organization(self, agent_id: uuid.UUID, organization_id: uuid.UUID) -> AIAgent | None:
        stmt = select(AIAgent).where(AIAgent.id == agent_id, AIAgent.organization_id == organization_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_organization(self, organization_id: uuid.UUID) -> list[AIAgent]:
        stmt = select(AIAgent).where(AIAgent.organization_id == organization_id).order_by(AIAgent.name)
        return list(self.db.execute(stmt).scalars().all())

    def delete(self, agent: AIAgent) -> None:
        """Hard delete — no SoftDeleteMixin on this table (not in the Phase
        12 spec), same precedent as Category.
        """
        self.db.delete(agent)
        self.db.flush()
