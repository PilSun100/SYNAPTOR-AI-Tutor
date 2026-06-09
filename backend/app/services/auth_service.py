from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.learning import RefreshToken, User, utc_now


def register_user(
    db: Session,
    email: str,
    password: str,
    display_name: str,
) -> tuple[User, str, str, int]:
    normalized_email = email.lower().strip()
    existing = db.query(User).filter(User.email == normalized_email).one_or_none()
    if existing is not None:
        raise ValueError("이미 가입된 이메일입니다.")

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        display_name=display_name.strip(),
    )
    db.add(user)
    db.flush()
    access_token, expires_in = create_access_token(user.id)
    refresh_token = _store_refresh_token(db, user.id)
    db.commit()
    db.refresh(user)
    return user, access_token, refresh_token, expires_in


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> tuple[User, str, str, int]:
    normalized_email = email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email).one_or_none()
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다.")

    access_token, expires_in = create_access_token(user.id)
    refresh_token = _store_refresh_token(db, user.id)
    db.commit()
    db.refresh(user)
    return user, access_token, refresh_token, expires_in


def refresh_access_token(
    db: Session,
    refresh_token: str,
) -> tuple[User, str, str, int]:
    token_hash = hash_token(refresh_token)
    stored = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .one_or_none()
    )
    if (
        stored is None
        or stored.revoked_at is not None
        or _as_utc(stored.expires_at) < utc_now()
    ):
        raise ValueError("refresh token이 유효하지 않습니다.")

    user = stored.user
    if not user.is_active:
        raise ValueError("비활성화된 사용자입니다.")

    stored.revoked_at = utc_now()
    access_token, expires_in = create_access_token(user.id)
    new_refresh_token = _store_refresh_token(db, user.id)
    db.commit()
    db.refresh(user)
    return user, access_token, new_refresh_token, expires_in


def _store_refresh_token(db: Session, user_id: int) -> str:
    refresh_token = create_refresh_token()
    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=hash_token(refresh_token),
            expires_at=utc_now() + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    return refresh_token


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
