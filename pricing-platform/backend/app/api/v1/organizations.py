from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.user import User
from app.schemas.organization import OrganizationOut, OrganizationUpdate
from app.services import organization_service

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.put("/me", response_model=APIResponse[OrganizationOut])
def update_my_organization(
    payload: OrganizationUpdate,
    current_user: User = Depends(require_permission(PermissionCode.ORGANIZATIONS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[OrganizationOut]:
    organization = organization_service.update_organization(
        db, organization_id=current_user.organization_id, payload=payload
    )
    return APIResponse(data=OrganizationOut.model_validate(organization))
