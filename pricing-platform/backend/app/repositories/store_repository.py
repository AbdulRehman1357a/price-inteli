import uuid

from sqlalchemy import func, or_, select

from app.models.store import Store, StoreStatus
from app.repositories.base import BaseRepository


class StoreRepository(BaseRepository[Store]):
    model = Store

    def get_by_id_for_organization(self, store_id: uuid.UUID, organization_id: uuid.UUID) -> Store | None:
        stmt = self._not_deleted(
            select(Store).where(Store.id == store_id, Store.organization_id == organization_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_ids_for_organization(self, organization_id: uuid.UUID) -> list[uuid.UUID]:
        """Every non-deleted store id for an org — used by
        analytics_service to recompute a per-store snapshot row for each
        actual store, regardless of status (a now-inactive store's history
        still matters for past-dated dashboard ranges).
        """
        stmt = self._not_deleted(select(Store.id).where(Store.organization_id == organization_id))
        return list(self.db.execute(stmt).scalars().all())

    def get_by_code(self, organization_id: uuid.UUID, store_code: str) -> Store | None:
        stmt = self._not_deleted(
            select(Store).where(Store.organization_id == organization_id, Store.store_code == store_code)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        search: str | None = None,
        status: StoreStatus | None = None,
        store_type: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Store], int]:
        conditions = [Store.organization_id == organization_id]
        if status is not None:
            conditions.append(Store.status == status)
        if store_type:
            conditions.append(Store.store_type == store_type)
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(Store.store_code.ilike(pattern), Store.name.ilike(pattern), Store.city.ilike(pattern))
            )

        base_stmt = self._not_deleted(select(Store).where(*conditions))

        total = self.db.execute(
            select(func.count()).select_from(base_stmt.order_by(None).subquery())
        ).scalar_one()

        items = list(
            self.db.execute(base_stmt.order_by(Store.created_at.desc()).offset(offset).limit(limit))
            .scalars()
            .all()
        )
        return items, total
