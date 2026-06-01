from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.database import SessionDep
from app.core.security import find_user_by_username, get_current_user, token_store, verify_password
from app.models import User
from app.services.operation_log import record_operation

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    id: int
    username: str


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, session: SessionDep) -> LoginResponse:
    user = find_user_by_username(session, payload.username)
    if not user or not verify_password(payload.password, user.password_hash):
        record_operation(
            session,
            action="auth.login.failed",
            actor=payload.username or "unknown",
            target_type="user",
            target_id=payload.username,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = token_store.issue(user)
    record_operation(
        session,
        action="auth.login.success",
        actor=user.username,
        target_type="user",
        target_id=str(user.id),
    )
    return LoginResponse(access_token=token)


@router.get("/me", response_model=UserProfile)
def get_profile(current_user: User = Depends(get_current_user)) -> UserProfile:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
    return UserProfile(id=current_user.id, username=current_user.username)
