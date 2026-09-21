import uuid

from sqlalchemy import select

from app.models.external_promotion import ExternalPromotion
from app.repositories.base import BaseRepository


class ExternalPromotionRepository(BaseRepository[ExternalPromotion]):
    model = ExternalPromotion

    def get_by_external_promotion_id(
        self, integration_id: uuid.UUID, external_promotion_id: str
    ) -> ExternalPromotion | None:
        stmt = select(ExternalPromotion).where(
            ExternalPromotion.integration_id == integration_id,
            ExternalPromotion.external_promotion_id == external_promotion_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()
