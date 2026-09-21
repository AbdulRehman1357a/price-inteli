import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic data-access layer. Routes/services never touch SQLAlchemy directly.

    Subclasses for tenant-scoped models must override the query methods to
    filter by organization_id — see rule 21 (tenant isolation in every
    relevant query) and rule 22 (never expose another org's data).
    """

    model: type[ModelType]

    def __init__(self, db: Session):
        self.db = db

    def _not_deleted(self, stmt):
        """Filter out soft-deleted rows, for models that have a deleted_at column."""
        if hasattr(self.model, "deleted_at"):
            return stmt.where(self.model.deleted_at.is_(None))
        return stmt

    def get_by_id(self, id_: uuid.UUID) -> ModelType | None:
        stmt = self._not_deleted(select(self.model).where(self.model.id == id_))
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, *, offset: int = 0, limit: int = 20) -> list[ModelType]:
        stmt = self._not_deleted(select(self.model)).offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def add(self, instance: ModelType) -> ModelType:
        self.db.add(instance)
        self.db.flush()
        return instance

    def soft_delete(self, instance: ModelType) -> None:
        from app.models.mixins import utcnow

        instance.deleted_at = utcnow()
        self.db.flush()
