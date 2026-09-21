import logging
import socket
import uuid
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError
from app.db.session import SessionLocal
from app.models.integration_checkpoint import IntegrationCheckpoint
from app.models.integration_error import IntegrationError, IntegrationErrorSeverity
from app.models.integration_mapping import CanonicalEntityType
from app.models.integration_sync_job import (
    IntegrationSyncDirection,
    IntegrationSyncJob,
    IntegrationSyncJobStatus,
)
from app.models.mixins import utcnow
from app.repositories.integration_checkpoint_repository import IntegrationCheckpointRepository
from app.repositories.integration_error_repository import IntegrationErrorRepository
from app.repositories.integration_mapping_repository import IntegrationMappingRepository
from app.repositories.integration_repository import IntegrationRepository
from app.repositories.integration_sync_job_repository import IntegrationSyncJobRepository
from app.schemas.canonical import (
    CanonicalInventory,
    CanonicalOrder,
    CanonicalPrice,
    CanonicalProduct,
    CanonicalPromotion,
    CanonicalStore,
)
from app.schemas.integration_sync_job import IntegrationSyncJobListParams, IntegrationSyncRequest
from app.services import integration_apply_service, integration_service
from app.services.integration_authority_service import AuthorityBlockedError
from app.services.integration_mapping_engine import TransformationError, map_record
from app.services.integration_retry_policy import with_retry

logger = logging.getLogger(__name__)

_CANONICAL_MODEL_BY_ENTITY_TYPE: dict[CanonicalEntityType, type] = {
    CanonicalEntityType.PRODUCT: CanonicalProduct,
    CanonicalEntityType.PRICE: CanonicalPrice,
    CanonicalEntityType.INVENTORY: CanonicalInventory,
    CanonicalEntityType.PROMOTION: CanonicalPromotion,
    CanonicalEntityType.STORE: CanonicalStore,
    CanonicalEntityType.ORDER: CanonicalOrder,
}

_APPLY_FN_BY_ENTITY_TYPE = {
    CanonicalEntityType.PRODUCT: integration_apply_service.apply_product,
    CanonicalEntityType.PRICE: integration_apply_service.apply_price,
    CanonicalEntityType.INVENTORY: integration_apply_service.apply_inventory,
    CanonicalEntityType.PROMOTION: integration_apply_service.apply_promotion,
    CanonicalEntityType.STORE: integration_apply_service.apply_store,
    CanonicalEntityType.ORDER: integration_apply_service.apply_order,
}

# Per-record exceptions that don't abort the whole job — isolated in
# db.begin_nested() and appended to error_details, same as before the
# Phase 10 upgrade. AuthorityBlockedError is new: a record whose write was
# refused because PIP owns that field is a per-record outcome, not a
# whole-job failure.
_PER_RECORD_ERRORS = (
    TransformationError,
    PydanticValidationError,
    integration_apply_service.ApplyError,
    AuthorityBlockedError,
)


def create_sync_job(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, payload: IntegrationSyncRequest
) -> IntegrationSyncJob:
    integration_service.get_integration(
        db, organization_id=organization_id, integration_id=integration_id
    )  # tenant check

    job = IntegrationSyncJobRepository(db).add(
        IntegrationSyncJob(
            id=uuid.uuid4(),
            integration_id=integration_id,
            job_type=payload.job_type,
            entity_type=payload.entity_type,
            status=IntegrationSyncJobStatus.PENDING,
            direction=IntegrationSyncDirection.INBOUND,
            pushed_records=payload.records or None,
        )
    )
    # Commit before dispatching — the Celery worker is a separate OS process
    # reading the committed DB, so dispatching first would race the
    # request-scoped get_db() commit and risk the worker finding the job
    # not yet there (the exact gap CLAUDE.md documents for Phase 7's
    # output_job_service and Phase 10's webhook pushed_records).
    db.commit()
    _dispatch(job.id)
    # The dev-only synchronous fallback in _dispatch() (see its docstring)
    # processes the job through a *different* session — this one's `job`
    # object would otherwise still show its pre-dispatch "pending" snapshot
    # even though the row is already "completed" in the DB. Refresh so the
    # response reflects reality; a no-op when a real Celery worker picks
    # the job up later instead (still correctly "pending").
    db.refresh(job)
    return job


def get_job(db: Session, *, organization_id: uuid.UUID, job_id: uuid.UUID) -> IntegrationSyncJob:
    job = IntegrationSyncJobRepository(db).get_by_id_for_organization(job_id, organization_id)
    if job is None:
        raise NotFoundError("Sync job not found.", code="integration_sync_job_not_found")
    return job


