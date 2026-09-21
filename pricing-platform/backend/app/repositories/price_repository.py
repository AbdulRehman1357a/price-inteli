import uuid
from datetime import datetime

from sqlalchemy import func, or_, select

from app.models.price import Price, PriceStatus, PriceType
from app.repositories.base import BaseRepository


class PriceRepository(BaseRepository[Price]):
    model = Price

    def get_by_id_for_organization(self, price_id: uuid.UUID, organization_id: uuid.UUID) -> Price | None:
        stmt = select(Price).where(Price.id == price_id, Price.organization_id == organization_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_current_effective(
        self, organization_id: uuid.UUID, *, product_id: uuid.UUID, store_id: uuid.UUID | None, now: datetime
    ) -> Price | None:
        """The Price row in effect right now for this product — a
        store-specific price if one exists, otherwise the org-wide
        (store_id IS NULL) price. Used as the "Current Price" starting
        point for rule evaluation.
        """
        conditions = [
            Price.organization_id == organization_id,
            Price.product_id == product_id,
            Price.status == PriceStatus.ACTIVE,
            Price.effective_from <= now,
            or_(Price.effective_to.is_(None), Price.effective_to >= now),
        ]
        if store_id is not None:
            store_specific = select(Price).where(*conditions, Price.store_id == store_id)
            found = self.db.execute(store_specific.order_by(Price.effective_from.desc())).scalars().first()
            if found is not None:
                return found

        org_wide = select(Price).where(*conditions, Price.store_id.is_(None))
        return self.db.execute(org_wide.order_by(Price.effective_from.desc())).scalars().first()

    def get_latest_for_product_store(
        self, organization_id: uuid.UUID, *, product_id: uuid.UUID, store_id: uuid.UUID | None
    ) -> Price | None:
        """The most recently created Price row for this (product, store) —
        used by app.services.integration_apply_service.apply_price's
        skip-if-unchanged check (Phase 10 upgrade's loop-prevention
        mechanism). Deliberately ignores status/effective dates: it's
        comparing "what would this write duplicate," not "what's active."
        """
        conditions = [
            Price.organization_id == organization_id,
            Price.product_id == product_id,
            Price.store_id == store_id if store_id is not None else Price.store_id.is_(None),
        ]
        stmt = select(Price).where(*conditions).order_by(Price.created_at.desc())
        return self.db.execute(stmt).scalars().first()

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        product_id: uuid.UUID | None = None,
        store_id: uuid.UUID | None = None,
        price_type: PriceType | None = None,
        status: PriceStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Price], int]:
        conditions = [Price.organization_id == organization_id]
        if product_id is not None:
            conditions.append(Price.product_id == product_id)
        if store_id is not None:
            conditions.append(Price.store_id == store_id)
        if price_type is not None:
            conditions.append(Price.price_type == price_type)
        if status is not None:
            conditions.append(Price.status == status)

        base_stmt = select(Price).where(*conditions)
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(
                base_stmt.order_by(Price.effective_from.desc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total
