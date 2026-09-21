import datetime as dt
import logging
import socket
import uuid
from collections import defaultdict
from decimal import Decimal
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core import cache
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.analytics_snapshot import AnalyticsSnapshot
from app.models.mixins import utcnow
from app.repositories.ai_pricing_recommendation_repository import AIPricingRecommendationRepository
from app.repositories.analytics_snapshot_repository import AnalyticsSnapshotRepository
from app.repositories.device_sync_log_repository import DeviceSyncLogRepository
from app.repositories.inventory_adjustment_repository import InventoryAdjustmentRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.price_history_repository import PriceHistoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.analytics import DashboardMetricsOut, DashboardQueryParams

logger = logging.getLogger(__name__)

DEFAULT_RANGE_DAYS = 30
# Bound on how many not-yet-computed days a single dashboard request will
# aggregate inline. Below this, a cache/snapshot miss just costs a handful
# of grouped SQL queries over a bounded window (cheap, per "do not compute
# complex reports synchronously for large datasets" this stays small);
# above it, the request enqueues a background recompute and serves
# whatever's already there instead of blocking on a big backfill.
LAZY_COMPUTE_MAX_DAYS = 35
CACHE_TTL_SECONDS = 120
# How many trailing days the periodic beat task re-touches, not just
# "today" — AIPricingRecommendation.status keeps changing after creation
# via human review, so yesterday's snapshot can go stale.
CATCH_UP_DAYS = 3

_METRIC_FIELDS = (
    "revenue",
    "cogs",
    "price_changes_count",
    "price_change_amount_sum",
    "ai_recommendations_count",
    "ai_approved_count",
    "device_sync_attempts_count",
    "device_sync_success_count",
    "device_sync_failed_count",
)


def _empty_metrics() -> dict:
    return {
        "revenue": Decimal("0"),
        "cogs": Decimal("0"),
        "price_changes_count": 0,
        "price_change_amount_sum": Decimal("0"),
        "ai_recommendations_count": 0,
        "ai_approved_count": 0,
        "device_sync_attempts_count": 0,
        "device_sync_success_count": 0,
        "device_sync_failed_count": 0,
    }


def _date_range(start: dt.date, end: dt.date) -> list[dt.date]:
    return [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]


def get_dashboard_metrics(
    db: Session, *, organization_id: uuid.UUID, params: DashboardQueryParams
) -> DashboardMetricsOut:
    """Single read entry point behind every Phase 15 dashboard page — pages
    differ only in which fields of the response they render as cards.
    """
    today = utcnow().date()
    date_to = params.date_to or today
    date_from = params.date_from or (date_to - dt.timedelta(days=DEFAULT_RANGE_DAYS - 1))
    if date_from > date_to:
        date_from, date_to = date_to, date_from

    # Today's snapshot is recomputed on every read (see _compute_from_snapshots),
    # so a cached dashboard response whose range spans today is never trusted as
    # final — a price change / adjustment / sync that landed moments ago would be
    # invisible for up to CACHE_TTL_SECONDS. Only settled day-ranges that end
    # strictly before today are served from — and written to — the cache.
    cacheable_range = date_to < today

    cache_key = _cache_key(
        organization_id, date_from, date_to, params.store_id, params.category_id, params.product_id
    )
    if cacheable_range:
        cached = cache.get_json(cache_key)
        if cached is not None:
            return DashboardMetricsOut(**cached)

    if params.category_id is not None or params.product_id is not None:
        # A single category/product is a narrow slice regardless of date
        # range width, so computing it live (never pre-aggregated) is
        # cheap and always fresh — see the repositories' totals_for_filters.
        metrics = _compute_live(
            db,
            organization_id,
            date_from=date_from,
            date_to=date_to,
            store_id=params.store_id,
            category_id=params.category_id,
            product_id=params.product_id,
        )
        is_partial = False
    else:
        metrics, is_partial = _compute_from_snapshots(
            db, organization_id, date_from=date_from, date_to=date_to, store_id=params.store_id
        )

    inventory_counts = InventoryRepository(db).summary_counts(
        organization_id,
        store_id=params.store_id,
        category_id=params.category_id,
        product_id=params.product_id,
    )

    result = _to_metrics_out(
        metrics,
        inventory_counts,
        date_from=date_from,
        date_to=date_to,
        store_id=params.store_id,
        category_id=params.category_id,
        product_id=params.product_id,
        is_partial=is_partial,
    )
    if cacheable_range:
        cache.set_json(cache_key, result.model_dump(mode="json"), ttl_seconds=CACHE_TTL_SECONDS)
    return result


