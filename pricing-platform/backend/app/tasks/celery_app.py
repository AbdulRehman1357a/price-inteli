from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "rpip",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Fail fast instead of retrying/hanging when the broker is unreachable
    # (e.g. local dev without Redis running) — callers like
    # import_service.start_import() catch the resulting exception and
    # leave the job queued for whenever a worker becomes available, rather
    # than blocking the HTTP request that tried to dispatch it.
    broker_connection_timeout=2,
    task_publish_retry=False,
)

# Phase 15 is this codebase's first periodic (Celery beat) job — every
# other task is dispatched inline right after a DB write, never on a
# schedule. Requires a `celery -A app.tasks.celery_app beat` process
# running alongside the worker (see infrastructure/docker-compose.yml's
# celery_beat service); with no beat process, dashboard reads simply fall
# back to computing/caching on demand (see app.services.analytics_service).
celery_app.conf.beat_schedule = {
    "recompute-analytics-daily": {
        "task": "analytics.recompute_all_organizations",
        "schedule": crontab(hour=1, minute=0),
    },
    # Phase 10 upgrade: scans every organization's integration_sync_schedules
    # for due rows (fixed interval_minutes, not cron — see
    # app.models.integration_sync_schedule.IntegrationSyncSchedule) and
    # dispatches a sync job per one, same as a manual "Start Sync" click.
    "dispatch-due-integration-sync-schedules": {
        "task": "integrations.dispatch_due_sync_schedules",
        "schedule": crontab(minute="*/1"),
    },
}

# Long-running work (bulk price recalculation, ERP/POS sync, ESL pushes,
# AI recommendation batches) is registered here as it's added. Do not make
# AI calls inside a database transaction — dispatch a task instead.
celery_app.autodiscover_tasks(["app.tasks"])

# Ensure every task module is imported so Celery sees the tasks even when
# autodiscover fails (can happen on Windows with some pool types).
import app.tasks.analytics  # noqa: E402, F401
import app.tasks.imports  # noqa: E402, F401
import app.tasks.integrations  # noqa: E402, F401
import app.tasks.outputs  # noqa: E402, F401
