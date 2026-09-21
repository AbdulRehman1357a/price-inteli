import uuid
from datetime import datetime

from sqlalchemy import and_, func, or_, select

from app.models.pricing_rule import PricingRule, RuleStatus, RuleType
from app.repositories.base import BaseRepository


class PricingRuleRepository(BaseRepository[PricingRule]):
    model = PricingRule

    def get_by_id_for_organization(
        self, rule_id: uuid.UUID, organization_id: uuid.UUID
    ) -> PricingRule | None:
        stmt = select(PricingRule).where(
            PricingRule.id == rule_id, PricingRule.organization_id == organization_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_in_force(
        self, organization_id: uuid.UUID, *, now: datetime, include_rule_id: uuid.UUID | None = None
    ) -> list[PricingRule]:
        """ACTIVE rules whose effective window covers `now`, in priority
        order (ascending — lower priority number runs first). If
        include_rule_id is given, that rule is included even if it's DRAFT
        or outside its window — lets POST /pricing/rules/{id}/test preview
        a not-yet-active rule alongside everything currently in force.
        """
        in_force = and_(
            PricingRule.status == RuleStatus.ACTIVE,
            or_(PricingRule.effective_from.is_(None), PricingRule.effective_from <= now),
            or_(PricingRule.effective_to.is_(None), PricingRule.effective_to >= now),
        )
        match_condition = or_(in_force, PricingRule.id == include_rule_id) if include_rule_id else in_force

        stmt = select(PricingRule).where(PricingRule.organization_id == organization_id, match_condition)
        return list(self.db.execute(stmt.order_by(PricingRule.priority.asc())).scalars().all())

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        rule_type: RuleType | None = None,
        status: RuleStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[PricingRule], int]:
        conditions = [PricingRule.organization_id == organization_id]
        if rule_type is not None:
            conditions.append(PricingRule.rule_type == rule_type)
        if status is not None:
            conditions.append(PricingRule.status == status)

        base_stmt = select(PricingRule).where(*conditions)
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(
                base_stmt.order_by(PricingRule.priority.asc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total
