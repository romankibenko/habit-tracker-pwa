"""Роуты подписки на пуши и тестовой отправки."""

from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import CurrentUser
from app.config import VAPIDConfig
from app.database import Database
from app.push import PushService
from app.schemas import PushSubscribeRequest, PushTestRequest


def build_router(
    database: Database,
    push_service: PushService,
    vapid_config: VAPIDConfig,
    get_current_user,
) -> APIRouter:
    router = APIRouter(prefix="/api/push", tags=["push"])

    @router.get("/public-key")
    async def public_key() -> dict[str, str | None]:
        """Фронт берёт ключ отсюда для PushManager.subscribe."""
        return {"public_key": vapid_config.public_key}

    @router.post("/subscribe", status_code=201)
    async def subscribe(
        payload: PushSubscribeRequest,
        user: CurrentUser = Depends(get_current_user),
    ) -> dict[str, str]:
        try:
            await database.pool.execute(
                "INSERT INTO push_subscriptions "
                "(user_id, endpoint, p256dh, auth) "
                "VALUES ($1, $2, $3, $4)",
                user.user_id,
                payload.endpoint,
                payload.keys.p256dh,
                payload.keys.auth,
            )
        except asyncpg.UniqueViolationError:
            # Подписка уже зарегистрирована — это норм, идемпотентно
            pass
        return {"status": "subscribed"}

    @router.post("/test")
    async def test_push(
        payload: PushTestRequest,
        user: CurrentUser = Depends(get_current_user),
    ) -> dict[str, int]:
        if not push_service.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="VAPID-ключи не настроены на сервере",
            )
        rows = await database.pool.fetch(
            "SELECT endpoint, p256dh, auth FROM push_subscriptions "
            "WHERE user_id = $1",
            user.user_id,
        )
        sent = 0
        for row in rows:
            subscription = {
                "endpoint": row["endpoint"],
                "keys": {"p256dh": row["p256dh"], "auth": row["auth"]},
            }
            ok = await push_service.send(subscription, payload.title, payload.body)
            if ok:
                sent += 1
        return {"sent": sent, "total_subscriptions": len(rows)}

    return router
