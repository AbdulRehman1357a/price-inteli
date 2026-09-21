import uuid

from sqlalchemy import select

from app.models.label_template import LabelTemplate
from app.repositories.base import BaseRepository


class LabelTemplateRepository(BaseRepository[LabelTemplate]):
    model = LabelTemplate

    def get_by_id_for_organization(
        self, template_id: uuid.UUID, organization_id: uuid.UUID
    ) -> LabelTemplate | None:
        stmt = select(LabelTemplate).where(
            LabelTemplate.id == template_id, LabelTemplate.organization_id == organization_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_organization(self, organization_id: uuid.UUID) -> list[LabelTemplate]:
        stmt = (
            select(LabelTemplate)
            .where(LabelTemplate.organization_id == organization_id)
            .order_by(LabelTemplate.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())