def _compute_from_snapshots(
    db: Session,
    organization_id: uuid.UUID,
    *,
    date_from: dt.date,
    date_to: dt.date,
    store_id: uuid.UUID | None,
) -> tuple[dict, bool]:
    snapshot_repo = AnalyticsSnapshotRepository(db)
    all_days = _date_range(date_from, date_to)
    existing = snapshot_repo.existing_dates(
        organization_id, store_id=store_id, date_from=date_from, date_to=date_to
    )
    today = utcnow().date()
    # Today is still accumulating events, so an existing snapshot row for
    # it is never trusted as final the way a past (fully-settled) day is —
    # it's always recomputed on read. This keeps a same-day dashboard from
    # freezing at whatever it read on the first request of the day, while
    # staying cheap: it's always exactly one extra day of aggregation, no
    # matter how wide the requested range is.
    missing = sorted(day for day in all_days if day not in existing or day == today)

    is_partial = False
    if missing:
        if len(missing) <= LAZY_COMPUTE_MAX_DAYS:
            recompute_range(organization_id, start_date=missing[0], end_date=missing[-1], db=db)
        else:
            _dispatch_recompute(organization_id, date_from, date_to)
            is_partial = True

    metrics = snapshot_repo.aggregate(
        organization_id, store_id=store_id, date_from=date_from, date_to=date_to
    )
    return metrics, is_partial


def _compute_live(
    db: Session,
    organization_id: uuid.UUID,
    *,
    date_from: dt.date,
    date_to: dt.date,
    store_id: uuid.UUID | None,
    category_id: uuid.UUID | None,
    product_id: uuid.UUID | None,
) -> dict:
    filters = dict(
        date_from=date_from,
        date_to=date_to,
        store_id=store_id,
        category_id=category_id,
        product_id=product_id,
    )
    price_count, price_sum = PriceHistoryRepository(db).totals_for_filters(organization_id, **filters)
    ai_total, ai_approved = AIPricingRecommendationRepository(db).totals_for_filters(
        organization_id, **filters
    )
    device_attempts, device_success, device_failed = DeviceSyncLogRepository(db).totals_for_filters(
        organization_id, **filters
    )
    adjustment_totals = InventoryAdjustmentRepository(db).totals_for_filters(organization_id, **filters)

    revenue, cogs = _value_adjustments(db, organization_id, adjustment_totals)

    return {
        "revenue": revenue,
        "cogs": cogs,
        "price_changes_count": price_count,
        "price_change_amount_sum": price_sum,
        "ai_recommendations_count": ai_total,
        "ai_approved_count": ai_approved,
        "device_sync_attempts_count": device_attempts,
        "device_sync_success_count": device_success,
        "device_sync_failed_count": device_failed,
    }


def _value_adjustments(
    db: Session, organization_id: uuid.UUID, adjustment_totals: list[tuple[uuid.UUID, Decimal]]
) -> tuple[Decimal, Decimal]:
    """Prices a list of (product_id, quantity_sold_proxy) pairs at each
    product's CURRENT catalog price/cost — see AnalyticsSnapshot's
    docstring for why this isn't a historical price-at-time-of-sale.
    """
    product_ids = [pid for pid, _ in adjustment_totals]
    prices = ProductRepository(db).list_prices_by_ids(organization_id, product_ids)
    revenue = Decimal("0")
    cogs = Decimal("0")
    for product_id, qty in adjustment_totals:
        selling_price, cost_price = prices.get(product_id, (Decimal("0"), None))
        revenue += qty * selling_price
        cogs += qty * (cost_price or Decimal("0"))
    return revenue, cogs


