import logging
import socket
import uuid
from decimal import Decimal
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError
from app.db.session import SessionLocal
from app.models.inventory import Inventory
from app.models.mixins import utcnow
from app.models.output_channel import OutputChannelStatus
from app.models.output_job import OutputJob, OutputJobStatus
from app.models.product import Product
from app.outputs.base import OutputRenderContext
from app.outputs.registry import get_output_adapter
from app.repositories.label_template_repository import LabelTemplateRepository
from app.repositories.output_channel_repository import OutputChannelRepository
from app.repositories.output_job_repository import OutputJobRepository
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.output_job import OutputJobBulkCreate, OutputJobCreate, OutputJobDashboardSummary, OutputJobListParams
from app.services import pricing_engine

logger = logging.getLogger(__name__)


def create_job(db: Session, *, organization_id: uuid.UUID, payload: OutputJobCreate) -> OutputJob:
    channel = OutputChannelRepository(db).get_by_id_for_organization(
        payload.output_channel_id, organization_id
    )
    if channel is None:
        raise NotFoundError("Output channel not found.", code="output_channel_not_found")
    if channel.status != OutputChannelStatus.ACTIVE:
        raise ConflictError("This output channel is inactive.", code="output_channel_inactive")
    if ProductRepository(db).get_by_id_for_organization(payload.product_id, organization_id) is None:
        raise NotFoundError("Product not found.", code="product_not_found")
    if (
        payload.store_id is not None
        and StoreRepository(db).get_by_id_for_organization(payload.store_id, organization_id) is None
    ):
        raise NotFoundError("Store not found.", code="store_not_found")

    job = OutputJob(
        id=uuid.uuid4(),
        organization_id=organization_id,
        output_channel_id=channel.id,
        product_id=payload.product_id,
        store_id=payload.store_id,
        status=OutputJobStatus.PENDING,
        attempts=0,
    )
    job = OutputJobRepository(db).add(job)
    # Commit BEFORE dispatching: the Celery worker is a separate process that
    # reads the committed DB, so it races the FastAPI request-scoped get_db()
    # commit. If we dispatch first, the worker finds no (still-uncommitted) job
    # row and gives up, leaving the job stuck as pending forever.
    db.commit()
    _dispatch(job.id)
    # The dev-only synchronous fallback in _dispatch() (see its comment)
    # processes the job through a *different* session — this one's `job`
    # object would otherwise still show its pre-dispatch "pending" snapshot
    # even though the row is already "completed"/"failed" in the DB.
    # Refresh so the response reflects reality; a no-op when a real Celery
    # worker picks the job up later instead (still correctly "pending").
    db.refresh(job)
    return job


def create_bulk_jobs(
    db: Session, *, organization_id: uuid.UUID, payload: OutputJobBulkCreate
) -> list[OutputJob]:
    """Create one OutputJob per product_id, all sharing the same channel/store.

    Validation runs for every product before any row is written so a single
    bad product_id rejects the whole batch rather than partially creating jobs.
    """
    channel = OutputChannelRepository(db).get_by_id_for_organization(
        payload.output_channel_id, organization_id
    )
    if channel is None:
        raise NotFoundError("Output channel not found.", code="output_channel_not_found")
    if channel.status != OutputChannelStatus.ACTIVE:
        raise ConflictError("This output channel is inactive.", code="output_channel_inactive")

    if payload.store_id is not None and (
        StoreRepository(db).get_by_id_for_organization(payload.store_id, organization_id) is None
    ):
        raise NotFoundError("Store not found.", code="store_not_found")

    product_repo = ProductRepository(db)
    missing = []
    for pid in payload.product_ids:
        if product_repo.get_by_id_for_organization(pid, organization_id) is None:
            missing.append(pid)
    if missing:
        raise NotFoundError(
            f"Products not found: {', '.join(str(p) for p in missing)}.",
            code="product_not_found",
        )

    jobs: list[OutputJob] = []
    for pid in payload.product_ids:
        job = OutputJob(
            id=uuid.uuid4(),
            organization_id=organization_id,
            output_channel_id=channel.id,
            product_id=pid,
            store_id=payload.store_id,
            status=OutputJobStatus.PENDING,
            attempts=0,
        )
        job = OutputJobRepository(db).add(job)
        jobs.append(job)

    # Commit BEFORE dispatching every job — same race-protection as create_job.
    db.commit()
    for job in jobs:
        _dispatch(job.id)
    for job in jobs:
        db.refresh(job)
    return jobs


