# Habit Tracker PWA

Трекер привычек в формате PWA. **FastAPI + PostgreSQL** на бэкенде,
**чистый JavaScript без фреймворков** на фронте, **полный PWA** (manifest,
service worker, **Web Push с VAPID**, установка на главный экран).

Бэкенд и фронтенд лежат в одном репозитории — FastAPI раздаёт и API,
и статику фронта.

> **Статус:** пет-проект, публичного демо нет — запускается локально
> по инструкции [«Запуск локально»](#запуск-локально) (Docker + uvicorn,
> 4 шага). Smoke-тест `smoke_test.py` покрывает register / login / CRUD /
> checkin / stats / auth — 18 ассертов, все зелёные.

## Стек

| Слой | Технологии |
|---|---|
| Язык | Python 3.11+, полностью async/await |
| Веб-фреймворк | FastAPI 0.115 + Uvicorn |
| База | PostgreSQL 16 + asyncpg (без ORM, чистый SQL) |
| Миграции | Идемпотентный DDL при старте (`CREATE TABLE IF NOT EXISTS`) |
| Auth | JWT (`python-jose`) + bcrypt (`passlib`) |
| Web Push | VAPID + `pywebpush`, генерация ключей через `cryptography` |
| Фронт | Vanilla JS (ES-модули), HTML, CSS — без сборщика, без фреймворков |
| PWA | manifest.json, service worker, offline-fallback, install prompt |
| Конфиг | `.env` + `python-dotenv`, типизированный dataclass |

## Что умеет

- Регистрация и вход (email + пароль, JWT в `Authorization: Bearer`).
- CRUD привычек с цветом, описанием и целью «дней в неделю».
- Отметка выполнения за день, удаление отметки.
- Статистика: текущий стрик, максимальный, всего выполнений,
  визуальный календарь последних 30 дней.
- Push-уведомления через VAPID: подписка прямо из браузера,
  отправка с сервера через `pywebpush`.
- Установка как нативное приложение на десктоп и мобильный
  (manifest + maskable иконки).
- Офлайн-режим: статика кешируется service worker'ом,
  навигация фолбэчится на закешированный shell.

## Структура

```
habit-tracker-pwa/
├── docker-compose.yml          # PostgreSQL для локальной разработки
├── requirements.txt
├── .env.example
├── app/                        # Backend
│   ├── main.py                 # FastAPI app, lifespan, монтирование статики
│   ├── config.py               # Загрузка env, типизированный AppConfig
│   ├── database.py             # asyncpg pool, прогон DDL при старте
│   ├── models.py               # SQL-схема (users, habits, checkins, push_subscriptions)
│   ├── schemas.py              # Pydantic запросы/ответы
│   ├── auth.py                 # bcrypt + JWT + dependency для текущего юзера
│   ├── push.py                 # Обёртка над pywebpush
│   ├── routes/
│   │   ├── auth_routes.py      # /api/auth/register, /login
│   │   ├── habits_routes.py    # /api/habits CRUD
│   │   ├── checkins_routes.py  # /api/checkins + /habits/{id}/stats
│   │   └── push_routes.py      # /api/push/subscribe, /test, /public-key
│   └── scripts/
│       └── generate_vapid.py   # Генерация VAPID-пары ключей
└── static/                     # Frontend
    ├── index.html              # SPA shell с двумя экранами (auth / app) + модалки
    ├── manifest.json           # PWA manifest
    ├── service-worker.js       # Cache-first статика + push handler
    ├── icons/                  # 192 и 512 PNG (maskable)
    ├── css/
    │   └── style.css           # Адаптивный CSS, dark mode через prefers-color-scheme
    └── js/                     # ES-модули, без сборщика
        ├── app.js              # Главный контроллер, роутинг экранов
        ├── api.js              # Fetch-обёртка с авто-JWT
        ├── auth.js             # Логика login/register
        ├── habits.js           # Список привычек, чекин
        ├── stats.js            # Модалка со стриком и календарём
        ├── push.js             # PushManager.subscribe + VAPID
        ├── install.js          # beforeinstallprompt
        └── toast.js            # Тост-уведомления
```

## REST API

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/auth/register` | Регистрация, возвращает JWT |
| `POST` | `/api/auth/login` | Вход, возвращает JWT |
| `GET` | `/api/habits` | Список привычек текущего юзера |
| `POST` | `/api/habits` | Создать привычку |
| `PATCH` | `/api/habits/{id}` | Обновить привычку (частично) |
| `DELETE` | `/api/habits/{id}` | Удалить (каскадом сносятся checkins) |
| `POST` | `/api/checkins` | Отметить день |
| `DELETE` | `/api/checkins/{id}` | Снять отметку |
| `GET` | `/api/habits/{id}/checkins?days=N` | История чекинов |
| `GET` | `/api/habits/{id}/stats` | Стрики + последние 30 дней |
| `GET` | `/api/push/public-key` | VAPID public key (для фронта) |
| `POST` | `/api/push/subscribe` | Сохранить подписку браузера |
| `POST` | `/api/push/test` | Послать тестовый пуш всем подпискам |
| `GET` | `/api/health` | Health-check |

Все защищённые роуты требуют `Authorization: Bearer <jwt>`.
Полный OpenAPI — `/docs` (Swagger UI) после запуска.

## Запуск локально

### 1. Зависимости

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
# или: source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

### 2. PostgreSQL

```bash
cp .env.example .env
# заполнить DB_PASSWORD и JWT_SECRET (генерация: python -c "import secrets; print(secrets.token_urlsafe(48))")
docker compose up -d
```

### 3. VAPID-ключи (для push)

```bash
python -m app.scripts.generate_vapid
# скопировать вывод в .env (VAPID_PUBLIC_KEY и VAPID_PRIVATE_KEY)
```

Без ключей всё работает, кроме пушей — кнопка «включить уведомления»
вернёт 503.

### 4. Старт

```bash
uvicorn app.main:app --reload
# или: python -m app.main
```

Открыть `http://localhost:8000`. При первом старте автоматически
создаются все таблицы.

## Безопасность и эксплуатация

- Пароли — bcrypt-хеш через passlib (не plain).
- JWT — HS256, секрет в env, дефолтное время жизни 24 часа.
- Все секреты в `.env`, `.env` в `.gitignore`.
- VAPID-ключи генерируются локально, в репозиторий не попадают.
- При недоступности БД startup не запускает приложение — раннее падение,
  понятная ошибка.

## Известные ограничения

- Email-валидация только формальная (Pydantic `EmailStr`), без отправки
  подтверждения.
- Нет refresh-токенов — после истечения access нужно логиниться заново.
- Нет rate-limit на регистрацию (для прод-деплоя — добавить через slowapi
  или прокси-уровень).
- Cron-уведомления по привычкам не реализованы — есть только эндпоинт
  тестового пуша. Регулярные напоминания — следующий этап (APScheduler).
