import uuid

from sqlalchemy import delete, select

from app.models.role_permission import RolePermission
from app.repositories.base import BaseRepository


class RolePermissionRepository(BaseRepository[RolePermission]):
    model = RolePermission

    def list_permission_ids_for_role(self, role_id: uuid.UUID) -> list[uuid.UUID]:
        stmt = select(RolePermission.permission_id).where(RolePermission.role_id == role_id)
        return list(self.db.execute(stmt).scalars().all())

    def replace_permissions(self, role_id: uuid.UUID, permission_ids: list[uuid.UUID]) -> None:
        self.db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
        for permission_id in permission_ids:
            self.db.add(RolePermission(role_id=role_id, permission_id=permission_id))
        self.db.flush()
