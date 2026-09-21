import uuid

from sqlalchemy import select

from app.models.organization import Organization, OrganizationStatus
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    model = Organization

    def get_by_slug(self, slug: str) -> Organization | None:
        stmt = self._not_deleted(select(Organization).where(Organization.slug == slug))
        return self.db.execute(stmt).scalar_one_or_none()

    def list_active_ids(self) -> list[uuid.UUID]:
        """Used by the Phase 15 periodic snapshot recompute (app.tasks.analytics)
        to loop every tenant — suspended/inactive orgs are skipped since
        their data isn't changing.
        """
        stmt = self._not_deleted(
            select(Organization.id).where(Organization.status == OrganizationStatus.ACTIVE)
        )
        return list(self.db.execute(stmt).scalars().all())
