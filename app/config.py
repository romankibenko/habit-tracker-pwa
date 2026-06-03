"""Конфигурация приложения — читается из переменных окружения."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Не задана обязательная переменная окружения: {name}")
    return value


def _optional(name: str, default: str = "") -> str:
    return os.getenv(name) or default


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str

    @property
    def dsn(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


@dataclass(frozen=True)
class JWTConfig:
    secret: str
    algorithm: str
    access_token_expire_minutes: int


@dataclass(frozen=True)
class VAPIDConfig:
    public_key: Optional[str]
    private_key: Optional[str]
    contact_email: str

    @property
    def is_configured(self) -> bool:
        return bool(self.public_key and self.private_key)


@dataclass(frozen=True)
class AppConfig:
    host: str
    port: int
    database: DatabaseConfig
    jwt: JWTConfig
    vapid: VAPIDConfig


def load_config() -> AppConfig:
    """Собирает конфиг из окружения. Падает рано, если не хватает обязательных."""
    return AppConfig(
        host=_optional("APP_HOST", "0.0.0.0"),
        port=int(_optional("APP_PORT", "8000")),
        database=DatabaseConfig(
            host=_optional("DB_HOST", "localhost"),
            port=int(_optional("DB_PORT", "5432")),
            name=_require("DB_NAME"),
            user=_require("DB_USER"),
            password=_require("DB_PASSWORD"),
        ),
        jwt=JWTConfig(
            secret=_require("JWT_SECRET"),
            algorithm=_optional("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(
                _optional("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
            ),
        ),
        vapid=VAPIDConfig(
            public_key=_optional("VAPID_PUBLIC_KEY") or None,
            private_key=_optional("VAPID_PRIVATE_KEY") or None,
            contact_email=_optional("VAPID_CONTACT_EMAIL", "mailto:admin@example.com"),
        ),
    )
