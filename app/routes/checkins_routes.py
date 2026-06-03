"""Отметки выполнения привычки + статистика стриков."""

from __future__ import annotations

from datetime import date, timedelta

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import CurrentUser
from app.database import Database
from app.schemas import CheckinCreate, CheckinResponse, HabitStatsResponse


def _calc_streaks(dates: list[date]) -> tuple[int, int]:
    """Считает текущий и максимальный стрик из отсортированного списка дат.

    Текущий стрик — это серия подряд идущих дней, заканчивающаяся сегодня
    или вчера (если ещё не отметились сегодня).
    """
    if not dates:
        return 0, 0
    unique_sorted = sorted(set(dates))
    longest = 1
    current_run = 1
    for previous, current in zip(unique_sorted, unique_sorted[1:]):
        if (current - previous).days == 1:
            current_run += 1
            longest = max(longest, current_run)
        else:
            current_run = 1
    today = date.today()
    last = unique_sorted[-1]
    if last not in (today, today - timedelta(days=1)):
        return 0, longest
    # тек. стрик = длина последней непрерывной серии
    current_streak = 1
    for i in range(len(unique_sorted) - 1, 0, -1):
        if (unique_sorted[i] - unique_sorted[i - 1]).days == 1:
            current_streak += 1
        else:
            break
    return current_streak, longest


def build_router(database: Database, get_current_user) -> APIRouter:
    router = APIRouter(tags=["checkins"])

    async def _assert_habit_owned(habit_id: int, user_id: int) -> None:
        owner_check = await database.pool.fetchval(
            "SELECT 1 FROM habits WHERE id = $1 AND user_id = $2",
            habit_id,
            user_id,
        )
        if owner_check is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Привычка не найдена",
            )

    @router.post(
        "/api/checkins", response_model=CheckinResponse, status_code=201
    )
    async def create_checkin(
        payload: CheckinCreate,
        user: CurrentUser = Depends(get_current_user),
    ) -> CheckinResponse:
        await _assert_habit_owned(payload.habit_id, user.user_id)
        try:
            row = await database.pool.fetchrow(
                "INSERT INTO checkins (habit_id, date, note) "
                "VALUES ($1, $2, $3) "
                "RETURNING id, habit_id, date, note",
                payload.habit_id,
                payload.date,
                payload.note,
            )
        except asyncpg.UniqueViolationError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Отметка за эту дату уже есть",
            ) from error
        return CheckinResponse(**dict(row))

    @router.delete("/api/checkins/{checkin_id}", status_code=204)
    async def delete_checkin(
        checkin_id: int,
        user: CurrentUser = Depends(get_current_user),
    ) -> None:
        # Проверяем владение через JOIN с habits
        result = await database.pool.execute(
            "DELETE FROM checkins c "
            "USING habits h "
            "WHERE c.id = $1 AND c.habit_id = h.id AND h.user_id = $2",
            checkin_id,
            user.user_id,
        )
        if result.endswith(" 0"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Отметка не найдена",
            )

    @router.get(
        "/api/habits/{habit_id}/checkins",
        response_model=list[CheckinResponse],
    )
    async def list_checkins(
        habit_id: int,
        days: int = Query(default=90, ge=1, le=365),
        user: CurrentUser = Depends(get_current_user),
    ) -> list[CheckinResponse]:
        await _assert_habit_owned(habit_id, user.user_id)
        since = date.today() - timedelta(days=days)
        rows = await database.pool.fetch(
            "SELECT id, habit_id, date, note FROM checkins "
            "WHERE habit_id = $1 AND date >= $2 "
            "ORDER BY date DESC",
            habit_id,
            since,
        )
        return [CheckinResponse(**dict(row)) for row in rows]

    @router.get(
        "/api/habits/{habit_id}/stats", response_model=HabitStatsResponse
    )
    async def habit_stats(
        habit_id: int,
        user: CurrentUser = Depends(get_current_user),
    ) -> HabitStatsResponse:
        await _assert_habit_owned(habit_id, user.user_id)
        all_rows = await database.pool.fetch(
            "SELECT date FROM checkins WHERE habit_id = $1 ORDER BY date ASC",
            habit_id,
        )
        all_dates = [row["date"] for row in all_rows]
        current_streak, longest_streak = _calc_streaks(all_dates)

        since_30 = date.today() - timedelta(days=29)
        last_30 = [d for d in all_dates if d >= since_30]

        return HabitStatsResponse(
            habit_id=habit_id,
            total_checkins=len(all_dates),
            current_streak=current_streak,
            longest_streak=longest_streak,
            last_30_days=sorted(last_30),
        )

    return router