def list_jobs(
    db: Session,
    *,
    organization_id: uuid.UUID,
    integration_id: uuid.UUID,
    params: IntegrationSyncJobListParams,
) -> tuple[list[IntegrationSyncJob], int]:
    integration_service.get_integration(
        db, organization_id=organization_id, integration_id=integration_id
    )  # tenant check
    offset = (params.page - 1) * params.page_size
    return IntegrationSyncJobRepository(db).search_for_integration(
        integration_id=integration_id,
        organization_id=organization_id,
        status=params.status,
        offset=offset,
        limit=params.page_size,
    )


def retry_job(
    db: Session, *, organization_id: uuid.UUID, job_id: uuid.UUID, records: list[dict[str, Any]] | None = None
) -> IntegrationSyncJob:
    job = get_job(db, organization_id=organization_id, job_id=job_id)
    if job.status not in (IntegrationSyncJobStatus.FAILED, IntegrationSyncJobStatus.COMPLETED_WITH_ERRORS):
        raise ConflictError(
            f"Only failed jobs can be retried (current status: {job.status}).",
            code="integration_sync_job_not_retryable",
        )

    job.status = IntegrationSyncJobStatus.PENDING
    job.records_processed = 0
    job.records_created = 0
    job.records_updated = 0
    job.records_skipped = 0
    job.records_failed = 0
    job.error_details = None
    job.error_type = None
    job.completed_at = None
    job.retry_count += 1
    if records:
        job.pushed_records = records
    IntegrationSyncJobRepository(db).add(job)

    # Same pre-dispatch commit fix as create_sync_job — see its comment.
    db.commit()
    _dispatch(job.id)
    db.refresh(job)  # see create_sync_job's comment on why this is needed
    return job


def _dispatch(job_id: uuid.UUID) -> None:
    if _broker_reachable():
        try:
            from app.tasks.integrations import process_sync_job_task

            process_sync_job_task.delay(str(job_id))
            return
        except Exception:  # noqa: BLE001 — broker went away between the check and the dispatch
            logger.warning("Could not dispatch integration sync job %s to Celery.", job_id)
            return

    # Dev-only fallback: a real deployment always has Redis/Celery reachable
    # (see infrastructure/docker-compose.yml's celery_worker service), so a
    # job would only ever sit here waiting for a worker in local dev without
    # Redis running. Rather than leaving it stuck "pending" forever, process
    # it synchronously right here — same process_sync_job() a worker would
    # call, just invoked inline instead of via Celery's .delay(). Wrapped in
    # try/except: this opens its own SessionLocal() against whatever
    # DATABASE_URL is configured, which in a test/CI environment may not be
    # reachable at all (unlike the test suite's own SQLite db_session
    # fixture) — a failure here must fail soft, exactly like the
    # broker-unreachable case it's substituting for, not bubble up and
    # break the request/test that dispatched the job.
    logger.warning(
        "Redis broker unreachable — processing integration sync job %s synchronously instead of "
        "leaving it pending (dev-only fallback; production always has a Celery worker available).",
        job_id,
    )
    try:
        process_sync_job(job_id)
    except Exception:  # noqa: BLE001 — see comment above; leave the job pending rather than raise
        logger.warning("Synchronous fallback processing failed for integration sync job %s.", job_id)


def _broker_reachable(timeout: float = 0.5) -> bool:
    url = urlparse(get_settings().redis_url)
    try:
        with socket.create_connection((url.hostname or "localhost", url.port or 6379), timeout=timeout):
            return True
    except OSError:
        return False


def process_sync_job(job_id: uuid.UUID, db: Session | None = None) -> None:
    """The worker logic. In production the thin Celery task
    (app/tasks/integrations.py) calls this with no session, so it opens and
    manages its own — mirrors app.services.import_service.process_import_job
    and app.services.output_job_service.process_output_job.
    """
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    try:
        _run(session, job_id)
    finally:
        if owns_session:
            session.close()


def _record_job_error(
    db: Session, *, integration_id: uuid.UUID, job_id: uuid.UUID, error_type: str, message: str
) -> None:
    IntegrationErrorRepository(db).add(
        IntegrationError(
            id=uuid.uuid4(),
            integration_id=integration_id,
            sync_job_id=job_id,
            error_type=error_type,
            severity=IntegrationErrorSeverity.ERROR,
            message=message,
        )
    )


