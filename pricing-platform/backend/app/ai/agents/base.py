import uuid
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from app.models.ai_agent import AgentType, AIAgent
from app.models.ai_policy import AIPolicy


class Agent(ABC):
    """Rule: every agent follows Observe -> Analyze -> Recommend -> Validate
    -> Request Approval -> Execute if authorized -> Record Result. Concrete
    agents implement that whole pipeline inside run() and return the JSON
    to store on AIAgentRun.output — app.services.agent_service owns
    creating/finalizing the AIAgentRun row itself (started_at/completed_at/
    status/error_message), so an agent only needs to produce output or
    raise.
    """

    agent_type: AgentType

    @abstractmethod
    def run(
        self, db: Session, *, organization_id: uuid.UUID, agent: AIAgent, policy: AIPolicy
    ) -> dict[str, Any]: ...
