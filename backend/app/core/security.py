import base64
import hashlib
import hmac
import json
import secrets
from datetime import timedelta

from app.core.config import settings
from app.models.learning import utc_now

JWT_ALGORITHM = "HS256"
PASSWORD_ITERATIONS = 390_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${PASSWORD_ITERATIONS}$"
        f"{base64.urlsafe_b64encode(salt).decode()}$"
        f"{base64.urlsafe_b64encode(digest).decode()}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, encoded_salt, encoded_digest = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(encoded_salt.encode())
        expected_digest = base64.urlsafe_b64decode(encoded_digest.encode())
        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
    except (ValueError, TypeError):
        return False

    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(user_id: int) -> tuple[str, int]:
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expires_at = utc_now() + expires_delta
    token = _encode_jwt(
        {
            "sub": str(user_id),
            "type": "access",
            "exp": int(expires_at.timestamp()),
        }
    )
    return token, int(expires_delta.total_seconds())


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_access_token(token: str) -> int | None:
    payload = _decode_jwt(token)
    if not payload or payload.get("type") != "access":
        return None

    subject = payload.get("sub")
    try:
        return int(subject)
    except (TypeError, ValueError):
        return None


def _encode_jwt(payload: dict) -> str:
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    header_segment = _base64url_json(header)
    payload_segment = _base64url_json(payload)
    signature = _sign(f"{header_segment}.{payload_segment}")
    return f"{header_segment}.{payload_segment}.{signature}"


def _decode_jwt(token: str) -> dict | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None

    signing_input = f"{parts[0]}.{parts[1]}"
    expected_signature = _sign(signing_input)
    if not hmac.compare_digest(expected_signature, parts[2]):
        return None

    try:
        payload = json.loads(_base64url_decode(parts[1]).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    expires_at = payload.get("exp")
    if not isinstance(expires_at, int) or expires_at < int(utc_now().timestamp()):
        return None

    return payload


def _sign(value: str) -> str:
    digest = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(digest)


def _base64url_json(value: dict) -> str:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _base64url_encode(raw)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("utf-8")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("utf-8"))
