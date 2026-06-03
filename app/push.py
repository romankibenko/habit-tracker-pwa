"""Обёртка над pywebpush для отправки Web Push с VAPID."""

from __future__ import annotations

import json
import logging
from typing import Any

from pywebpush import WebPushException, webpush

from app.config import VAPIDConfig

logger = logging.getLogger(__name__)


class PushService:
    def __init__(self, config: VAPIDConfig) -> None:
        self._config = config

    @property
    def is_configured(self) -> bool:
        return self._config.is_configured

    async def send(
        self,
        subscription: dict[str, Any],
        title: str,
        body: str,
        url: str = "/",
    ) -> bool:
        """Отправляет одно уведомление. Возвращает True если успех.

        subscription — dict с полями endpoint, keys.p256dh, keys.auth.
        """
        if not self.is_configured:
            logger.warning("VAPID не настроен — пуш не отправлен")
            return False
        payload = json.dumps({"title": title, "body": body, "url": url})
        try:
            webpush(
                subscription_info=subscription,
                data=payload,
                vapid_private_key=self._config.private_key,
                vapid_claims={"sub": self._config.contact_email},
            )
            return True
        except WebPushException as error:
            logger.error("Ошибка отправки пуша: %s", error)
            return False
