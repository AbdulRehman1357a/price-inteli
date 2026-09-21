import uuid

from sqlalchemy import func, or_, select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_id_for_organization(self, user_id: uuid.UUID, organization_id: uuid.UUID) -> User | None:
        stmt = self._not_deleted(
            select(User).where(User.id == user_id, User.organization_id == organization_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        search: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        conditions = [User.organization_id == organization_id]
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(User.first_name.ilike(pattern), User.last_name.ilike(pattern), User.email.ilike(pattern))
            )

        base_stmt = self._not_deleted(select(User).where(*conditions))

        total = self.db.execute(
            select(func.count()).select_from(base_stmt.order_by(None).subquery())
        ).scalar_one()

        items = list(
            self.db.execute(base_stmt.order_by(User.created_at.desc()).offset(offset).limit(limit))
            .scalars()
            .all()
        )
        return items, total

    def get_by_email(self, email: str) -> User | None:
        """Global lookup across every organization.

        users.email is only unique per-organization at the DB level, but the
        login/registration flows have no org selector, so the service layer
        enforces email uniqueness globally at registration — this lookup
        backs that check and backs login-by-email.
        """
        stmt = self._not_deleted(select(User).where(User.email == email))
        return self.db.execute(stmt).scalar_one_or_none()
