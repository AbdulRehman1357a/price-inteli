import uuid

from app.services.output_job_service import process_output_job
from app.tasks.celery_app import celery_app


@celery_app.task(name="outputs.process_output_job")
def process_output_job_task(job_id: str) -> None:
    """Thin wrapper — all real logic lives in
    app.services.output_job_service.process_output_job so it can be called
    directly (no Celery/Redis needed) from tests or a management command.
    """
    process_output_job(uuid.UUID(job_id))
