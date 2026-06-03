"""Роуты регистрации и входа."""

from __future__ import annotations

import asyncpg
from fastapi import APIRouter, HTTPException, status

from app.auth import create_access_token, hash_password, verify_password
from app.config import JWTConfig
from app.database import Database
from app.schemas import LoginRequest, RegisterRequest, TokenResponse


def build_router(database: Database, jwt_config: JWTConfig) -> APIRouter:
    router = APIRouter(prefix="/api/auth", tags=["auth"])

    @router.post("/register", response_model=TokenResponse, status_code=201)
    async def register(payload: RegisterRequest) -> TokenResponse:
        password_hash = hash_password(payload.password)
        try:
            row = await database.pool.fetchrow(
                "INSERT INTO users (email, password_hash) "
                "VALUES ($1, $2) RETURNING id, email",
                payload.email.lower(),
                password_hash,
            )
        except asyncpg.UniqueViolationError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким email уже зарегистрирован",
            ) from error
        token = create_access_token(row["id"], row["email"], jwt_config)
        return TokenResponse(
            access_token=token, user_id=row["id"], email=row["email"]
        )

    @router.post("/login", response_model=TokenResponse)
    async def login(payload: LoginRequest) -> TokenResponse:
        row = await database.pool.fetchrow(
            "SELECT id, email, password_hash FROM users WHERE email = $1",
            payload.email.lower(),
        )
        if row is None or not verify_password(payload.password, row["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
            )
        token = create_access_token(row["id"], row["email"], jwt_config)
        return TokenResponse(
            access_token=token, user_id=row["id"], email=row["email"]
        )

    return router
