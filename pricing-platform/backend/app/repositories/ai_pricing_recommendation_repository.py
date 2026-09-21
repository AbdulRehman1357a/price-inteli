import datetime as dt
import uuid

from sqlalchemy import case, func, select

from app.models.ai_pricing_recommendation import AIPricingRecommendation, RecommendationStatus
from app.models.product import Product
from app.repositories.base import BaseRepository

_APPROVED_OR_APPLIED = AIPricingRecommendation.status.in_(
    [RecommendationStatus.APPROVED, RecommendationStatus.APPLIED]
)


class AIPricingRecommendationRepository(BaseRepository[AIPricingRecommendation]):
    model = AIPricingRecommendation

    def get_by_id_for_organization(
        self, recommendation_id: uuid.UUID, organization_id: uuid.UUID
    ) -> AIPricingRecommendation | None:
        stmt = select(AIPricingRecommendation).where(
            AIPricingRecommendation.id == recommendation_id,
            AIPricingRecommendation.organization_id == organization_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        status: RecommendationStatus | None = None,
        product_id: uuid.UUID | None = None,
        store_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[AIPricingRecommendation], int]:
        conditions = [AIPricingRecommendation.organization_id == organization_id]
        if status is not None:
            conditions.append(AIPricingRecommendation.status == status)
        if product_id is not None:
            conditions.append(AIPricingRecommendation.product_id == product_id)
        if store_id is not None:
            conditions.append(AIPricingRecommendation.store_id == store_id)

        base_stmt = select(AIPricingRecommendation).where(*conditions)
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(
                base_stmt.order_by(AIPricingRecommendation.created_at.desc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total

    def status_counts(self, organization_id: uuid.UUID) -> dict[str, int]:
        stmt = (
            select(AIPricingRecommendation.status, func.count())
            .where(AIPricingRecommendation.organization_id == organization_id)
            .group_by(AIPricingRecommendation.status)
        )
        counts = {status.value: 0 for status in RecommendationStatus}
        for status, count in self.db.execute(stmt).all():
            counts[status.value] = count
        return counts

    def list_pending(self, organization_id: uuid.UUID) -> list[AIPricingRecommendation]:
        stmt = select(AIPricingRecommendation).where(
            AIPricingRecommendation.organization_id == organization_id,
            AIPricingRecommendation.status == RecommendationStatus.PENDING,
        )
        return list(self.db.execute(stmt).scalars().all())

    def aggregate_by_day_and_store(
        self, organization_id: uuid.UUID, *, date_from: dt.date, date_to: dt.date
    ) -> list[tuple[dt.date, uuid.UUID | None, int, int]]:
        """(day, store_id, total_count, approved_or_applied_count) for every
        day/store a recommendation was CREATED in range — pre-aggregation
        source for AnalyticsSnapshot.ai_recommendations_count /
        ai_approved_count. status is read as of recompute time, so a
        recommendation reviewed days after creation only shows up correctly
        once its creation day's snapshot is recomputed again (the periodic
        beat task re-touches the last few days for exactly this reason).
        """
        day_col = func.date(AIPricingRecommendation.created_at)
        approved_count = func.sum(case((_APPROVED_OR_APPLIED, 1), else_=0))
        stmt = (
            select(day_col, AIPricingRecommendation.store_id, func.count(), approved_count)
            .where(
                AIPricingRecommendation.organization_id == organization_id,
                AIPricingRecommendation.created_at >= date_from,
                AIPricingRecommendation.created_at < date_to + dt.timedelta(days=1),
            )
            .group_by(day_col, AIPricingRecommendation.store_id)
        )
        return [
            (_as_date(day), store_id, total, approved or 0)
            for day, store_id, total, approved in self.db.execute(stmt).all()
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
    ) -> tuple[int, int]:
        """(total_count, approved_or_applied_count) over the whole range for
        a category/product filtered (live) dashboard request.
        """
        conditions = [
            AIPricingRecommendation.organization_id == organization_id,
            AIPricingRecommendation.created_at >= date_from,
            AIPricingRecommendation.created_at < date_to + dt.timedelta(days=1),
        ]
        if store_id is not None:
            conditions.append(AIPricingRecommendation.store_id == store_id)
        if product_id is not None:
            conditions.append(AIPricingRecommendation.product_id == product_id)
        if category_id is not None:
            conditions.append(
                AIPricingRecommendation.product_id.in_(
                    select(Product.id).where(Product.category_id == category_id)
                )
            )

        approved_count = func.sum(case((_APPROVED_OR_APPLIED, 1), else_=0))
        stmt = select(func.count(), approved_count).where(*conditions)
        total, approved = self.db.execute(stmt).one()
        return total, approved or 0


def _as_date(value) -> dt.date:
    return value if isinstance(value, dt.date) else dt.date.fromisoformat(str(value))
