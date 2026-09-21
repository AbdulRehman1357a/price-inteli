import uuid

from sqlalchemy import select

from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.repositories.base import BaseRepository


class PermissionRepository(BaseRepository[Permission]):
    model = Permission

    def list_codes_for_roles(self, role_ids: list[uuid.UUID]) -> set[str]:
        if not role_ids:
            return set()
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id.in_(role_ids))
        )
        return set(self.db.execute(stmt).scalars().all())

    def list_all(self) -> list[Permission]:
        stmt = select(Permission).order_by(Permission.module, Permission.code)
        return list(self.db.execute(stmt).scalars().all())

    def list_by_ids(self, permission_ids: list[uuid.UUID]) -> list[Permission]:
        if not permission_ids:
            return []
        stmt = select(Permission).where(Permission.id.in_(permission_ids))
        return list(self.db.execute(stmt).scalars().all())

    def list_for_role(self, role_id: uuid.UUID) -> list[Permission]:
        stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
            .order_by(Permission.module, Permission.code)
        )
        return list(self.db.execute(stmt).scalars().all())
