import uuid

from sqlalchemy import select

from app.models.role import Role
from app.models.user_role import UserRole
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    model = Role

    def get_system_role_by_name(self, name: str) -> Role | None:
        stmt = select(Role).where(
            Role.name == name, Role.organization_id.is_(None), Role.is_system_role.is_(True)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(self, user_id: uuid.UUID) -> list[Role]:
        stmt = select(Role).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
        return list(self.db.execute(stmt).scalars().all())

    def list_assignable(self, organization_id: uuid.UUID) -> list[Role]:
        """Roles this organization can assign/edit: every global system
        role, except where the org has forked it into its own customized
        copy (see Role.cloned_from_role_id) — in that case the fork
        replaces the original in this list so there's exactly one "Store
        Manager" entry per organization, never two.
        """
        system_roles = self.list_system_roles()
        org_roles = self.list_for_organization(organization_id)
        forked_source_ids = {role.cloned_from_role_id for role in org_roles if role.cloned_from_role_id}

        result = [role for role in system_roles if role.id not in forked_source_ids]
        result.extend(org_roles)
        result.sort(key=lambda role: role.name)
        return result

    def list_system_roles(self) -> list[Role]:
        stmt = select(Role).where(Role.is_system_role.is_(True)).order_by(Role.name)
        return list(self.db.execute(stmt).scalars().all())

    def list_for_organization(self, organization_id: uuid.UUID) -> list[Role]:
        stmt = select(Role).where(Role.organization_id == organization_id).order_by(Role.name)
        return list(self.db.execute(stmt).scalars().all())

    def get_org_fork(self, organization_id: uuid.UUID, source_role_id: uuid.UUID) -> Role | None:
        stmt = select(Role).where(
            Role.organization_id == organization_id, Role.cloned_from_role_id == source_role_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_ids(self, role_ids: list[uuid.UUID]) -> list[Role]:
        if not role_ids:
            return []
        stmt = select(Role).where(Role.id.in_(role_ids))
        return list(self.db.execute(stmt).scalars().all())