def _to_metrics_out(
    metrics: dict,
    inventory_counts: dict,
    *,
    date_from: dt.date,
    date_to: dt.date,
    store_id: uuid.UUID | None,
    category_id: uuid.UUID | None,
    product_id: uuid.UUID | None,
    is_partial: bool,
) -> DashboardMetricsOut:
    revenue = metrics["revenue"]
    cogs = metrics["cogs"]
    gross_margin_amount = revenue - cogs
    gross_margin_pct = (
        (gross_margin_amount / revenue * 100).quantize(Decimal("0.01")) if revenue > 0 else None
    )

    price_changes_count = metrics["price_changes_count"]
    average_price_change = (
        (metrics["price_change_amount_sum"] / price_changes_count).quantize(Decimal("0.0001"))
        if price_changes_count
        else None
    )

    ai_count = metrics["ai_recommendations_count"]
    ai_approval_rate_pct = (
        (Decimal(metrics["ai_approved_count"]) / ai_count * 100).quantize(Decimal("0.01"))
        if ai_count
        else None
    )

    device_attempts = metrics["device_sync_attempts_count"]
    device_uptime_pct = (
        (Decimal(metrics["device_sync_success_count"]) / device_attempts * 100).quantize(Decimal("0.01"))
        if device_attempts
        else None
    )

    return DashboardMetricsOut(
        date_from=date_from,
        date_to=date_to,
        store_id=store_id,
        category_id=category_id,
        product_id=product_id,
        revenue=revenue.quantize(Decimal("0.0001")),
        gross_margin_amount=gross_margin_amount.quantize(Decimal("0.0001")),
        gross_margin_pct=gross_margin_pct,
        price_changes_count=price_changes_count,
        average_price_change=average_price_change,
        ai_recommendations_count=ai_count,
        ai_approval_rate_pct=ai_approval_rate_pct,
        low_stock_count=inventory_counts["low_stock"],
        overstock_count=inventory_counts["overstock"],
        failed_device_updates_count=metrics["device_sync_failed_count"],
        device_uptime_pct=device_uptime_pct,
        is_partial=is_partial,
        computed_at=utcnow(),
    )


def _cache_key(
    organization_id: uuid.UUID,
    date_from: dt.date,
    date_to: dt.date,
    store_id: uuid.UUID | None,
    category_id: uuid.UUID | None,
    product_id: uuid.UUID | None,
) -> str:
    parts = [
        "analytics:dashboard",
        str(organization_id),
        date_from.isoformat(),
        date_to.isoformat(),
        str(store_id) if store_id else "-",
        str(category_id) if category_id else "-",
        str(product_id) if product_id else "-",
    ]
    return ":".join(parts)


def recompute_range(
    organization_id: uuid.UUID, *, start_date: dt.date, end_date: dt.date, db: Session | None = None
) -> None:
    """Recomputes every snapshot grain (each store + the org-wide NULL row)
    for [start_date, end_date]. Callable two ways:
      - with an externally-owned `db` (the request-scoped session from the
        lazy-fill path in _compute_from_snapshots) — no commit here, the
        request boundary (app.db.session.get_db) commits.
      - with db=None (app.tasks.analytics's Celery task, or a test) — opens
        and commits its own session, mirroring
        app.services.output_job_service.process_output_job.
    """
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    try:
        _recompute_range(session, organization_id, start_date, end_date)
        if owns_session:
            session.commit()
    except Exception:
        if owns_session:
            session.rollback()
        raise
    finally:
        if owns_session:
            session.close()


