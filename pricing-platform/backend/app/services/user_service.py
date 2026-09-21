import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User, UserStatus
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_role_repository import UserRoleRepository
from app.schemas.user import UserAdminUpdate, UserCreate, UserListParams, UserUpdateSelf


def update_current_user(db: Session, *, user: User, payload: UserUpdateSelf) -> User:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)

    return UserRepository(db).add(user)


def _resolve_roles(db: Session, *, organization_id: uuid.UUID, role_ids: list[uuid.UUID]) -> list[Role]:
    roles = RoleRepository(db).list_by_ids(role_ids)
    found_ids = {role.id for role in roles}
    missing = [str(rid) for rid in role_ids if rid not in found_ids]
    if missing:
        raise NotFoundError(f"Unknown role id(s): {', '.join(missing)}", code="role_not_found")

    # A role is assignable here if it's a global system template, or an
    # org-scoped fork (see Role.cloned_from_role_id) belonging to this
    # organization — never another organization's custom fork.
    foreign = [
        str(role.id)
        for role in roles
        if role.organization_id is not None and role.organization_id != organization_id
    ]
    if foreign:
        raise NotFoundError(f"Unknown role id(s): {', '.join(foreign)}", code="role_not_found")

    return roles


def roles_for_user(db: Session, user_id: uuid.UUID) -> list[Role]:
    return RoleRepository(db).list_for_user(user_id)


def list_users(
    db: Session, *, organization_id: uuid.UUID, params: UserListParams
) -> tuple[list[User], int]:
    offset = (params.page - 1) * params.page_size
    return UserRepository(db).search(
        organization_id, search=params.search, offset=offset, limit=params.page_size
    )


def get_user(db: Session, *, organization_id: uuid.UUID, user_id: uuid.UUID) -> User:
    user = UserRepository(db).get_by_id_for_organization(user_id, organization_id)
    if user is None:
        raise NotFoundError("User not found.", code="user_not_found")
    return user


def create_user(db: Session, *, organization_id: uuid.UUID, payload: UserCreate) -> User:
    user_repo = UserRepository(db)
    # Email must be globally unique, not just per-organization: login looks a
    # user up by email alone with no org selector (see UserRepository.get_by_email).
    if user_repo.get_by_email(payload.email) is not None:
        raise ConflictError("A user with this email already exists.", code="email_taken")

    roles = _resolve_roles(db, organization_id=organization_id, role_ids=payload.role_ids)

    user = user_repo.add(
        User(
            id=uuid.uuid4(),
            organization_id=organization_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            password_hash=hash_password(payload.password),
            phone=payload.phone,
            status=UserStatus.ACTIVE,
        )
    )

    user_role_repo = UserRoleRepository(db)
    for role in roles:
        user_role_repo.assign(user.id, role.id)

    return user


def update_user(
    db: Session,
    *,
    organization_id: uuid.UUID,
    actor_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: UserAdminUpdate,
) -> User:
    if user_id == actor_id:
        raise ForbiddenError(
            "Use your profile page to edit your own account.", code="cannot_self_administer"
        )

    user = get_user(db, organization_id=organization_id, user_id=user_id)

    updates = payload.model_dump(exclude_unset=True, exclude={"role_ids"})
    for field, value in updates.items():
        setattr(user, field, value)

    if payload.role_ids is not None:
        roles = _resolve_roles(db, organization_id=organization_id, role_ids=payload.role_ids)
        UserRoleRepository(db).replace_roles(user.id, [role.id for role in roles])

    return UserRepository(db).add(user)


def delete_user(db: Session, *, organization_id: uuid.UUID, actor_id: uuid.UUID, user_id: uuid.UUID) -> None:
    if user_id == actor_id:
        raise ForbiddenError("You cannot delete your own account.", code="cannot_self_administer")

    user = get_user(db, organization_id=organization_id, user_id=user_id)
    UserRepository(db).soft_delete(user)
