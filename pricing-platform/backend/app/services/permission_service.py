from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.repositories.permission_repository import PermissionRepository


def list_permissions(db: Session) -> list[Permission]:
    return PermissionRepository(db).list_all()
