import uuid

from app.services.import_service import process_import_job
from app.tasks.celery_app import celery_app


@celery_app.task(name="imports.process_import_job")
def process_import_job_task(job_id: str) -> None:
    """Thin wrapper — all real logic lives in
    app.services.import_service.process_import_job so it can be called
    directly (no Celery/Redis needed) from tests or a management command.
    """
    process_import_job(uuid.UUID(job_id))
