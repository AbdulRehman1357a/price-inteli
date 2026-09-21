import uuid
from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.rbac import PermissionCode
from app.core.security import TokenType, decode_token
from app.db.session import get_db
from app.models.user import User, UserStatus
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Not authenticated.", code="not_authenticated")

    claims = decode_token(credentials.credentials)
    if claims is None or claims.get("type") != TokenType.ACCESS.value:
        raise UnauthorizedError("Invalid or expired access token.", code="invalid_access_token")

    try:
        user_id = uuid.UUID(claims["sub"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Invalid or expired access token.", code="invalid_access_token") from exc

    user = UserRepository(db).get_by_id(user_id)
    if user is None or user.status != UserStatus.ACTIVE:
        raise UnauthorizedError("Invalid or expired access token.", code="invalid_access_token")

    return user


def require_permission(permission: PermissionCode | str) -> Callable[..., User]:
    """RBAC dependency factory: 401 if unauthenticated, 403 if the user's
    roles don't grant `permission`. Usage: Depends(require_permission(PermissionCode.USERS_READ)).
    """
    code = permission.value if isinstance(permission, PermissionCode) else permission

    def _dependency(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        roles = RoleRepository(db).list_for_user(user.id)
        granted = PermissionRepository(db).list_codes_for_roles([role.id for role in roles])
        if code not in granted:
            raise ForbiddenError(
                "You do not have permission to perform this action.", code="permission_denied"
            )
        return user

    return _dependency
