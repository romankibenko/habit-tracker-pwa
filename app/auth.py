"""Хеширование паролей и работа с JWT."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import JWTConfig

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, email: str, config: JWTConfig) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=config.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, config.secret, algorithm=config.algorithm)


def decode_token(token: str, config: JWTConfig) -> dict:
    try:
        return jwt.decode(token, config.secret, algorithms=[config.algorithm])
    except JWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Невалидный токен: {error}",
        ) from error


class CurrentUser:
    """DI-объект текущего пользователя — пробрасывается в роуты."""

    def __init__(self, user_id: int, email: str) -> None:
        self.user_id = user_id
        self.email = email


def make_get_current_user(config: JWTConfig):
    """Фабрика зависимости — нужна, чтобы прокинуть JWTConfig в Depends."""

    async def get_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    ) -> CurrentUser:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Требуется авторизация",
            )
        payload = decode_token(credentials.credentials, config)
        user_id_raw = payload.get("sub")
        email = payload.get("email")
        if user_id_raw is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен повреждён",
            )
        return CurrentUser(user_id=int(user_id_raw), email=email)

    return get_current_user
