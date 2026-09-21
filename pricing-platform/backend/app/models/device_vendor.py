import enum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class DeviceVendorStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class DeviceVendor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A global ESL hardware vendor (e.g. "ESL Simulator", a real vendor
    added later). Not tenant-scoped — this is shared platform catalog data,
    same pattern as the seeded system Role rows: individual tenant Device
    rows reference into this catalog via vendor_id.
    """

    __tablename__ = "device_vendors"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[DeviceVendorStatus] = mapped_column(
        Enum(DeviceVendorStatus, native_enum=False, length=20),
        nullable=False,
        default=DeviceVendorStatus.ACTIVE,
    )
