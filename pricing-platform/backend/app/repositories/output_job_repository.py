import uuid

from sqlalchemy import func, select

from app.models.output_job import OutputJob, OutputJobStatus
from app.repositories.base import BaseRepository


class OutputJobRepository(BaseRepository[OutputJob]):
    model = OutputJob

    def get_by_id_for_organization(self, job_id: uuid.UUID, organization_id: uuid.UUID) -> OutputJob | None:
        stmt = select(OutputJob).where(OutputJob.id == job_id, OutputJob.organization_id == organization_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_idempotency_key(
        self, organization_id: uuid.UUID, idempotency_key: str
    ) -> OutputJob | None:
        stmt = select(OutputJob).where(
            OutputJob.organization_id == organization_id, OutputJob.idempotency_key == idempotency_key
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def status_counts(self, organization_id: uuid.UUID) -> dict[OutputJobStatus, int]:
        stmt = (
            select(OutputJob.status, func.count())
            .where(OutputJob.organization_id == organization_id)
            .group_by(OutputJob.status)
        )
        return {status: count for status, count in self.db.execute(stmt).all()}

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        output_channel_id: uuid.UUID | None = None,
        product_id: uuid.UUID | None = None,
        store_id: uuid.UUID | None = None,
        status: OutputJobStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[OutputJob], int]:
        conditions = [OutputJob.organization_id == organization_id]
        if output_channel_id is not None:
            conditions.append(OutputJob.output_channel_id == output_channel_id)
        if product_id is not None:
            conditions.append(OutputJob.product_id == product_id)
        if store_id is not None:
            conditions.append(OutputJob.store_id == store_id)
        if status is not None:
            conditions.append(OutputJob.status == status)

        base_stmt = select(OutputJob).where(*conditions)
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(base_stmt.order_by(OutputJob.created_at.desc()).offset(offset).limit(limit))
            .scalars()
            .all()
        )
        return items, total
