import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt


ALGORITHM = "HS256"


def _get_secret_key() -> str:
    key = os.getenv("ACTIVITYPASS_SECRET_KEY", "").strip()
    environment = os.getenv("ENVIRONMENT", "development").lower()

    if environment == "production":
        if len(key) < 32:
            raise RuntimeError(
                "ACTIVITYPASS_SECRET_KEY must be set to a strong secret in production."
            )
        return key

    # Development only. A new key per process means local sessions reset on restart,
    # which is safer than shipping a reusable secret in the source code.
    return key if len(key) >= 32 else secrets.token_urlsafe(48)


SECRET_KEY = _get_secret_key()


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        120_000,
    )
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split(":", 1)
        expected = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            120_000,
        )
        return hmac.compare_digest(expected.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if not subject:
            raise ValueError("Invalid token subject")
        return int(subject)
    except (JWTError, ValueError, TypeError):
        raise ValueError("Invalid access token") from None
