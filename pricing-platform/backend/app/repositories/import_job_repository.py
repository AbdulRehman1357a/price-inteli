import uuid

from sqlalchemy import select

from app.models.import_job import ImportJob
from app.repositories.base import BaseRepository


class ImportJobRepository(BaseRepository[ImportJob]):
    model = ImportJob

    def get_by_id_for_organization(
        self, import_job_id: uuid.UUID, organization_id: uuid.UUID
    ) -> ImportJob | None:
        stmt = select(ImportJob).where(
            ImportJob.id == import_job_id, ImportJob.organization_id == organization_id
        )
        return self.db.execute(stmt).scalar_one_or_none()