def _recompute_range(db: Session, organization_id: uuid.UUID, start_date: dt.date, end_date: dt.date) -> None:
    store_ids = StoreRepository(db).list_ids_for_organization(organization_id)

    price_rows = PriceHistoryRepository(db).aggregate_by_day_and_store(
        organization_id, date_from=start_date, date_to=end_date
    )
    ai_rows = AIPricingRecommendationRepository(db).aggregate_by_day_and_store(
        organization_id, date_from=start_date, date_to=end_date
    )
    device_rows = DeviceSyncLogRepository(db).aggregate_by_day_and_store(
        organization_id, date_from=start_date, date_to=end_date
    )
    adjustment_rows = InventoryAdjustmentRepository(db).aggregate_decreases_by_day_store_product(
        organization_id, date_from=start_date, date_to=end_date
    )
    product_ids = list({product_id for _, _, product_id, _ in adjustment_rows})
    prices_by_product = ProductRepository(db).list_prices_by_ids(organization_id, product_ids)

    acc: dict[tuple[uuid.UUID | None, dt.date], dict] = defaultdict(_empty_metrics)

    # Every day gets an explicit row for every grain (org-wide + each
    # store), even with all-zero metrics — otherwise a day with zero
    # activity would look "missing" forever and get lazily recomputed on
    # every single request that touches it.
    for day in _date_range(start_date, end_date):
        acc[(None, day)]  # noqa: B018 — materializes the defaultdict entry
        for store_id in store_ids:
            acc[(store_id, day)]  # noqa: B018

    for day, store_id, count, signed_sum in price_rows:
        acc[(None, day)]["price_changes_count"] += count
        acc[(None, day)]["price_change_amount_sum"] += signed_sum
        if store_id is not None:
            acc[(store_id, day)]["price_changes_count"] += count
            acc[(store_id, day)]["price_change_amount_sum"] += signed_sum

    for day, store_id, total, approved in ai_rows:
        acc[(None, day)]["ai_recommendations_count"] += total
        acc[(None, day)]["ai_approved_count"] += approved
        if store_id is not None:
            acc[(store_id, day)]["ai_recommendations_count"] += total
            acc[(store_id, day)]["ai_approved_count"] += approved

    for day, store_id, attempts, success, failed in device_rows:
        acc[(None, day)]["device_sync_attempts_count"] += attempts
        acc[(None, day)]["device_sync_success_count"] += success
        acc[(None, day)]["device_sync_failed_count"] += failed
        acc[(store_id, day)]["device_sync_attempts_count"] += attempts
        acc[(store_id, day)]["device_sync_success_count"] += success
        acc[(store_id, day)]["device_sync_failed_count"] += failed

    for day, store_id, product_id, qty in adjustment_rows:
        selling_price, cost_price = prices_by_product.get(product_id, (Decimal("0"), None))
        revenue = qty * selling_price
        cogs = qty * (cost_price or Decimal("0"))
        acc[(None, day)]["revenue"] += revenue
        acc[(None, day)]["cogs"] += cogs
        acc[(store_id, day)]["revenue"] += revenue
        acc[(store_id, day)]["cogs"] += cogs

    AnalyticsSnapshotRepository(db).delete_range(organization_id, date_from=start_date, date_to=end_date)
    rows = [
        AnalyticsSnapshot(
            id=uuid.uuid4(),
            organization_id=organization_id,
            store_id=store_key,
            snapshot_date=day,
            **{field: metrics[field] for field in _METRIC_FIELDS},
        )
        for (store_key, day), metrics in acc.items()
    ]
    AnalyticsSnapshotRepository(db).bulk_insert(rows)


def recompute_all_organizations(db: Session | None = None) -> None:
    """The periodic (Celery beat) entry point — re-touches the last
    CATCH_UP_DAYS for every active org. app.tasks.analytics schedules this.
    """
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    try:
        today = utcnow().date()
        start_date = today - dt.timedelta(days=CATCH_UP_DAYS - 1)
        for organization_id in OrganizationRepository(session).list_active_ids():
            _recompute_range(session, organization_id, start_date, today)
        if owns_session:
            session.commit()
    except Exception:
        if owns_session:
            session.rollback()
        raise
    finally:
        if owns_session:
            session.close()


def _dispatch_recompute(organization_id: uuid.UUID, date_from: dt.date, date_to: dt.date) -> None:
    if not _broker_reachable():
        logger.warning(
            "Redis broker unreachable — analytics snapshot backfill for org %s (%s..%s) will stay "
            "pending until a worker is available.",
            organization_id,
            date_from,
            date_to,
        )
        return
    try:
        from app.tasks.analytics import recompute_analytics_task

        recompute_analytics_task.delay(str(organization_id), date_from.isoformat(), date_to.isoformat())
    except Exception:  # noqa: BLE001 — broker went away between the check and the dispatch
        logger.warning("Could not dispatch analytics recompute for org %s.", organization_id)


def _broker_reachable(timeout: float = 0.5) -> bool:
    """Deliberately-duplicated copy of output_job_service._broker_reachable,
    matching this project's established preference for independent copies
    of small infra logic over cross-module coupling.
    """
    url = urlparse(get_settings().redis_url)
    try:
        with socket.create_connection((url.hostname or "localhost", url.port or 6379), timeout=timeout):
            return True
    except OSError:
        return False
