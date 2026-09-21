import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.user import User
from app.schemas.analytics import DashboardMetricsOut, DashboardQueryParams
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=APIResponse[DashboardMetricsOut])
def get_dashboard(
    date_from: date | None = None,
    date_to: date | None = None,
    store_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
    current_user: User = Depends(require_permission(PermissionCode.ANALYTICS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[DashboardMetricsOut]:
    """Backs every Phase 15 dashboard page (Executive/Pricing/Inventory/AI/
    Device) — each page requests the same full metrics set and renders
    only the cards relevant to it.
    """
    params = DashboardQueryParams(
        date_from=date_from,
        date_to=date_to,
        store_id=store_id,
        category_id=category_id,
        product_id=product_id,
    )
    metrics = analytics_service.get_dashboard_metrics(
        db, organization_id=current_user.organization_id, params=params
    )
    return APIResponse(data=metrics)
