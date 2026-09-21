from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserOut, UserUpdateSelf
from app.services import auth_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=APIResponse[TokenResponse], status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> APIResponse[TokenResponse]:
    return APIResponse(data=auth_service.register(db, payload))


@router.post("/login", response_model=APIResponse[TokenResponse])
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> APIResponse[TokenResponse]:
    return APIResponse(data=auth_service.login(db, payload))


@router.post("/refresh", response_model=APIResponse[AccessTokenResponse])
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> APIResponse[AccessTokenResponse]:
    return APIResponse(data=auth_service.refresh_access_token(db, payload.refresh_token))


@router.get("/me", response_model=APIResponse[MeResponse])
def me(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> APIResponse[MeResponse]:
    return APIResponse(data=auth_service.get_current_user_context(db, current_user))


@router.put("/me", response_model=APIResponse[UserOut])
def update_me(
    payload: UserUpdateSelf,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponse[UserOut]:
    user = user_service.update_current_user(db, user=current_user, payload=payload)
    return APIResponse(data=UserOut.model_validate(user))


@router.post("/logout", response_model=APIResponse[dict[str, bool]])
def logout(current_user: User = Depends(get_current_user)) -> APIResponse[dict[str, bool]]:
    # Stateless JWT: there is no server-side session to invalidate yet, so
    # this just confirms the caller was authenticated. The client discards
    # both tokens. A refresh-token revocation store is a future-phase concern.
    return APIResponse(data={"logged_out": True})
