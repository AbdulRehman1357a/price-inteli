import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.rbac import PermissionCode
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_permission_repository import RolePermissionRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_role_repository import UserRoleRepository


def list_roles_with_permissions(
    db: Session, *, organization_id: uuid.UUID
) -> list[tuple[Role, list[Permission]]]:
    permission_repo = PermissionRepository(db)
    return [
        (role, permission_repo.list_for_role(role.id))
        for role in RoleRepository(db).list_assignable(organization_id)
    ]


def _resolve_permissions(db: Session, permission_ids: list[uuid.UUID]) -> list[Permission]:
    permissions = PermissionRepository(db).list_by_ids(permission_ids)
    found_ids = {p.id for p in permissions}
    missing = [str(pid) for pid in permission_ids if pid not in found_ids]
    if missing:
        raise NotFoundError(f"Unknown permission id(s): {', '.join(missing)}", code="permission_not_found")
    return permissions


def _assert_actor_keeps_role_management(
    db: Session, *, actor: User, edited_role_id: uuid.UUID, new_codes: set[str]
) -> None:
    """An admin editing a role must not strip away their own ability to
    manage users/roles — otherwise nobody (not even another admin) could
    undo the change, since doing so requires the very permission just
    removed. Only matters if the actor holds the role being edited.
    """
    actor_roles = RoleRepository(db).list_for_user(actor.id)
    if edited_role_id not in {role.id for role in actor_roles}:
        return

    other_role_ids = [role.id for role in actor_roles if role.id != edited_role_id]
    effective_codes = PermissionRepository(db).list_codes_for_roles(other_role_ids) | new_codes
    if PermissionCode.USERS_UPDATE.value not in effective_codes:
        raise ForbiddenError(
            "This change would remove your own ability to manage users and roles.",
            code="cannot_remove_own_role_management",
        )


def update_role_permissions(
    db: Session,
    *,
    organization_id: uuid.UUID,
    actor: User,
    role_id: uuid.UUID,
    permission_ids: list[uuid.UUID],
) -> tuple[Role, list[Permission]]:
    role_repo = RoleRepository(db)
    role = role_repo.get_by_id(role_id)
    if role is None:
        raise NotFoundError("Role not found.", code="role_not_found")
    if role.organization_id is not None and role.organization_id != organization_id:
        raise NotFoundError("Role not found.", code="role_not_found")

    permissions = _resolve_permissions(db, permission_ids)
    new_codes = {p.code for p in permissions}
    _assert_actor_keeps_role_management(db, actor=actor, edited_role_id=role.id, new_codes=new_codes)

    if role.organization_id == organization_id:
        target = role
    else:
        # Still the shared global template — fork it into an org-scoped
        # copy rather than mutating the row every other tenant reads, and
        # migrate this org's existing assignments onto the fork so they
        # keep the role name but pick up its (about to be set) permissions.
        target = role_repo.get_org_fork(organization_id, role.id)
        if target is None:
            target = role_repo.add(
                Role(
                    id=uuid.uuid4(),
                    organization_id=organization_id,
                    name=role.name,
                    description=role.description,
                    is_system_role=False,
                    cloned_from_role_id=role.id,
                )
            )
            UserRoleRepository(db).reassign_role_for_organization(
                organization_id=organization_id, old_role_id=role.id, new_role_id=target.id
            )

    RolePermissionRepository(db).replace_permissions(target.id, [p.id for p in permissions])
    return target, permissions
