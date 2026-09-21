import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class AnalyticsSnapshot(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One pre-aggregated day of Phase 15 dashboard metrics for one
    organization, optionally scoped to one store.

    Grain: (organization_id, store_id, snapshot_date). store_id NULL means
    "all stores" — a genuine org-wide rollup computed by its own query
    (app.services.analytics_service), not a sum of the per-store rows,
    since some source rows (e.g. an org-wide PriceHistory/AIPricingRecommendation
    entry with store_id NULL) aren't attributable to any single store.

    Only counts/sums are stored here, never a pre-divided rate/percentage —
    a percentage computed per day cannot be correctly averaged across a
    multi-day date range (days with different denominators), so callers
    must sum the raw numerator/denominator columns across the requested
    range first and divide once, at read time
    (app.services.analytics_service._to_metrics_out).

    Deliberately excludes Low Stock / Overstock: those are current-state
    inventory gauges (not a flow of events over a day) and are already
    served cheaply and correctly-filtered by the existing
    InventoryRepository.summary_counts() query — pre-aggregating a second,
    date-bucketed copy of a "right now" count would just make it stale.

    No unique DB constraint on the grain: app.services.analytics_service
    always recomputes a whole date range by deleting then re-inserting
    (see AnalyticsSnapshotRepository.delete_range/bulk_insert), so
    uniqueness is an application invariant, not a DB one.
    """

    __tablename__ = "analytics_snapshots"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("stores.id"), nullable=True, index=True
    )
    snapshot_date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)

    # Revenue / gross margin — proxied from InventoryAdjustment(decrease) as
    # the closest available "units sold" signal (this platform has no
    # Orders/POS-transaction module — same documented heuristic as
    # app.services.sales_velocity), valued at each product's CURRENT
    # catalog price/cost (Product.selling_price/cost_price) rather than a
    # historical price-at-time-of-sale, which this platform doesn't track.
    revenue: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=Decimal("0"))
    cogs: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=Decimal("0"))

    # Price changes — from PriceHistory. price_change_amount_sum is signed
    # (new_price - old_price), so Average Price Change reflects trend
    # direction, not just magnitude; rows with no prior price (old_price
    # IS NULL, i.e. a brand-new Price) aren't a "change" and are excluded
    # from both columns.
    price_changes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price_change_amount_sum: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, default=Decimal("0")
    )

    # AI recommendations created that day, and how many of those are
    # currently approved or applied (AIPricingRecommendation.status can
    # keep changing after creation via human review, which is exactly why
    # the periodic recompute re-touches the last few days, not just "today").
    ai_recommendations_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_approved_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Device sync attempts (DeviceSyncLog.attempted_at that day). "Device
    # Uptime" = success / attempts; "Failed Device Updates" = failed.
    device_sync_attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    device_sync_success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    device_sync_failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