def get_job(db: Session, *, organization_id: uuid.UUID, job_id: uuid.UUID) -> OutputJob:
    job = OutputJobRepository(db).get_by_id_for_organization(job_id, organization_id)
    if job is None:
        raise NotFoundError("Output job not found.", code="output_job_not_found")
    return job


def list_jobs(
    db: Session, *, organization_id: uuid.UUID, params: OutputJobListParams
) -> tuple[list[OutputJob], int]:
    offset = (params.page - 1) * params.page_size
    return OutputJobRepository(db).search(
        organization_id,
        output_channel_id=params.output_channel_id,
        product_id=params.product_id,
        store_id=params.store_id,
        status=params.status,
        offset=offset,
        limit=params.page_size,
    )


def retry_job(db: Session, *, organization_id: uuid.UUID, job_id: uuid.UUID) -> OutputJob:
    job = get_job(db, organization_id=organization_id, job_id=job_id)
    if job.status not in (OutputJobStatus.FAILED, OutputJobStatus.COMPLETED):
        raise ConflictError(
            f"Only failed or completed jobs can be retried (current status: {job.status}).",
            code="output_job_not_retryable",
        )
    job.status = OutputJobStatus.PENDING
    job.last_error = None
    job.completed_at = None
    OutputJobRepository(db).add(job)
    # Same ordering as create_job: persist the PENDING status before dispatching,
    # or the worker (separate process) reads the stale completed/failed status
    # and skips the job.
    db.commit()
    _dispatch(job.id)
    db.refresh(job)  # see create_job's comment on why this is needed
    return job


def cancel_job(db: Session, *, organization_id: uuid.UUID, job_id: uuid.UUID) -> OutputJob:
    """Only a still-queued job can be cancelled — one that's already
    PROCESSING may be mid-send on a worker, and COMPLETED/FAILED/CANCELLED
    are already terminal.
    """
    job = get_job(db, organization_id=organization_id, job_id=job_id)
    if job.status != OutputJobStatus.PENDING:
        raise ConflictError(
            f"Only pending jobs can be cancelled (current status: {job.status}).",
            code="output_job_not_cancellable",
        )
    job.status = OutputJobStatus.CANCELLED
    job.completed_at = utcnow()
    OutputJobRepository(db).add(job)
    return job


def get_dashboard_summary(db: Session, *, organization_id: uuid.UUID) -> OutputJobDashboardSummary:
    counts = OutputJobRepository(db).status_counts(organization_id)
    return OutputJobDashboardSummary(
        total=sum(counts.values()),
        pending=counts.get(OutputJobStatus.PENDING, 0),
        processing=counts.get(OutputJobStatus.PROCESSING, 0),
        successful=counts.get(OutputJobStatus.COMPLETED, 0),
        failed=counts.get(OutputJobStatus.FAILED, 0),
        cancelled=counts.get(OutputJobStatus.CANCELLED, 0),
    )


def _dispatch(job_id: uuid.UUID) -> None:
    if _broker_reachable():
        try:
            from app.tasks.outputs import process_output_job_task

            process_output_job_task.delay(str(job_id))
            return
        except Exception:  # noqa: BLE001 — broker went away between the check and the dispatch
            logger.warning("Could not dispatch output job %s to Celery.", job_id)
            return

    # Dev-only fallback: a real deployment always has Redis/Celery reachable
    # (see infrastructure/docker-compose.yml's celery_worker service), so a
    # job would only ever sit here waiting for a worker in local dev without
    # Redis running. Rather than leaving it stuck "pending" forever, process
    # it synchronously right here — same process_output_job() a worker would
    # call, just invoked inline instead of via Celery's .delay(). Wrapped in
    # try/except: this opens its own SessionLocal() against whatever
    # DATABASE_URL is configured, which in a test/CI environment may not be
    # reachable at all — a failure here must fail soft, exactly like the
    # broker-unreachable case it's substituting for, not bubble up and break
    # the request that dispatched the job.
    logger.warning(
        "Redis broker unreachable — processing output job %s synchronously instead of leaving it "
        "pending (dev-only fallback; production always has a Celery worker available).",
        job_id,
    )
    try:
        process_output_job(job_id)
    except Exception:  # noqa: BLE001 — see comment above; leave the job pending rather than raise
        logger.warning("Synchronous fallback processing failed for output job %s.", job_id)


