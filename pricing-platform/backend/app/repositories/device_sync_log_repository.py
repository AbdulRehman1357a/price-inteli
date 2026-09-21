import datetime as dt
import uuid

from sqlalchemy import case, delete, func, select

from app.models.device import Device
from app.models.device_sync_log import DeviceSyncLog, DeviceSyncStatus
from app.models.product import Product
from app.repositories.base import BaseRepository

_IS_SUCCESS = DeviceSyncLog.status == DeviceSyncStatus.SUCCESS
_IS_FAILED = DeviceSyncLog.status == DeviceSyncStatus.FAILED


class DeviceSyncLogRepository(BaseRepository[DeviceSyncLog]):
    """device_sync_logs has no organization_id column (per the literal
    Phase 8 spec) — tenant-scoped queries join through device_id to
    Device.organization_id, same as DeviceAssignmentRepository.
    """

    model = DeviceSyncLog

    def delete_for_device(self, device_id: uuid.UUID) -> None:
        self.db.execute(delete(DeviceSyncLog).where(DeviceSyncLog.device_id == device_id))
        self.db.flush()

    def search_for_device(
        self,
        *,
        device_id: uuid.UUID,
        organization_id: uuid.UUID,
        status: DeviceSyncStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[DeviceSyncLog], int]:
        conditions = [DeviceSyncLog.device_id == device_id, Device.organization_id == organization_id]
        if status is not None:
            conditions.append(DeviceSyncLog.status == status)

        base_stmt = (
            select(DeviceSyncLog).join(Device, Device.id == DeviceSyncLog.device_id).where(*conditions)
        )
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(
                base_stmt.order_by(DeviceSyncLog.attempted_at.desc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total

    def aggregate_by_day_and_store(
        self, organization_id: uuid.UUID, *, date_from: dt.date, date_to: dt.date
    ) -> list[tuple[dt.date, uuid.UUID, int, int, int]]:
        """(day, store_id, attempts, success_count, failed_count) for every
        day/store in range — pre-aggregation source for
        AnalyticsSnapshot.device_sync_*_count (Failed Device Updates /
        Device Uptime). Joins Device for organization_id/store_id since
        device_sync_logs carries neither column itself.
        """
        day_col = func.date(DeviceSyncLog.attempted_at)
        success_count = func.sum(case((_IS_SUCCESS, 1), else_=0))
        failed_count = func.sum(case((_IS_FAILED, 1), else_=0))
        stmt = (
            select(day_col, Device.store_id, func.count(), success_count, failed_count)
            .join(Device, Device.id == DeviceSyncLog.device_id)
            .where(
                Device.organization_id == organization_id,
                DeviceSyncLog.attempted_at >= date_from,
                DeviceSyncLog.attempted_at < date_to + dt.timedelta(days=1),
            )
            .group_by(day_col, Device.store_id)
        )
        return [
            (_as_date(day), store_id, attempts, success or 0, failed or 0)
            for day, store_id, attempts, success, failed in self.db.execute(stmt).all()
        ]

    def totals_for_filters(
        self,
        organization_id: uuid.UUID,
        *,
        date_from: dt.date,
        date_to: dt.date,
        store_id: uuid.UUID | None,
        category_id: uuid.UUID | None,
        product_id: uuid.UUID | None,
    ) -> tuple[int, int, int]:
        """(attempts, success_count, failed_count) over the whole range for
        a category/product filtered (live) dashboard request.
        """
        conditions = [
            Device.organization_id == organization_id,
            DeviceSyncLog.attempted_at >= date_from,
            DeviceSyncLog.attempted_at < date_to + dt.timedelta(days=1),
        ]
        if store_id is not None:
            conditions.append(Device.store_id == store_id)
        if product_id is not None:
            conditions.append(DeviceSyncLog.product_id == product_id)
        if category_id is not None:
            conditions.append(
                DeviceSyncLog.product_id.in_(select(Product.id).where(Product.category_id == category_id))
            )

        success_count = func.sum(case((_IS_SUCCESS, 1), else_=0))
        failed_count = func.sum(case((_IS_FAILED, 1), else_=0))
        stmt = (
            select(func.count(), success_count, failed_count)
            .join(Device, Device.id == DeviceSyncLog.device_id)
            .where(*conditions)
        )
        attempts, success, failed = self.db.execute(stmt).one()
        return attempts, success or 0, failed or 0


def _as_date(value) -> dt.date:
    return value if isinstance(value, dt.date) else dt.date.fromisoformat(str(value))
