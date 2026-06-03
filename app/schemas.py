"""Pydantic-схемы запросов и ответов API."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ============ Auth ============

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str


# ============ Habits ============

class HabitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    color: Optional[str] = Field(default="#4f46e5", max_length=20)
    target_per_week: int = Field(default=7, ge=1, le=7)


class HabitUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    color: Optional[str] = Field(default=None, max_length=20)
    target_per_week: Optional[int] = Field(default=None, ge=1, le=7)
    is_archived: Optional[bool] = None


class HabitResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: str
    target_per_week: int
    is_archived: bool
    created_at: datetime


# ============ Checkins ============

class CheckinCreate(BaseModel):
    habit_id: int
    date: date
    note: Optional[str] = Field(default=None, max_length=500)


class CheckinResponse(BaseModel):
    id: int
    habit_id: int
    date: date
    note: Optional[str]


class HabitStatsResponse(BaseModel):
    habit_id: int
    total_checkins: int
    current_streak: int
    longest_streak: int
    last_30_days: list[date]


# ============ Push ============

class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscribeRequest(BaseModel):
    endpoint: str
    keys: PushSubscriptionKeys


class PushTestRequest(BaseModel):
    title: str = "Habit Tracker"
    body: str = "Тестовое уведомление"