def _broker_reachable(timeout: float = 0.5) -> bool:
    """Same quick TCP pre-check as app.services.import_service — kept as a
    deliberately-duplicated copy rather than a shared import, matching this
    project's existing preference (see tests/conftest.py) for independent
    copies of small fixture/infra logic over cross-module coupling.
    """
    url = urlparse(get_settings().redis_url)
    try:
        with socket.create_connection((url.hostname or "localhost", url.port or 6379), timeout=timeout):
            return True
    except OSError:
        return False


def _build_public_url(product_id: uuid.UUID, store_id: uuid.UUID | None) -> str:
    base = get_settings().public_base_url.rstrip("/")
    url = f"{base}/public/price/{product_id}"
    return f"{url}?store_id={store_id}" if store_id else url


def resolve_display_price(
    db: Session, *, organization_id: uuid.UUID, product: Product, store_id: uuid.UUID | None
) -> tuple[Decimal, str]:
    """The price an output should show: the fully rule-applied final price
    (app.services.pricing_engine), not just the raw stored Price row — an
    output that skipped active pricing rules would show a stale number.
    """
    now = utcnow()
    result = pricing_engine.evaluate_for_product(
        db, organization_id=organization_id, product=product, store_id=store_id, now=now
    )
    current = PriceRepository(db).get_current_effective(
        organization_id, product_id=product.id, store_id=store_id, now=now
    )
    currency = current.currency if current else (product.currency or "USD")
    return result.final_price, currency


def process_output_job(job_id: uuid.UUID, db: Session | None = None) -> None:
    """The worker logic. In production the thin Celery task
    (app/tasks/outputs.py) calls this with no session, so it opens and
    manages its own — mirrors app.services.import_service.process_import_job.
    """
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    try:
        _run(session, job_id)
    finally:
        if owns_session:
            session.close()


def _run(db: Session, job_id: uuid.UUID) -> None:
    job_repo = OutputJobRepository(db)
    job = job_repo.get_by_id(job_id)
    if job is None:
        logger.error("process_output_job: job %s not found", job_id)
        return
    if job.status != OutputJobStatus.PENDING:
        logger.warning("process_output_job: job %s has status %s, skipping", job_id, job.status)
        return

    job.status = OutputJobStatus.PROCESSING
    job.attempts += 1
    job_repo.add(job)
    db.commit()

    try:
        channel = OutputChannelRepository(db).get_by_id(job.output_channel_id)
        product = ProductRepository(db).get_by_id(job.product_id)
        if channel is None or product is None:
            raise ValueError("The output channel or product no longer exists.")
        store = StoreRepository(db).get_by_id(job.store_id) if job.store_id else None

        price, currency = resolve_display_price(
            db, organization_id=job.organization_id, product=product, store_id=job.store_id
        )

        # Base price for promo comparison + stock count for the QR label
        current_price_row = PriceRepository(db).get_current_effective(
            job.organization_id, product_id=product.id, store_id=job.store_id, now=utcnow()
        )
        base_price = current_price_row.base_price if current_price_row else product.selling_price

        stock_qty: int | None = None
        if job.store_id:
            inv = db.query(Inventory).filter_by(
                organization_id=job.organization_id,
                product_id=product.id,
                store_id=job.store_id,
            ).first()
            stock_qty = inv.quantity_on_hand if inv else None

        # Stage 2: resolve the channel's visual template (colors + background
        # image) here — the single resolution point. Adapters stay DB-free and
        # read the resolved overrides from the context; a future template
        # builder just writes LabelTemplate rows and this picks them up.
        template_colors: dict[str, str] | None = None
        template_background_image_url: str | None = None
        if channel.label_template_id is not None:
            template = LabelTemplateRepository(db).get_by_id(channel.label_template_id)
            if template is not None:
                template_colors = template.colors
                template_background_image_url = template.background_image_url

        context = OutputRenderContext(
            product=product,
            store=store,
            price=price,
            currency=currency,
            public_url=_build_public_url(job.product_id, job.store_id),
            configuration=channel.configuration or {},
            base_price=base_price,
            stock_qty=stock_qty,
            template_colors=template_colors,
            template_background_image_url=template_background_image_url,
        )
        adapter = get_output_adapter(channel.output_type)
        payload = adapter.render_payload(context)
        job.payload = adapter.send_update(job=job, context=context, payload=payload)
        job.status = OutputJobStatus.COMPLETED
        job.last_error = None
    except Exception as exc:  # noqa: BLE001 — isolate failures to this one job
        logger.exception("output job %s failed", job_id)
        job.status = OutputJobStatus.FAILED
        job.last_error = str(exc)

    job.completed_at = utcnow()
    job_repo.add(job)
    db.commit()
