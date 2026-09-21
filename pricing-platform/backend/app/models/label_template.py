import uuid

from sqlalchemy import JSON, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class LabelTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A reusable, org-scoped set of shelf-label visual overrides (colors +
    optional background image). An OutputChannel points at one via the
    nullable label_template_id FK; NULL means the adapter's built-in
    defaults (today's behavior).

    colors is a flat dict of the adapter's color keys (e.g. background,
    border, text, banner) → hex strings. background_image_url is an opaque
    storage reference returned by ObjectStorageAdapter.upload().

    Deliberately extensible for a later full template-builder stage: fonts,
    layout, and spacing become additional columns here (and matching
    optional fields on OutputRenderContext) without touching the adapter
    signature — the adapter already reads a resolved colors dict + image
    URL carried in the render context, never the DB.
    """

    __tablename__ = "label_templates"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    colors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    background_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
