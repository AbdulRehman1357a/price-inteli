import enum
import uuid

from sqlalchemy import JSON, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class OutputType(enum.StrEnum):
    ESL_SIMULATOR = "esl_simulator"
    QR_CODE = "qr_code"
    PDF_LABEL = "pdf_label"
    WEB_DISPLAY = "web_display"
    # Phase 14: no live POS terminal, e-commerce platform, or digital
    # signage network is connected in this phase — same honesty pattern as
    # the ESL Simulator above (app/outputs/pos_integration.py etc. render
    # the correct payload and simulate a successful push rather than
    # claiming a real vendor connection).
    POS_INTEGRATION = "pos_integration"
    ECOMMERCE_INTEGRATION = "ecommerce_integration"
    DIGITAL_SIGNAGE = "digital_signage"


class OutputChannelStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class OutputChannel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A configured destination that product prices can be pushed/rendered
    to (a simulated ESL, a QR code, a printable label, a public web page).

    store_id is not in the literal Phase 7 DB spec, but the "Output
    Management UI" field list explicitly asks for a Store field — added as
    a nullable FK (NULL = organization-wide channel, not tied to one store),
    same precedent as Product.brand in Phase 3.
    """

    __tablename__ = "output_channels"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("stores.id"), nullable=True, index=True
    )
    # Stage 2: optional visual template applied to this channel's labels.
    # NULL = built-in defaults (rendering byte-identical to today). Deleting
    # the template detaches channels back to defaults (FK ON DELETE SET NULL).
    label_template_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False),
        ForeignKey("label_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    output_type: Mapped[OutputType] = mapped_column(
        Enum(OutputType, native_enum=False, length=30), nullable=False
    )
    configuration: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[OutputChannelStatus] = mapped_column(
        Enum(OutputChannelStatus, native_enum=False, length=20),
        nullable=False,
        default=OutputChannelStatus.ACTIVE,
    )
