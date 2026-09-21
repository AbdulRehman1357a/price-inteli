import logging
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.db.session import SessionLocal
from app.models.external_price import ExternalPrice
from app.models.integration_mapping import CanonicalEntityType
from app.models.integration_sync_job import (
    IntegrationSyncDirection,
    IntegrationSyncJob,
    IntegrationSyncJobStatus,
    IntegrationSyncJobType,
)
from app.models.mixins import utcnow
from app.repositories.external_price_repository import ExternalPriceRepository
from app.repositories.integration_repository import IntegrationRepository
from app.repositories.integration_sync_job_repository import IntegrationSyncJobRepository
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.services import integration_service
from app.services.integration_service import get_integration

logger = logging.getLogger(__name__)

# --- Outbound execution (PIP -> External), Phase 10 upgrade ---
# Deliberately its own worker path rather than folded into
# integration_sync_service._run(), which is inbound-only (fetch ->
# map -> apply). Outbound has no mapping step — a Price row is already
# canonical — so the pipeline is genuinely simpler: resolve external_id ->
# build a payload -> adapter.push_records(). Still produces an
# IntegrationSyncJob(direction="outbound") row for the same audit trail
# and job-history UI as every inbound sync.


def create_push_job(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, price_ids: list[uuid.UUID]
) -> IntegrationSyncJob:
    integration = get_integration(db, organization_id=organization_id, integration_id=integration_id)
    adapter = integration_service.adapter_for(integration)
    if not adapter.supports_price_write:
        raise ValidationError(
            f"The {integration.provider.value} adapter does not support pushing price updates outward."
        )
    if not price_ids:
        raise ValidationError("At least one price_id is required to push.")

    job = IntegrationSyncJobRepository(db).add(
        IntegrationSyncJob(
            id=uuid.uuid4(),
            integration_id=integration_id,
            job_type=IntegrationSyncJobType.FULL_SYNC,
            entity_type=CanonicalEntityType.PRICE,
            status=IntegrationSyncJobStatus.PENDING,
            direction=IntegrationSyncDirection.OUTBOUND,
            pushed_records=[str(pid) for pid in price_ids],
        )
    )
    # Commit before dispatching — the Celery worker is a separate OS
    # process reading the committed DB, so dispatching first would race
    # the request-scoped get_db() commit and risk the worker finding the
    # job not yet there (the same gap CLAUDE.md documents for Phase 7's
    # output_job_service; get it right from the start here).
    db.commit()
    _dispatch(job.id)
    # See integration_sync_service.create_sync_job's comment: the dev-only
    # synchronous fallback processes this job through a different session,
    # so refresh to reflect its real status instead of a stale "pending".
    db.refresh(job)
    return job


def _dispatch(job_id: uuid.UUID) -> None:
    from app.services.integration_sync_service import _broker_reachable

    if _broker_reachable():
        try:
            from app.tasks.integrations import process_push_job_task

            process_push_job_task.delay(str(job_id))
            return
        except Exception:  # noqa: BLE001 — broker went away between the check and the dispatch
            logger.warning("Could not dispatch integration push job %s to Celery.", job_id)
            return

    # Dev-only fallback — see integration_sync_service._dispatch's comment
    # for why: without a reachable broker the job would otherwise sit
    # "pending" forever, so process it synchronously here instead. Wrapped
    # in try/except so a failure (e.g. no real DB reachable in a test/CI
    # environment) fails soft rather than bubbling up into the request.
    logger.warning(
        "Redis broker unreachable — processing integration push job %s synchronously instead of "
        "leaving it pending (dev-only fallback; production always has a Celery worker available).",
        job_id,
    )
    try:
        process_push_job(job_id)
    except Exception:  # noqa: BLE001 — see comment above; leave the job pending rather than raise
        logger.warning("Synchronous fallback processing failed for integration push job %s.", job_id)


def process_push_job(job_id: uuid.UUID, db: Session | None = None) -> None:
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    try:
        _run(session, job_id)
    finally:
        if owns_session:
            session.close()


