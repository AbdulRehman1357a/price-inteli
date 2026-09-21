import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin, utcnow


class DeviceSyncStatus(enum.StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class DeviceSyncLog(UUIDPrimaryKeyMixin, Base):
    """One attempt to push a price/template update to a device (the
    "ESL Adapter -> MQTT -> ESL Simulator -> Acknowledgement" step). No
    organization_id/created_at columns per the literal Phase 8 spec —
    tenant scoping joins through device_id, and attempted_at is the
    creation-equivalent timestamp.

    output_job_id is nullable: a sync can be triggered directly (a manual
    "Resync" action, or automatically when a product is assigned to a
    device) as well as, in a future integration phase, by an Output Job.
    """

    __tablename__ = "device_sync_logs"

    device_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("devices.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("products.id"), nullable=False
    )
    output_job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("output_jobs.id"), nullable=True
    )
    status: Mapped[DeviceSyncStatus] = mapped_column(
        Enum(DeviceSyncStatus, native_enum=False, length=20),
        nullable=False,
        default=DeviceSyncStatus.PENDING,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
