import uuid

from app.services.integration_push_service import process_push_job
from app.services.integration_schedule_service import dispatch_due_schedules
from app.services.integration_sync_service import process_sync_job
from app.services.integration_webhook_service import process_webhook_event
from app.tasks.celery_app import celery_app


@celery_app.task(name="integrations.process_sync_job")
def process_sync_job_task(job_id: str) -> None:
    """Thin wrapper — all real logic lives in
    app.services.integration_sync_service.process_sync_job so it can be
    called directly (no Celery/Redis needed) from tests or a management
    command.
    """
    process_sync_job(uuid.UUID(job_id))


@celery_app.task(name="integrations.process_webhook_event")
def process_webhook_event_task(event_id: str) -> None:
    """Thin wrapper around app.services.integration_webhook_service.process_webhook_event —
    dispatched by the unauthenticated webhook receiver
    (app/api/v1/integration_webhooks.py) after signature verification and
    idempotency dedup, so the actual sync work happens off the request
    path (spec section 18: "webhook processing must be asynchronous").
    """
    process_webhook_event(uuid.UUID(event_id))


@celery_app.task(name="integrations.dispatch_due_sync_schedules")
def dispatch_due_sync_schedules_task() -> None:
    """Runs every minute via Celery Beat (see app/tasks/celery_app.py's
    beat_schedule) — scans every organization's integration_sync_schedules
    for due rows and dispatches a sync job per one.
    """
    dispatch_due_schedules()


@celery_app.task(name="integrations.process_push_job")
def process_push_job_task(job_id: str) -> None:
    """Thin wrapper around app.services.integration_push_service.process_push_job —
    the outbound (PIP -> External) execution counterpart to process_sync_job_task."""
    process_push_job(uuid.UUID(job_id))
