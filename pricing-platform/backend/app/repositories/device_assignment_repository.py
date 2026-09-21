import uuid

from sqlalchemy import delete, func, select

from app.models.device import Device
from app.models.device_assignment import DeviceAssignment, DeviceAssignmentStatus
from app.repositories.base import BaseRepository


class DeviceAssignmentRepository(BaseRepository[DeviceAssignment]):
    """device_assignments has no organization_id column (per the literal
    Phase 8 spec) — every tenant-scoped query here joins through device_id
    to Device.organization_id instead.
    """

    model = DeviceAssignment

    def get_by_id_for_organization(
        self, assignment_id: uuid.UUID, organization_id: uuid.UUID
    ) -> DeviceAssignment | None:
        stmt = (
            select(DeviceAssignment)
            .join(Device, Device.id == DeviceAssignment.device_id)
            .where(DeviceAssignment.id == assignment_id, Device.organization_id == organization_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_active_for_device(self, device_id: uuid.UUID) -> DeviceAssignment | None:
        stmt = select(DeviceAssignment).where(
            DeviceAssignment.device_id == device_id,
            DeviceAssignment.status == DeviceAssignmentStatus.ACTIVE,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def delete_for_device(self, device_id: uuid.UUID) -> None:
        self.db.execute(delete(DeviceAssignment).where(DeviceAssignment.device_id == device_id))
        self.db.flush()

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        device_id: uuid.UUID | None = None,
        status: DeviceAssignmentStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[DeviceAssignment], int]:
        conditions = [Device.organization_id == organization_id]
        if device_id is not None:
            conditions.append(DeviceAssignment.device_id == device_id)
        if status is not None:
            conditions.append(DeviceAssignment.status == status)

        base_stmt = select(DeviceAssignment).join(Device, Device.id == DeviceAssignment.device_id).where(
            *conditions
        )
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(
                base_stmt.order_by(DeviceAssignment.assigned_at.desc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total
