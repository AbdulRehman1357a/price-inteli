import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin, utcnow


class TriggerType(enum.StrEnum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"  # not yet produced by any code path — see AIAgent's docstring


class AgentRunStatus(enum.StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AIAgentRun(UUIDPrimaryKeyMixin, Base):
    """One execution of an agent's Observe -> Analyze -> Recommend ->
    Validate -> Request Approval -> Execute if authorized -> Record Result
    pipeline. A single run can evaluate multiple products; output holds one
    entry per candidate (recommendation, guardrail result, action taken,
    execution result) — see app/services/agent_service.py for the exact
    shape, which is what the frontend's run-history detail view renders.

    No separate created_at: started_at is this row's creation marker (set
    when the run begins), matching the literal Phase 12 column list.
    """

    __tablename__ = "ai_agent_runs"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("ai_agents.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    trigger_type: Mapped[TriggerType] = mapped_column(
        Enum(TriggerType, native_enum=False, length=20), nullable=False, default=TriggerType.MANUAL
    )
    input_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[AgentRunStatus] = mapped_column(
        Enum(AgentRunStatus, native_enum=False, length=20),
        nullable=False,
        default=AgentRunStatus.RUNNING,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
