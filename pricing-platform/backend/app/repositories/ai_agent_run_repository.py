import uuid

from sqlalchemy import func, select

from app.models.ai_agent_run import AIAgentRun
from app.repositories.base import BaseRepository


class AIAgentRunRepository(BaseRepository[AIAgentRun]):
    model = AIAgentRun

    def get_by_id_for_organization(self, run_id: uuid.UUID, organization_id: uuid.UUID) -> AIAgentRun | None:
        stmt = select(AIAgentRun).where(
            AIAgentRun.id == run_id, AIAgentRun.organization_id == organization_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        agent_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[AIAgentRun], int]:
        conditions = [AIAgentRun.organization_id == organization_id]
        if agent_id is not None:
            conditions.append(AIAgentRun.agent_id == agent_id)

        base_stmt = select(AIAgentRun).where(*conditions)
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(
                base_stmt.order_by(AIAgentRun.started_at.desc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total
