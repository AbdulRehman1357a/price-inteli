import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import delete, func, select

from app.models.analytics_snapshot import AnalyticsSnapshot
from app.repositories.base import BaseRepository


def _store_condition(store_id: uuid.UUID | None):
    if store_id is None:
        return AnalyticsSnapshot.store_id.is_(None)
    return AnalyticsSnapshot.store_id == store_id


class AnalyticsSnapshotRepository(BaseRepository[AnalyticsSnapshot]):
    model = AnalyticsSnapshot

    def delete_range(
        self, organization_id: uuid.UUID, *, date_from: dt.date, date_to: dt.date
    ) -> None:
        """Wipes every snapshot row (every store + the org-wide NULL row)
        for this org/date range so analytics_service.recompute_range can
        do a clean delete-then-insert — the simplest way to keep a
        recompute idempotent without a DB-level uniqueness constraint.
        """
        stmt = delete(AnalyticsSnapshot).where(
            AnalyticsSnapshot.organization_id == organization_id,
            AnalyticsSnapshot.snapshot_date >= date_from,
            AnalyticsSnapshot.snapshot_date <= date_to,
        )
        self.db.execute(stmt)

    def bulk_insert(self, rows: list[AnalyticsSnapshot]) -> None:
        if not rows:
            return
        self.db.add_all(rows)
        self.db.flush()

    def existing_dates(
        self, organization_id: uuid.UUID, *, store_id: uuid.UUID | None, date_from: dt.date, date_to: dt.date
    ) -> set[dt.date]:
        """Which days already have a snapshot row for this exact grain
        (store_id or the NULL org-wide row) — used to find gaps to fill.
        """
        stmt = select(AnalyticsSnapshot.snapshot_date).where(
            AnalyticsSnapshot.organization_id == organization_id,
            _store_condition(store_id),
            AnalyticsSnapshot.snapshot_date >= date_from,
            AnalyticsSnapshot.snapshot_date <= date_to,
        )
        return set(self.db.execute(stmt).scalars().all())

    def aggregate(
        self, organization_id: uuid.UUID, *, store_id: uuid.UUID | None, date_from: dt.date, date_to: dt.date
    ) -> dict:
        """Sums every raw counter/amount column across the date range for
        one grain (a specific store, or NULL for the org-wide rollup) — the
        cheap read path once snapshot rows exist, regardless of how wide
        the date range is (it's summing pre-aggregated daily rows, not
        re-scanning source tables).
        """
        stmt = select(
            func.coalesce(func.sum(AnalyticsSnapshot.revenue), 0),
            func.coalesce(func.sum(AnalyticsSnapshot.cogs), 0),
            func.coalesce(func.sum(AnalyticsSnapshot.price_changes_count), 0),
            func.coalesce(func.sum(AnalyticsSnapshot.price_change_amount_sum), 0),
            func.coalesce(func.sum(AnalyticsSnapshot.ai_recommendations_count), 0),
            func.coalesce(func.sum(AnalyticsSnapshot.ai_approved_count), 0),
            func.coalesce(func.sum(AnalyticsSnapshot.device_sync_attempts_count), 0),
            func.coalesce(func.sum(AnalyticsSnapshot.device_sync_success_count), 0),
            func.coalesce(func.sum(AnalyticsSnapshot.device_sync_failed_count), 0),
        ).where(
            AnalyticsSnapshot.organization_id == organization_id,
            _store_condition(store_id),
            AnalyticsSnapshot.snapshot_date >= date_from,
            AnalyticsSnapshot.snapshot_date <= date_to,
        )
        row = self.db.execute(stmt).one()
        keys = [
            "revenue",
            "cogs",
            "price_changes_count",
            "price_change_amount_sum",
            "ai_recommendations_count",
            "ai_approved_count",
            "device_sync_attempts_count",
            "device_sync_success_count",
            "device_sync_failed_count",
        ]
        result = dict(zip(keys, row, strict=True))
        for money_key in ("revenue", "cogs", "price_change_amount_sum"):
            result[money_key] = Decimal(result[money_key])
        return result
