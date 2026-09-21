import re
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError, ConflictError, UnauthorizedError
from app.core.rbac import SystemRoleName
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.organization import Organization, OrganizationStatus
from app.models.user import User, UserStatus
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_role_repository import UserRoleRepository
from app.schemas.auth import AccessTokenResponse, LoginRequest, MeResponse, RegisterRequest, TokenResponse
from app.schemas.organization import OrganizationOut
from app.schemas.user import UserOut


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return (slug or "org")[:90]


def _generate_unique_slug(org_repo: OrganizationRepository, name: str) -> str:
    base = _slugify(name)
    slug = base
    suffix = 1
    while org_repo.get_by_slug(slug) is not None:
        suffix += 1
        slug = f"{base}-{suffix}"
    return slug


def _issue_tokens(user_id: uuid.UUID, *, remember_me: bool = False) -> TokenResponse:
    settings = get_settings()
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id, remember_me=remember_me),
        expires_in=settings.access_token_expire_minutes * 60,
    )


def register(db: Session, payload: RegisterRequest) -> TokenResponse:
    """Register a new organization + its first (admin) user in one transaction.

    Creates: Organization, User, and assigns the seeded "Organization Admin"
    system role via UserRole. Committed by the get_db dependency once this
    returns without error — see app/db/session.py.
    """
    org_repo = OrganizationRepository(db)
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    user_role_repo = UserRoleRepository(db)

    if user_repo.get_by_email(payload.email) is not None:
        raise ConflictError("An account with this email already exists.", code="email_taken")

    admin_role = role_repo.get_system_role_by_name(SystemRoleName.ORGANIZATION_ADMIN)
    if admin_role is None:
        raise AppError(
            "System roles are not seeded — run the Phase 1 data migration.",
            code="roles_not_seeded",
            status_code=500,
        )

    organization_id = uuid.uuid4()
    organization = org_repo.add(
        Organization(
            id=organization_id,
            name=payload.organization_name,
            slug=_generate_unique_slug(org_repo, payload.organization_name),
            email=payload.email,
            country=payload.country,
            timezone=payload.timezone,
            currency=payload.currency,
            status=OrganizationStatus.ACTIVE,
        )
    )

    user = user_repo.add(
        User(
            id=uuid.uuid4(),
            organization_id=organization.id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            password_hash=hash_password(payload.password),
            status=UserStatus.ACTIVE,
        )
    )

    user_role_repo.assign(user.id, admin_role.id)

    return _issue_tokens(user.id)


def login(db: Session, payload: LoginRequest) -> TokenResponse:
    user_repo = UserRepository(db)
    org_repo = OrganizationRepository(db)

    user = user_repo.get_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password.", code="invalid_credentials")

    if user.status != UserStatus.ACTIVE:
        raise UnauthorizedError("This account is not active.", code="account_not_active")

    organization = org_repo.get_by_id(user.organization_id)
    if organization is None or organization.status != OrganizationStatus.ACTIVE:
        raise UnauthorizedError("This organization is not active.", code="organization_not_active")

    user.last_login_at = datetime.now(UTC)
    user_repo.add(user)

    return _issue_tokens(user.id, remember_me=payload.remember_me)


def refresh_access_token(db: Session, refresh_token: str) -> AccessTokenResponse:
    settings = get_settings()
    claims = decode_token(refresh_token)
    if claims is None or claims.get("type") != TokenType.REFRESH.value:
        raise UnauthorizedError("Invalid or expired refresh token.", code="invalid_refresh_token")

    user_repo = UserRepository(db)
    try:
        user_id = uuid.UUID(claims["sub"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Invalid or expired refresh token.", code="invalid_refresh_token") from exc

    user = user_repo.get_by_id(user_id)
    if user is None or user.status != UserStatus.ACTIVE:
        raise UnauthorizedError("Invalid or expired refresh token.", code="invalid_refresh_token")

    return AccessTokenResponse(
        access_token=create_access_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60,
    )


def get_current_user_context(db: Session, user: User) -> MeResponse:
    org_repo = OrganizationRepository(db)
    role_repo = RoleRepository(db)
    permission_repo = PermissionRepository(db)

    organization = org_repo.get_by_id(user.organization_id)
    if organization is None:
        raise UnauthorizedError("Organization not found.", code="organization_not_found")

    roles = role_repo.list_for_user(user.id)
    permission_codes = permission_repo.list_codes_for_roles([role.id for role in roles])

    return MeResponse(
        user=UserOut.model_validate(user),
        organization=OrganizationOut.model_validate(organization),
        roles=[role.name for role in roles],
        permissions=sorted(permission_codes),
    )
