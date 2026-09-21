import logging
import socket
import uuid
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.ai.agents import registry as agent_registry
from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError
from app.db.session import SessionLocal
from app.models.ai_agent import AgentStatus, AIAgent
from app.models.ai_agent_run import AgentRunStatus, AIAgentRun, TriggerType
from app.models.mixins import utcnow
from app.repositories.ai_agent_repository import AIAgentRepository
from app.repositories.ai_agent_run_repository import AIAgentRunRepository
from app.schemas.ai_agent import AgentCreate, AgentRunListParams, AgentUpdate
from app.services import ai_policy_service

logger = logging.getLogger(__name__)


def create_agent(db: Session, *, organization_id: uuid.UUID, payload: AgentCreate) -> AIAgent:
    agent = AIAgent(
        id=uuid.uuid4(),
        organization_id=organization_id,
        agent_type=payload.agent_type,
        name=payload.name,
        status=payload.status,
        configuration=payload.configuration.model_dump(mode="json"),
    )
    return AIAgentRepository(db).add(agent)


def get_agent(db: Session, *, organization_id: uuid.UUID, agent_id: uuid.UUID) -> AIAgent:
    agent = AIAgentRepository(db).get_by_id_for_organization(agent_id, organization_id)
    if agent is None:
        raise NotFoundError("Agent not found.", code="agent_not_found")
    return agent


def list_agents(db: Session, *, organization_id: uuid.UUID) -> list[AIAgent]:
    return AIAgentRepository(db).list_for_organization(organization_id)


def update_agent(
    db: Session, *, organization_id: uuid.UUID, agent_id: uuid.UUID, payload: AgentUpdate
) -> AIAgent:
    agent = get_agent(db, organization_id=organization_id, agent_id=agent_id)
    updates = payload.model_dump(exclude_unset=True)
    if "configuration" in updates and updates["configuration"] is not None:
        updates["configuration"] = payload.configuration.model_dump(mode="json")
    for field, value in updates.items():
        setattr(agent, field, value)
    return AIAgentRepository(db).add(agent)


def delete_agent(db: Session, *, organization_id: uuid.UUID, agent_id: uuid.UUID) -> None:
    """Blocks deletion once the agent has run history — same precedent as
    CategoryService.delete blocking a category with subcategories/products
    — rather than cascading and destroying the audit trail, or leaving
    orphaned ai_agent_runs rows behind. Deactivate (status=inactive) via
    update_agent instead once an agent has actually been run.
    """
    agent = get_agent(db, organization_id=organization_id, agent_id=agent_id)
    _, run_count = AIAgentRunRepository(db).search(organization_id, agent_id=agent.id, limit=1)
    if run_count > 0:
        raise ConflictError(
            "This agent has run history and can't be deleted — set it to inactive instead.",
            code="agent_has_runs",
        )
    AIAgentRepository(db).delete(agent)


def trigger_run(
    db: Session,
    *,
    organization_id: uuid.UUID,
    agent_id: uuid.UUID,
    trigger_type: TriggerType = TriggerType.MANUAL,
) -> AIAgentRun:
    agent = get_agent(db, organization_id=organization_id, agent_id=agent_id)
    if agent.status != AgentStatus.ACTIVE:
        raise ConflictError("This agent is inactive.", code="agent_inactive")

    policy = ai_policy_service.get_or_create_policy(
        db, organization_id=organization_id, agent_type=agent.agent_type
    )

    run = AIAgentRun(
        id=uuid.uuid4(),
        agent_id=agent.id,
        organization_id=organization_id,
        trigger_type=trigger_type,
        input_snapshot={
            "agent_configuration": agent.configuration,
            "policy": {
                "mode": policy.mode.value,
                "min_confidence": str(policy.min_confidence),
                "max_price_change_percent": str(policy.max_price_change_percent),
                "min_margin_percent": str(policy.min_margin_percent),
                "approval_required": policy.approval_required,
                "auto_execute": policy.auto_execute,
            },
        },
        status=AgentRunStatus.RUNNING,
        started_at=utcnow(),
    )
    run = AIAgentRunRepository(db).add(run)
    _dispatch(run.id)
    return run


def _dispatch(run_id: uuid.UUID) -> None:
    if _broker_reachable():
        try:
            from app.tasks.agents import process_agent_run_task

            process_agent_run_task.delay(str(run_id))
        except Exception:  # noqa: BLE001 — broker went away between the check and the dispatch
            logger.warning("Could not dispatch agent run %s to Celery.", run_id)
    else:
        logger.warning(
            "Redis broker unreachable — agent run %s will stay running until a worker is available.",
            run_id,
        )


def _broker_reachable(timeout: float = 0.5) -> bool:
    """Same quick TCP pre-check as app.services.import_service / output_job_service."""
    url = urlparse(get_settings().redis_url)
    try:
        with socket.create_connection((url.hostname or "localhost", url.port or 6379), timeout=timeout):
            return True
    except OSError:
        return False


def get_run(db: Session, *, organization_id: uuid.UUID, run_id: uuid.UUID) -> AIAgentRun:
    run = AIAgentRunRepository(db).get_by_id_for_organization(run_id, organization_id)
    if run is None:
        raise NotFoundError("Agent run not found.", code="agent_run_not_found")
    return run


def list_runs(
    db: Session,
    *,
    organization_id: uuid.UUID,
    agent_id: uuid.UUID | None,
    params: AgentRunListParams,
) -> tuple[list[AIAgentRun], int]:
    offset = (params.page - 1) * params.page_size
    return AIAgentRunRepository(db).search(
        organization_id, agent_id=agent_id, offset=offset, limit=params.page_size
    )


def process_agent_run(run_id: uuid.UUID, db: Session | None = None) -> None:
    """The worker logic. In production the thin Celery task
    (app/tasks/agents.py) calls this with no session, so it opens and
    manages its own — mirrors app.services.import_service.process_import_job
    and app.services.output_job_service.process_output_job. Running the
    agent's full Observe..Record Result pipeline here (not inline in the
    triggering HTTP request) is why POST /ai-agents/{id}/run returns
    immediately with status=running rather than blocking: "Do not make AI
    calls inside a database transaction."
    """
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    try:
        _run(session, run_id)
    finally:
        if owns_session:
            session.close()


def _run(db: Session, run_id: uuid.UUID) -> None:
    run_repo = AIAgentRunRepository(db)
    run = run_repo.get_by_id(run_id)
    if run is None:
        logger.error("process_agent_run: run %s not found", run_id)
        return
    if run.status != AgentRunStatus.RUNNING:
        logger.warning("process_agent_run: run %s has status %s, skipping", run_id, run.status)
        return

    agent = AIAgentRepository(db).get_by_id(run.agent_id)
    if agent is None:
        run.status = AgentRunStatus.FAILED
        run.error_message = "The agent this run belongs to no longer exists."
        run.completed_at = utcnow()
        run_repo.add(run)
        db.commit()
        return

    policy = ai_policy_service.get_or_create_policy(
        db, organization_id=run.organization_id, agent_type=agent.agent_type
    )

    try:
        implementation = agent_registry.get_agent(agent.agent_type)
        output = implementation.run(db, organization_id=run.organization_id, agent=agent, policy=policy)
        run.output = output
        run.status = AgentRunStatus.COMPLETED
        run.error_message = None
    except Exception as exc:  # noqa: BLE001 — record the failure on the run rather than crashing the worker
        logger.exception("agent run %s failed", run_id)
        run.status = AgentRunStatus.FAILED
        run.error_message = str(exc)

    run.completed_at = utcnow()
    run_repo.add(run)
    db.commit()
