import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin, utcnow


class DeviceAssignmentStatus(enum.StrEnum):
    ACTIVE = "active"
    ENDED = "ended"


class DeviceAssignment(UUIDPrimaryKeyMixin, Base):
    """One product shown on one device over one period of time. No
    organization_id/created_at/updated_at columns per the literal Phase 8
    spec — tenant scoping is enforced by joining through device_id to
    Device.organization_id (see DeviceAssignmentRepository), and assigned_at
    already serves as the creation timestamp.

    A device can only display one product at a time: assigning a new
    product ends any existing ACTIVE assignment for that device first (see
    DeviceAssignmentService.create_assignment).
    """

    __tablename__ = "device_assignments"

    device_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("devices.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("products.id"), nullable=False, index=True
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("stores.id"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    unassigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[DeviceAssignmentStatus] = mapped_column(
        Enum(DeviceAssignmentStatus, native_enum=False, length=20),
        nullable=False,
        default=DeviceAssignmentStatus.ACTIVE,
    )
