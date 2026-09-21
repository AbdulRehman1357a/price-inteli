import uuid

from sqlalchemy import select

from app.models.device_model import DeviceModel, DeviceModelStatus
from app.repositories.base import BaseRepository


class DeviceModelRepository(BaseRepository[DeviceModel]):
    """DeviceModel is global catalog data (no organization_id), same as
    DeviceVendor.
    """

    model = DeviceModel

    def list_active(self, *, vendor_id: uuid.UUID | None = None) -> list[DeviceModel]:
        conditions = [DeviceModel.status == DeviceModelStatus.ACTIVE]
        if vendor_id is not None:
            conditions.append(DeviceModel.vendor_id == vendor_id)
        stmt = select(DeviceModel).where(*conditions).order_by(DeviceModel.name)
        return list(self.db.execute(stmt).scalars().all())
