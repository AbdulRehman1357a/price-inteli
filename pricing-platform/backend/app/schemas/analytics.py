import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DashboardQueryParams(BaseModel):
    """Phase 15 filters. date_from/date_to default to the trailing 30 days
    (resolved in app.services.analytics_service, not here, since "today"
    isn't knowable in a Pydantic default). Organization is deliberately not
    a field — this app is single-tenant-per-login (every route is already
    scoped to current_user.organization_id), so there's nothing to filter.
    """

    date_from: date | None = None
    date_to: date | None = None
    store_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None


class DashboardMetricsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date_from: date
    date_to: date
    store_id: uuid.UUID | None
    category_id: uuid.UUID | None
    product_id: uuid.UUID | None

    revenue: Decimal
    gross_margin_amount: Decimal
    gross_margin_pct: Decimal | None

    price_changes_count: int
    average_price_change: Decimal | None

    ai_recommendations_count: int
    ai_approval_rate_pct: Decimal | None

    low_stock_count: int
    overstock_count: int

    failed_device_updates_count: int
    device_uptime_pct: Decimal | None

    # True when the requested range included more not-yet-computed days
    # than analytics_service is willing to compute inline on this request —
    # the missing days were enqueued as a background job instead
    # (app.tasks.analytics) and are reported here as zero until it runs.
    is_partial: bool
    computed_at: datetime
