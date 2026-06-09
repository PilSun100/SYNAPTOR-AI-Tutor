from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_current_user, get_db
from app.models.learning import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import authenticate_user, refresh_access_token, register_user

router = APIRouter()


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user, access_token, refresh_token, expires_in = register_user(
            db=db,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _token_response(user, access_token, refresh_token, expires_in)


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user, access_token, refresh_token, expires_in = authenticate_user(
            db=db,
            email=payload.email,
            password=payload.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return _token_response(user, access_token, refresh_token, expires_in)


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user, access_token, refresh_token, expires_in = refresh_access_token(
            db=db,
            refresh_token=payload.refresh_token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return _token_response(user, access_token, refresh_token, expires_in)


@router.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _user_response(current_user)


def _token_response(
    user: User,
    access_token: str,
    refresh_token: str,
    expires_in: int,
) -> TokenResponse:
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user=_user_response(user),
    )


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
    )
