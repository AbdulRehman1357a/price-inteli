import base64
import math
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.import_job import ImportEntityType
from app.models.user import User
from app.schemas.common import PaginationMeta
from app.schemas.import_job import (
    ImportJobOut,
    ImportMappingRequest,
    ImportRowErrorListParams,
    ImportRowErrorOut,
    ImportTemplateOut,
)
from app.services import import_service

router = APIRouter(prefix="/imports", tags=["imports"])

_XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# Registered before /{import_job_id} — "templates" would otherwise be
# swallowed by that parameterized route and fail UUID parsing.
@router.get("/templates/{entity_type}", response_model=APIResponse[ImportTemplateOut])
def get_import_template(
    entity_type: ImportEntityType,
    current_user: User = Depends(require_permission(PermissionCode.IMPORTS_CREATE)),
) -> APIResponse[ImportTemplateOut]:
    filename, content = import_service.build_import_template(entity_type)
    return APIResponse(
        data=ImportTemplateOut(
            filename=filename,
            content_type=_XLSX_CONTENT_TYPE,
            content_base64=base64.b64encode(content).decode("ascii"),
        )
    )


@router.post("", response_model=APIResponse[ImportJobOut], status_code=status.HTTP_201_CREATED)
async def create_import(
    file: UploadFile = File(...),
    entity_type: ImportEntityType = Form(...),
    store_id: uuid.UUID | None = Form(None),
    current_user: User = Depends(require_permission(PermissionCode.IMPORTS_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[ImportJobOut]:
    settings = get_settings()
    content = await file.read()
    max_bytes = settings.max_import_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise ValidationError(f"File exceeds the {settings.max_import_file_size_mb} MB limit.")

    job = import_service.create_import_job(
        db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        filename=file.filename or "upload",
        content=content,
        entity_type=entity_type,
        store_id=store_id,
    )
    return APIResponse(data=ImportJobOut.model_validate(job))


@router.post("/{import_job_id}/start", response_model=APIResponse[ImportJobOut])
def start_import(
    import_job_id: uuid.UUID,
    payload: ImportMappingRequest,
    current_user: User = Depends(require_permission(PermissionCode.IMPORTS_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[ImportJobOut]:
    job = import_service.start_import(
        db, organization_id=current_user.organization_id, import_job_id=import_job_id, payload=payload
    )
    return APIResponse(data=ImportJobOut.model_validate(job))


@router.get("/{import_job_id}", response_model=APIResponse[ImportJobOut])
def get_import(
    import_job_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.IMPORTS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[ImportJobOut]:
    job = import_service.get_import_job(
        db, organization_id=current_user.organization_id, import_job_id=import_job_id
    )
    return APIResponse(data=ImportJobOut.model_validate(job))


@router.get("/{import_job_id}/errors", response_model=APIResponse[list[ImportRowErrorOut]])
def list_import_errors(
    import_job_id: uuid.UUID,
    params: ImportRowErrorListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.IMPORTS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[ImportRowErrorOut]]:
    items, total = import_service.list_row_errors(
        db, organization_id=current_user.organization_id, import_job_id=import_job_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[ImportRowErrorOut.model_validate(e) for e in items], meta=meta.model_dump())
