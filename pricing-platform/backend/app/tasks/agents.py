import uuid

from app.services.agent_service import process_agent_run
from app.tasks.celery_app import celery_app


@celery_app.task(name="agents.process_agent_run")
def process_agent_run_task(run_id: str) -> None:
    """Thin wrapper — all real logic lives in
    app.services.agent_service.process_agent_run so it can be called
    directly (no Celery/Redis needed) from tests or a management command.
    """
    process_agent_run(uuid.UUID(run_id))
