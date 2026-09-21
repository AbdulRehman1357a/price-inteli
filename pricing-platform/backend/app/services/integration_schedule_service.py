import uuid
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import SessionLocal
from app.models.integration_sync_job import IntegrationSyncJob, IntegrationSyncJobStatus
from app.models.integration_sync_schedule import IntegrationSyncSchedule
from app.models.mixins import utcnow
from app.repositories.integration_sync_job_repository import IntegrationSyncJobRepository
from app.repositories.integration_sync_schedule_repository import IntegrationSyncScheduleRepository
from app.schemas.integration_sync_schedule import IntegrationSyncScheduleCreate, IntegrationSyncScheduleUpdate
from app.services.integration_service import get_integration


def create_schedule(
    db: Session,
    *,
    organization_id: uuid.UUID,
    integration_id: uuid.UUID,
    payload: IntegrationSyncScheduleCreate,
) -> IntegrationSyncSchedule:
    get_integration(db, organization_id=organization_id, integration_id=integration_id)  # tenant check

    schedule = IntegrationSyncSchedule(
        id=uuid.uuid4(),
        integration_id=integration_id,
        entity_type=payload.entity_type,
        job_type=payload.job_type,
        interval_minutes=payload.interval_minutes,
        is_enabled=True,
        next_run_at=utcnow() + timedelta(minutes=payload.interval_minutes),
    )
    return IntegrationSyncScheduleRepository(db).add(schedule)


def list_schedules(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID
) -> list[IntegrationSyncSchedule]:
    get_integration(db, organization_id=organization_id, integration_id=integration_id)  # tenant check
    return IntegrationSyncScheduleRepository(db).list_for_integration(integration_id)


def update_schedule(
    db: Session,
    *,
    organization_id: uuid.UUID,
    schedule_id: uuid.UUID,
    payload: IntegrationSyncScheduleUpdate,
) -> IntegrationSyncSchedule:
    repo = IntegrationSyncScheduleRepository(db)
    schedule = repo.get_by_id_for_organization(schedule_id, organization_id)
    if schedule is None:
        raise NotFoundError(
            "Integration sync schedule not found.", code="integration_sync_schedule_not_found"
        )

    data = payload.model_dump(exclude_unset=True)
    if "interval_minutes" in data:
        schedule.interval_minutes = data["interval_minutes"]
    if "is_enabled" in data:
        schedule.is_enabled = data["is_enabled"]
    return repo.add(schedule)


def dispatch_due_schedules(db: Session | None = None) -> int:
    """Called every minute by a Celery Beat task
    (app.tasks.integrations.dispatch_due_sync_schedules_task) — scans
    every organization's due schedules in one pass (cross-tenant by
    design, since Beat runs globally) and dispatches a sync job per row,
    same as a manually-triggered POST /integrations/{id}/sync. Returns the
    number of jobs dispatched (for logging/observability).
    """
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    try:
        return _dispatch_due(session)
    finally:
        if owns_session:
            session.close()


def _dispatch_due(db: Session) -> int:
    from app.services import integration_sync_service

    repo = IntegrationSyncScheduleRepository(db)
    now = utcnow()
    due = repo.list_due(now=now)

    dispatched = 0
    for schedule in due:
        job = IntegrationSyncJobRepository(db).add(
            IntegrationSyncJob(
                id=uuid.uuid4(),
                integration_id=schedule.integration_id,
                job_type=schedule.job_type,
                entity_type=schedule.entity_type,
                status=IntegrationSyncJobStatus.PENDING,
                correlation_id=schedule.id,
            )
        )
        schedule.last_dispatched_job_id = job.id
        schedule.next_run_at = now + timedelta(minutes=schedule.interval_minutes)
        repo.add(schedule)
        db.commit()
        integration_sync_service._dispatch(job.id)  # noqa: SLF001 — same internal dispatch every sync job uses
        dispatched += 1
    return dispatched
