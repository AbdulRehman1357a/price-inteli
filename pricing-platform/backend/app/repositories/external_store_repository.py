import uuid

from sqlalchemy import select

from app.models.external_store import ExternalStore
from app.repositories.base import BaseRepository


class ExternalStoreRepository(BaseRepository[ExternalStore]):
    model = ExternalStore

    def get_by_external_id(self, integration_id: uuid.UUID, external_id: str) -> ExternalStore | None:
        stmt = select(ExternalStore).where(
            ExternalStore.integration_id == integration_id, ExternalStore.external_id == external_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_integration(self, integration_id: uuid.UUID) -> list[ExternalStore]:
        stmt = select(ExternalStore).where(ExternalStore.integration_id == integration_id)
        return list(self.db.execute(stmt).scalars().all())
