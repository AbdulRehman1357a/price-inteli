import uuid

from sqlalchemy import func, select

from app.models.output_routing_rule import OutputRoutingRule, RoutingRuleStatus
from app.repositories.base import BaseRepository


class OutputRoutingRuleRepository(BaseRepository[OutputRoutingRule]):
    model = OutputRoutingRule

    def get_by_id_for_organization(
        self, rule_id: uuid.UUID, organization_id: uuid.UUID
    ) -> OutputRoutingRule | None:
        stmt = select(OutputRoutingRule).where(
            OutputRoutingRule.id == rule_id, OutputRoutingRule.organization_id == organization_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        status: RoutingRuleStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[OutputRoutingRule], int]:
        conditions = [OutputRoutingRule.organization_id == organization_id]
        if status is not None:
            conditions.append(OutputRoutingRule.status == status)

        base_stmt = select(OutputRoutingRule).where(*conditions)
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(
                base_stmt.order_by(OutputRoutingRule.priority.asc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total

    def list_in_force(self, organization_id: uuid.UUID) -> list[OutputRoutingRule]:
        """ACTIVE rules in priority order (ascending — lower number runs
        first), mirroring PricingRuleRepository.list_in_force.
        """
        stmt = select(OutputRoutingRule).where(
            OutputRoutingRule.organization_id == organization_id,
            OutputRoutingRule.status == RoutingRuleStatus.ACTIVE,
        )
        return list(self.db.execute(stmt.order_by(OutputRoutingRule.priority.asc())).scalars().all())
