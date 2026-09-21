import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.user import User
from app.schemas.label_template import (
    LabelTemplateCreate,
    LabelTemplateListOut,
    LabelTemplateOut,
    LabelTemplateUpdate,
)
from app.services import label_template_service

router = APIRouter(prefix="/outputs/label-templates", tags=["label-templates"])


@router.get("", response_model=APIResponse[list[LabelTemplateListOut]])
def list_templates(
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[LabelTemplateListOut]]:
    templates = label_template_service.list_templates(db, organization_id=current_user.organization_id)
    return APIResponse(data=[LabelTemplateListOut.model_validate(t) for t in templates])


@router.post("", response_model=APIResponse[LabelTemplateOut], status_code=status.HTTP_201_CREATED)
def create_template(
    payload: LabelTemplateCreate,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[LabelTemplateOut]:
    template = label_template_service.create_template(
        db, organization_id=current_user.organization_id, payload=payload
    )
    return APIResponse(data=LabelTemplateOut.model_validate(template))


@router.get("/{template_id}", response_model=APIResponse[LabelTemplateOut])
def get_template(
    template_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[LabelTemplateOut]:
    template = label_template_service.get_template(
        db, organization_id=current_user.organization_id, template_id=template_id
    )
    return APIResponse(data=LabelTemplateOut.model_validate(template))


@router.put("/{template_id}", response_model=APIResponse[LabelTemplateOut])
def update_template(
    template_id: uuid.UUID,
    payload: LabelTemplateUpdate,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[LabelTemplateOut]:
    template = label_template_service.update_template(
        db, organization_id=current_user.organization_id, template_id=template_id, payload=payload
    )
    return APIResponse(data=LabelTemplateOut.model_validate(template))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_UPDATE)),
    db: Session = Depends(get_db),
) -> None:
    label_template_service.delete_template(
        db, organization_id=current_user.organization_id, template_id=template_id
    )


@router.post("/{template_id}/background-image", response_model=APIResponse[LabelTemplateOut])
async def upload_background_image(
    template_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission(PermissionCode.OUTPUTS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[LabelTemplateOut]:
    content = await file.read()
    template = label_template_service.upload_background_image(
        db,
        organization_id=current_user.organization_id,
        template_id=template_id,
        filename=file.filename or "image.png",
        content=content,
    )
    return APIResponse(data=LabelTemplateOut.model_validate(template))