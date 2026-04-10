from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

COMMON_WEAK_PASSWORDS = {
    "123456",
    "12345678",
    "123456789",
    "password",
    "password123",
    "qwerty",
    "qwerty123",
    "111111",
    "abc123",
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def validate_password_strength(password: str, username: str, email: str) -> None:
    lower_pwd = password.lower()

    if len(password) < 12:
        raise ValueError("密碼長度至少需 12 碼")

    if lower_pwd in COMMON_WEAK_PASSWORDS:
        raise ValueError("密碼過於簡單，請更換")

    if username.lower() in lower_pwd:
        raise ValueError("密碼不可包含使用者名稱")

    email_prefix = email.split("@")[0].lower()
    if email_prefix and email_prefix in lower_pwd:
        raise ValueError("密碼不可包含信箱前綴")

    if password.isalpha() or password.isdigit():
        raise ValueError("密碼不可全為英文字母或數字")


def create_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str = "access",
    extra_data: Optional[dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }

    if extra_data:
        payload.update(extra_data)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(subject: str) -> str:
    return create_token(
        subject=subject,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
    )


def create_refresh_token(subject: str) -> str:
    return create_token(
        subject=subject,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


def create_email_verification_token(subject: str) -> str:
    return create_token(
        subject=subject,
        expires_delta=timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS),
        token_type="email_verification",
    )