def _run(db: Session, job_id: uuid.UUID) -> None:
    job_repo = IntegrationSyncJobRepository(db)
    job = job_repo.get_by_id(job_id)
    if job is None or job.status != IntegrationSyncJobStatus.PENDING:
        return

    job.status = IntegrationSyncJobStatus.PROCESSING
    job_repo.add(job)
    db.commit()

    integration = IntegrationRepository(db).get_by_id(job.integration_id)
    if integration is None:
        job.status = IntegrationSyncJobStatus.FAILED
        job.error_details = [{"message": "The integration no longer exists."}]
        job.completed_at = utcnow()
        job_repo.add(job)
        db.commit()
        return

    adapter = integration_service.adapter_for(integration)
    credentials = integration_service.decrypt(integration)
    price_repo = PriceRepository(db)
    product_repo = ProductRepository(db)
    ext_price_repo = ExternalPriceRepository(db)

    records = []
    price_id_by_index: list[uuid.UUID] = []
    for raw_price_id in job.pushed_records or []:
        price_id = uuid.UUID(raw_price_id)
        price = price_repo.get_by_id_for_organization(price_id, integration.organization_id)
        if price is None:
            continue
        product = product_repo.get_by_id_for_organization(price.product_id, integration.organization_id)
        if product is None:
            continue
        ext_price = ext_price_repo.get_by_sku_store(
            integration.id, sku=product.sku, store_code=None
        )
        records.append(
            {
                "sku": product.sku,
                "external_id": ext_price.sku if ext_price else product.sku,
                "selling_price": str(price.selling_price),
                "currency": price.currency,
            }
        )
        price_id_by_index.append(price_id)

    records_created = 0
    records_failed = 0
    error_details = []
    try:
        result = adapter.push_records(integration, credentials, entity_type="price", records=records)
    except Exception as exc:  # noqa: BLE001 — the destination itself is unreachable/broken
        job.status = IntegrationSyncJobStatus.FAILED
        job.error_details = [{"message": f"Could not push records: {exc}"}]
        job.error_type = "connection"
        job.completed_at = utcnow()
        job_repo.add(job)
        db.commit()
        return

    for index, item in enumerate(result.get("results", [{"success": True}] * len(records))):
        price_id = price_id_by_index[index] if index < len(price_id_by_index) else None
        if item.get("success"):
            records_created += 1
            if price_id is not None:
                _record_outbound_sync(db, integration_id=integration.id, price_id=price_id)
        else:
            records_failed += 1
            error_details.append({"row": index + 1, "message": item.get("message", "Push failed.")})

    now = utcnow()
    job.records_processed = records_created
    job.records_created = records_created
    job.records_failed = records_failed
    job.error_details = error_details or None
    job.status = (
        IntegrationSyncJobStatus.COMPLETED_WITH_ERRORS
        if error_details
        else IntegrationSyncJobStatus.COMPLETED
    )
    job.completed_at = now
    job_repo.add(job)
    integration.last_sync_at = now
    IntegrationRepository(db).add(integration)
    db.commit()


def _record_outbound_sync(db: Session, *, integration_id: uuid.UUID, price_id: uuid.UUID) -> None:
    price = PriceRepository(db).get_by_id(price_id)
    if price is None:
        return
    product = ProductRepository(db).get_by_id(price.product_id)
    if product is None:
        return
    repo = ExternalPriceRepository(db)
    existing = repo.get_by_sku_store(integration_id, sku=product.sku, store_code=None)
    now = utcnow()
    if existing is not None:
        existing.price_id = price.id
        existing.external_selling_price = price.selling_price
        existing.currency = price.currency
        existing.direction = IntegrationSyncDirection.OUTBOUND
        existing.last_synced_at = now
        repo.add(existing)
        return
    repo.add(
        ExternalPrice(
            id=uuid.uuid4(),
            integration_id=integration_id,
            sku=product.sku,
            store_code=None,
            price_id=price.id,
            external_selling_price=price.selling_price,
            currency=price.currency,
            direction=IntegrationSyncDirection.OUTBOUND,
            last_synced_at=now,
        )
    )
