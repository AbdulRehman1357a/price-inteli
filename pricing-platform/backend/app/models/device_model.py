import enum
import uuid

from sqlalchemy import JSON, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class DeviceModelStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class DeviceModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A specific hardware model offered by a DeviceVendor (e.g. a 2.9in
    simulator display). Global catalog data, same as DeviceVendor.
    """

    __tablename__ = "device_models"

    vendor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=False), ForeignKey("device_vendors.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_code: Mapped[str] = mapped_column(String(100), nullable=False)
    screen_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color_capabilities: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    battery_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    communication_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[DeviceModelStatus] = mapped_column(
        Enum(DeviceModelStatus, native_enum=False, length=20),
        nullable=False,
        default=DeviceModelStatus.ACTIVE,
    )
