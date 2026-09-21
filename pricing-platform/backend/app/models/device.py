import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class DeviceStatus(enum.StrEnum):
    """Administrative lifecycle state, set by a user — distinct from the
    live connectivity status ESLVendorAdapter.get_status() derives from
    last_seen_at freshness.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class Device(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One physical (or, for now, simulated) ESL device belonging to a
    tenant and a store.
    """

    __tablename__ = "devices"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "device_identifier", name="uq_devices_organization_id_device_identifier"
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("stores.id"), nullable=False, index=True
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("device_vendors.id"), nullable=False
    )
    device_model_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("device_models.id"), nullable=False
    )
    # Not in the literal Phase 8 DB spec — added in Phase 9 so a device
    # imported through the Integration Setup Wizard's "Import Devices" step
    # (app/services/esl_integration_service.py) knows which real vendor
    # integration to route future price pushes through, instead of always
    # falling back to the built-in ESL simulator. NULL for devices created
    # directly via the Phase 8 Device Form.
    esl_integration_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("esl_integrations.id"), nullable=True
    )
    device_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus, native_enum=False, length=20), nullable=False, default=DeviceStatus.ACTIVE
    )
    # 0-100 simulated quality scores, not real hardware telemetry (no
    # physical device integration yet, per the Phase 8 spec).
    battery_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    signal_strength: Mapped[int | None] = mapped_column(Integer, nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
