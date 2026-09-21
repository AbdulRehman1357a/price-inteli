import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.integration_authority import AuthoritySource
from app.models.integration_mapping import CanonicalEntityType
from app.models.mixins import UUIDPrimaryKeyMixin, utcnow


class IntegrationReconciliationStatus(enum.StrEnum):
    OPEN = "open"
    RESOLVED_PIP_KEPT = "resolved_pip_kept"
    RESOLVED_EXTERNAL_APPLIED = "resolved_external_applied"
    IGNORED = "ignored"


class IntegrationReconciliation(UUIDPrimaryKeyMixin, Base):
    """One detected PIP-vs-external mismatch
    (app.services.integration_reconciliation_service.run_reconciliation),
    or one authority-override write logged in place of being blocked
    (app.services.integration_authority_service.may_apply with
    allow_override=True). No organization_id column — tenant scoping joins
    through integration_id. No TimestampMixin — detected_at serves as
    creation time, matching IntegrationSyncJob's started_at precedent.
    """

    __tablename__ = "integration_reconciliation"

    integration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("integrations.id"), nullable=False, index=True
    )
    entity_type: Mapped[CanonicalEntityType] = mapped_column(
        Enum(CanonicalEntityType, native_enum=False, length=20), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    pip_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    authority_at_detection: Mapped[AuthoritySource] = mapped_column(
        Enum(AuthoritySource, native_enum=False, length=10), nullable=False
    )
    status: Mapped[IntegrationReconciliationStatus] = mapped_column(
        Enum(IntegrationReconciliationStatus, native_enum=False, length=30),
        nullable=False,
        default=IntegrationReconciliationStatus.OPEN,
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), nullable=True
    )
