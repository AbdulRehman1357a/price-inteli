import datetime as dt
import uuid

from app.services import analytics_service
from app.tasks.celery_app import celery_app


@celery_app.task(name="analytics.recompute_dashboard_snapshot")
def recompute_analytics_task(organization_id: str, start_date: str, end_date: str) -> None:
    """Thin wrapper — all real logic lives in
    app.services.analytics_service.recompute_range so it can be called
    directly (no Celery/Redis needed) from tests. Dispatched by
    analytics_service._dispatch_recompute when a dashboard request's
    requested range has too many not-yet-computed days to fill in inline.
    """
    analytics_service.recompute_range(
        uuid.UUID(organization_id),
        start_date=dt.date.fromisoformat(start_date),
        end_date=dt.date.fromisoformat(end_date),
    )


@celery_app.task(name="analytics.recompute_all_organizations")
def recompute_all_organizations_task() -> None:
    """The Celery beat periodic entry point — see celery_app.py's
    beat_schedule. Re-touches the last few days for every active
    organization so snapshot rows catch up on same-day AI recommendation
    review changes, not just compute "today" once.
    """
    analytics_service.recompute_all_organizations()
