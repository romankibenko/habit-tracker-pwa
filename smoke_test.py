"""Локальный smoke-тест API: register, login, CRUD привычки, чекин, статы, удаление."""
from __future__ import annotations

import random
import sys
from datetime import date

import urllib.request
import urllib.error
import json

BASE = "http://127.0.0.1:8000"


def request(method: str, path: str, *, token: str | None = None, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        try:
            return err.code, json.loads(raw)
        except json.JSONDecodeError:
            return err.code, {"raw": raw}


def assert_eq(label: str, got, expected):
    ok = got == expected
    mark = "OK " if ok else "FAIL"
    print(f"[{mark}] {label}: got={got}, expected={expected}")
    if not ok:
        sys.exit(1)


def assert_status(label: str, got: int, expected: int):
    assert_eq(label, got, expected)


def main() -> None:
    email = f"smoke_{random.randint(1000, 99999)}@example.com"
    password = "secret-пароль-123"

    print(f"=== Регистрация {email} ===")
    status, body = request("POST", "/api/auth/register", body={"email": email, "password": password})
    assert_status("register status", status, 201)
    token = body["access_token"]
    print(f"  token: {token[:40]}...")

    print("=== Повторная регистрация (ожидаем 409) ===")
    status, body = request("POST", "/api/auth/register", body={"email": email, "password": password})
    assert_status("dup-register status", status, 409)

    print("=== Логин с верным паролем ===")
    status, body = request("POST", "/api/auth/login", body={"email": email, "password": password})
    assert_status("login status", status, 200)

    print("=== Логин с неверным паролем (ожидаем 401) ===")
    status, body = request("POST", "/api/auth/login", body={"email": email, "password": "wrong"})
    assert_status("bad-login status", status, 401)

    print("=== Создание привычки ===")
    status, habit = request(
        "POST", "/api/habits",
        token=token,
        body={
            "name": "Утренняя пробежка",
            "description": "5 км",
            "color": "#4f46e5",
            "target_per_week": 5,
        },
    )
    assert_status("create-habit status", status, 201)
    habit_id = habit["id"]
    assert_eq("habit name", habit["name"], "Утренняя пробежка")

    print("=== Список привычек ===")
    status, habits = request("GET", "/api/habits", token=token)
    assert_status("list-habits status", status, 200)
    assert_eq("list length", len(habits), 1)

    print("=== Чекин на сегодня ===")
    today = date.today().isoformat()
    status, checkin = request(
        "POST", "/api/checkins",
        token=token,
        body={"habit_id": habit_id, "date": today, "note": "smoke ✓"},
    )
    assert_status("checkin status", status, 201)
    assert_eq("checkin note", checkin["note"], "smoke ✓")

    print("=== Дубликат чекина (ожидаем 409) ===")
    status, body = request(
        "POST", "/api/checkins",
        token=token,
        body={"habit_id": habit_id, "date": today, "note": "dupe"},
    )
    assert_status("dup-checkin status", status, 409)

    print("=== Статистика по привычке ===")
    status, stats = request("GET", f"/api/habits/{habit_id}/stats", token=token)
    assert_status("stats status", status, 200)
    assert_eq("total_checkins", stats["total_checkins"], 1)
    assert_eq("current_streak", stats["current_streak"], 1)
    assert_eq("longest_streak", stats["longest_streak"], 1)
    print(f"  last_30_days: {stats['last_30_days']}")

    print("=== PATCH привычки ===")
    status, updated = request(
        "PATCH", f"/api/habits/{habit_id}",
        token=token,
        body={"name": "Утренняя пробежка (5 км)"},
    )
    assert_status("patch status", status, 200)
    assert_eq("patched name", updated["name"], "Утренняя пробежка (5 км)")

    print("=== Без токена (ожидаем 401) ===")
    status, body = request("GET", "/api/habits")
    assert_status("unauth status", status, 401)

    print("=== VAPID public key ===")
    status, key = request("GET", "/api/push/public-key")
    assert_status("vapid status", status, 200)
    assert "public_key" in key

    print("=== DELETE привычки ===")
    status, body = request("DELETE", f"/api/habits/{habit_id}", token=token)
    assert_status("delete status", status, 204)

    print("=== Удаление несуществующей (ожидаем 404) ===")
    status, body = request("DELETE", f"/api/habits/{habit_id}", token=token)
    assert_status("delete-missing status", status, 404)

    print("\n=== ALL GREEN ===")


if __name__ == "__main__":
    main()
