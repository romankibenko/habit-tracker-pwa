"""Пул asyncpg + хелперы доступа к БД."""

from __future__ import annotations

import logging
from typing import Optional

import asyncpg

from app.config import DatabaseConfig
from app.models import CREATE_TABLES_SQL

logger = logging.getLogger(__name__)


class Database:
    """Тонкая обёртка над asyncpg.Pool. Без ORM — чистый SQL."""

    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config
        self._pool: Optional[asyncpg.Pool] = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("База не инициализирована — вызови connect()")
        return self._pool

    async def connect(self) -> None:
        logger.info("Подключаюсь к Postgres %s:%s/%s",
                    self._config.host, self._config.port, self._config.name)
        self._pool = await asyncpg.create_pool(
            host=self._config.host,
            port=self._config.port,
            database=self._config.name,
            user=self._config.user,
            password=self._config.password,
            min_size=1,
            max_size=10,
            command_timeout=30,
        )
        async with self._pool.acquire() as connection:
            await connection.execute(CREATE_TABLES_SQL)
        logger.info("База готова: схема прогнана")

    async def disconnect(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("Пул соединений закрыт")