def _touch_checkpoint(db: Session, *, integration_id: uuid.UUID, entity_type: CanonicalEntityType) -> None:
    """Records "this entity type last synced successfully at <now>" —
    the honest scope of checkpointing in this pass: a plain watermark, not
    a real adapter-defined cursor. No adapter in this build threads a
    since-cursor back into fetch_records() yet (see
    RESTAPIAdapter.supports_incremental_sync's docstring); this keeps the
    table genuinely populated rather than an inert placeholder, ready for
    a future adapter to read cursor_value once one supports it.
    """
    repo = IntegrationCheckpointRepository(db)
    existing = repo.get_for_entity_type(integration_id, entity_type)
    now = utcnow()
    if existing is not None:
        existing.last_synced_at = now
        repo.add(existing)
        return
    repo.add(
        IntegrationCheckpoint(
            id=uuid.uuid4(), integration_id=integration_id, entity_type=entity_type, last_synced_at=now
        )
    )


def _run(db: Session, job_id: uuid.UUID) -> None:
    job_repo = IntegrationSyncJobRepository(db)
    job = job_repo.get_by_id(job_id)
    if job is None:
        logger.error("process_sync_job: job %s not found", job_id)
        return
    if job.status != IntegrationSyncJobStatus.PENDING:
        logger.warning("process_sync_job: job %s has status %s, skipping", job_id, job.status)
        return

    job.status = IntegrationSyncJobStatus.PROCESSING
    job_repo.add(job)
    db.commit()

    integration = IntegrationRepository(db).get_by_id(job.integration_id)
    if integration is None:
        job.status = IntegrationSyncJobStatus.FAILED
        job.error_details = [{"message": "The integration no longer exists."}]
        job.error_type = "mapping"
        job.completed_at = utcnow()
        job_repo.add(job)
        db.commit()
        return

    mappings = IntegrationMappingRepository(db).list_for_integration(
        integration_id=integration.id, entity_type=job.entity_type
    )
    canonical_model = _CANONICAL_MODEL_BY_ENTITY_TYPE[job.entity_type]
    apply_fn = _APPLY_FN_BY_ENTITY_TYPE[job.entity_type]

    records_created = 0
    records_updated = 0
    records_skipped = 0
    error_details: list[dict[str, Any]] = []

    try:
        adapter = integration_service.adapter_for(integration)
        credentials = integration_service.decrypt(integration)
        raw_records = with_retry(
            lambda: adapter.fetch_records(
                integration, credentials, entity_type=job.entity_type.value, records=job.pushed_records
            )
        )
    except Exception as exc:  # noqa: BLE001 — the source itself is unreachable/broken
        logger.exception("integration sync job %s: could not fetch records", job_id)
        job.status = IntegrationSyncJobStatus.FAILED
        job.error_details = [{"message": f"Could not fetch records: {exc}"}]
        job.error_type = "rate_limited" if _is_rate_limited(exc) else "connection"
        job.completed_at = utcnow()
        job_repo.add(job)
        _record_job_error(
            db,
            integration_id=integration.id,
            job_id=job.id,
            error_type=job.error_type,
            message=str(exc),
        )
        db.commit()
        return

    for index, raw_record in enumerate(raw_records):
        try:
            mapped = map_record(raw_record, mappings)
            with db.begin_nested():
                canonical = canonical_model(**mapped)
                result = apply_fn(
                    db,
                    organization_id=integration.organization_id,
                    integration_id=integration.id,
                    canonical=canonical,
                )
        except _PER_RECORD_ERRORS as exc:
            error_details.append({"row": index + 1, "message": str(exc)})
        except Exception as exc:  # noqa: BLE001 — isolate unexpected per-record failures
            logger.exception("integration sync job %s: unexpected error on row %s", job_id, index + 1)
            error_details.append({"row": index + 1, "message": str(exc)})
        else:
            if result.status == "created":
                records_created += 1
            elif result.status == "updated":
                records_updated += 1
            else:
                records_skipped += 1

    now = utcnow()
    records_processed = records_created + records_updated + records_skipped
    job.records_processed = records_processed
    job.records_created = records_created
    job.records_updated = records_updated
    job.records_skipped = records_skipped
    job.records_failed = len(error_details)
    job.error_details = error_details or None
    job.error_type = "validation" if error_details else None
    job.status = (
        IntegrationSyncJobStatus.COMPLETED_WITH_ERRORS
        if error_details
        else IntegrationSyncJobStatus.COMPLETED
    )
    job.completed_at = now
    job_repo.add(job)

    integration.last_sync_at = now
    IntegrationRepository(db).add(integration)

    if records_processed > 0:
        _touch_checkpoint(db, integration_id=integration.id, entity_type=job.entity_type)

    db.commit()


def _is_rate_limited(exc: Exception) -> bool:
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429
