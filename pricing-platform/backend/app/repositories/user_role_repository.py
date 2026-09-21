import uuid

from sqlalchemy import delete, select

from app.models.user import User
from app.models.user_role import UserRole
from app.repositories.base import BaseRepository


class UserRoleRepository(BaseRepository[UserRole]):
    model = UserRole

    def assign(self, user_id: uuid.UUID, role_id: uuid.UUID) -> UserRole:
        return self.add(UserRole(user_id=user_id, role_id=role_id))

    def reassign_role_for_organization(
        self, *, organization_id: uuid.UUID, old_role_id: uuid.UUID, new_role_id: uuid.UUID
    ) -> None:
        """Move every UserRole(role_id=old_role_id) for users in this
        organization onto new_role_id. Used when a system role is forked
        into an org-scoped copy — only this org's assignments move; every
        other tenant's UserRole rows still point at the untouched original.
        """
        stmt = select(UserRole.user_id).where(
            UserRole.role_id == old_role_id,
            UserRole.user_id.in_(select(User.id).where(User.organization_id == organization_id)),
        )
        user_ids = list(self.db.execute(stmt).scalars().all())
        if not user_ids:
            return

        self.db.execute(
            delete(UserRole).where(UserRole.role_id == old_role_id, UserRole.user_id.in_(user_ids))
        )
        for user_id in user_ids:
            self.db.add(UserRole(user_id=user_id, role_id=new_role_id))
        self.db.flush()

    def list_role_ids_for_user(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        stmt = select(UserRole.role_id).where(UserRole.user_id == user_id)
        return list(self.db.execute(stmt).scalars().all())

    def replace_roles(self, user_id: uuid.UUID, role_ids: list[uuid.UUID]) -> None:
        self.db.execute(delete(UserRole).where(UserRole.user_id == user_id))
        for role_id in role_ids:
            self.db.add(UserRole(user_id=user_id, role_id=role_id))
        self.db.flush()
