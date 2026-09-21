from sqlalchemy import select

from app.models.device_vendor import DeviceVendor, DeviceVendorStatus
from app.repositories.base import BaseRepository


class DeviceVendorRepository(BaseRepository[DeviceVendor]):
    """DeviceVendor is global catalog data (no organization_id) — every
    method here is intentionally unscoped by tenant. get_by_id() (unscoped)
    is inherited as-is from BaseRepository.
    """

    model = DeviceVendor

    def get_by_code(self, code: str) -> DeviceVendor | None:
        stmt = select(DeviceVendor).where(DeviceVendor.code == code)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_active(self) -> list[DeviceVendor]:
        stmt = select(DeviceVendor).where(DeviceVendor.status == DeviceVendorStatus.ACTIVE)
        return list(self.db.execute(stmt.order_by(DeviceVendor.name)).scalars().all())
