import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CompetitorStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Competitor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A tracked competitor for one organization. updated_at (via
    TimestampMixin) isn't in the literal Phase 13 column list but is
    required — name/website/status are all editable via the Competitor
    Management UI, same precedent as AIPricingRecommendation/AIAgent.
    """

    __tablename__ = "competitors"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[CompetitorStatus] = mapped_column(
        Enum(CompetitorStatus, native_enum=False, length=20), nullable=False, default=CompetitorStatus.ACTIVE
    )
