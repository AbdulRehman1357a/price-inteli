import uuid

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.label_template import LabelTemplate
from app.repositories.label_template_repository import LabelTemplateRepository
from app.schemas.label_template import LabelTemplateCreate, LabelTemplateUpdate
from app.storage import get_storage_adapter


def create_template(
    db: Session, *, organization_id: uuid.UUID, payload: LabelTemplateCreate
) -> LabelTemplate:
    return LabelTemplateRepository(db).add(
        LabelTemplate(
            id=uuid.uuid4(),
            organization_id=organization_id,
            name=payload.name,
            colors=payload.colors,
            background_image_url=payload.background_image_url,
        )
    )


def get_template(db: Session, *, organization_id: uuid.UUID, template_id: uuid.UUID) -> LabelTemplate:
    template = LabelTemplateRepository(db).get_by_id_for_organization(template_id, organization_id)
    if template is None:
        raise NotFoundError("Label template not found.", code="label_template_not_found")
    return template


def list_templates(db: Session, *, organization_id: uuid.UUID) -> list[LabelTemplate]:
    return LabelTemplateRepository(db).list_by_organization(organization_id)


def update_template(
    db: Session, *, organization_id: uuid.UUID, template_id: uuid.UUID, payload: LabelTemplateUpdate
) -> LabelTemplate:
    template = get_template(db, organization_id=organization_id, template_id=template_id)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        template.name = data["name"]
    if "colors" in data:
        template.colors = data["colors"]
    if "background_image_url" in data:
        template.background_image_url = data["background_image_url"]
    return LabelTemplateRepository(db).add(template)


def delete_template(db: Session, *, organization_id: uuid.UUID, template_id: uuid.UUID) -> None:
    template = get_template(db, organization_id=organization_id, template_id=template_id)
    # Channels referencing this template detach back to built-in defaults
    # (FK is ON DELETE SET NULL), so hard-delete is safe.
    db.delete(template)
    db.flush()


def upload_background_image(
    db: Session, *, organization_id: uuid.UUID, template_id: uuid.UUID, filename: str, content: bytes
) -> LabelTemplate:
    template = get_template(db, organization_id=organization_id, template_id=template_id)
    settings = get_settings()
    max_bytes = settings.max_import_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise ValidationError(f"File exceeds the {settings.max_import_file_size_mb} MB limit.")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed = {"png", "jpg", "jpeg", "gif", "webp"}
    if ext not in allowed:
        raise ValidationError(f"Unsupported image type '.{ext}'. Use one of: {', '.join(sorted(allowed))}.")

    content_type = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
    }[ext]

    key = f"label-templates/{organization_id}/{uuid.uuid4()}_{filename}"
    file_url = get_storage_adapter().upload(key=key, content=content, content_type=content_type)
    template.background_image_url = file_url
    return LabelTemplateRepository(db).add(template)
