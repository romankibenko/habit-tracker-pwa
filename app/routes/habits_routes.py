"""CRUD привычек. Все запросы привязаны к user_id из JWT."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth import CurrentUser
from app.database import Database
from app.schemas import HabitCreate, HabitResponse, HabitUpdate


def build_router(database: Database, get_current_user) -> APIRouter:
    router = APIRouter(prefix="/api/habits", tags=["habits"])

    @router.get("", response_model=list[HabitResponse])
    async def list_habits(
        user: CurrentUser = Depends(get_current_user),
    ) -> list[HabitResponse]:
        rows = await database.pool.fetch(
            "SELECT id, name, description, color, target_per_week, "
            "is_archived, created_at "
            "FROM habits WHERE user_id = $1 "
            "ORDER BY is_archived ASC, created_at DESC",
            user.user_id,
        )
        return [HabitResponse(**dict(row)) for row in rows]

    @router.post("", response_model=HabitResponse, status_code=201)
    async def create_habit(
        payload: HabitCreate,
        user: CurrentUser = Depends(get_current_user),
    ) -> HabitResponse:
        row = await database.pool.fetchrow(
            "INSERT INTO habits "
            "(user_id, name, description, color, target_per_week) "
            "VALUES ($1, $2, $3, $4, $5) "
            "RETURNING id, name, description, color, target_per_week, "
            "is_archived, created_at",
            user.user_id,
            payload.name,
            payload.description,
            payload.color or "#4f46e5",
            payload.target_per_week,
        )
        return HabitResponse(**dict(row))

    @router.patch("/{habit_id}", response_model=HabitResponse)
    async def update_habit(
        habit_id: int,
        payload: HabitUpdate,
        user: CurrentUser = Depends(get_current_user),
    ) -> HabitResponse:
        # Собираем динамический UPDATE только из заполненных полей
        fields = payload.model_dump(exclude_unset=True)
        if not fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нет полей для обновления",
            )
        set_parts = []
        values = []
        for index, (key, value) in enumerate(fields.items(), start=1):
            set_parts.append(f"{key} = ${index}")
            values.append(value)
        values.extend([habit_id, user.user_id])
        habit_id_pos = len(values) - 1
        user_id_pos = len(values)
        query = (
            f"UPDATE habits SET {', '.join(set_parts)} "
            f"WHERE id = ${habit_id_pos} AND user_id = ${user_id_pos} "
            "RETURNING id, name, description, color, target_per_week, "
            "is_archived, created_at"
        )
        row = await database.pool.fetchrow(query, *values)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Привычка не найдена",
            )
        return HabitResponse(**dict(row))

    @router.delete("/{habit_id}", status_code=204, response_class=Response)
    async def delete_habit(
        habit_id: int,
        user: CurrentUser = Depends(get_current_user),
    ):
        result = await database.pool.execute(
            "DELETE FROM habits WHERE id = $1 AND user_id = $2",
            habit_id,
            user.user_id,
        )
        # asyncpg возвращает строку "DELETE N" — если N=0, ничего не удалили
        if result.endswith(" 0"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Привычка не найдена",
            )
        return Response(status_code=204)

    return router
