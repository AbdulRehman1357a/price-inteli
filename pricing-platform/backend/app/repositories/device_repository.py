import uuid

from sqlalchemy import func, or_, select

from app.models.device import Device, DeviceStatus
from app.repositories.base import BaseRepository


class DeviceRepository(BaseRepository[Device]):
    model = Device

    def get_by_id_for_organization(self, device_id: uuid.UUID, organization_id: uuid.UUID) -> Device | None:
        stmt = select(Device).where(Device.id == device_id, Device.organization_id == organization_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_identifier(self, organization_id: uuid.UUID, device_identifier: str) -> Device | None:
        stmt = select(Device).where(
            Device.organization_id == organization_id, Device.device_identifier == device_identifier
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def delete(self, device: Device) -> None:
        self.db.delete(device)
        self.db.flush()

    def count_by_esl_integration(self, esl_integration_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(Device).where(Device.esl_integration_id == esl_integration_id)
        return self.db.execute(stmt).scalar_one()

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        store_id: uuid.UUID | None = None,
        vendor_id: uuid.UUID | None = None,
        esl_integration_id: uuid.UUID | None = None,
        device_model_id: uuid.UUID | None = None,
        status: DeviceStatus | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Device], int]:
        conditions = [Device.organization_id == organization_id]
        if store_id is not None:
            conditions.append(Device.store_id == store_id)
        if vendor_id is not None:
            conditions.append(Device.vendor_id == vendor_id)
        if esl_integration_id is not None:
            conditions.append(Device.esl_integration_id == esl_integration_id)
        if device_model_id is not None:
            conditions.append(Device.device_model_id == device_model_id)
        if status is not None:
            conditions.append(Device.status == status)
        if search:
            like = f"%{search}%"
            conditions.append(or_(Device.device_name.ilike(like), Device.device_identifier.ilike(like)))

        base_stmt = select(Device).where(*conditions)
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(base_stmt.order_by(Device.created_at.desc()).offset(offset).limit(limit))
            .scalars()
            .all()
        )
        return items, total
