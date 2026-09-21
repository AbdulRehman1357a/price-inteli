import uuid

from sqlalchemy import func, select

from app.models.import_row_error import ImportRowError
from app.repositories.base import BaseRepository


class ImportRowErrorRepository(BaseRepository[ImportRowError]):
    model = ImportRowError

    def list_for_job(
        self, import_job_id: uuid.UUID, *, offset: int = 0, limit: int = 50
    ) -> tuple[list[ImportRowError], int]:
        base_stmt = select(ImportRowError).where(ImportRowError.import_job_id == import_job_id)

        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()

        items = list(
            self.db.execute(base_stmt.order_by(ImportRowError.row_number).offset(offset).limit(limit))
            .scalars()
            .all()
        )
        return items, total
