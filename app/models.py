"""SQL-схема базы. DDL прогоняется при старте приложения."""

# Идемпотентные CREATE — безопасны при каждом запуске.
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS habits (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    description     TEXT,
    color           TEXT DEFAULT '#4f46e5',
    target_per_week SMALLINT NOT NULL DEFAULT 7,
    is_archived     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS checkins (
    id         SERIAL PRIMARY KEY,
    habit_id   INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    date       DATE NOT NULL,
    note       TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(habit_id, date)
);

CREATE TABLE IF NOT EXISTS push_subscriptions (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint   TEXT UNIQUE NOT NULL,
    p256dh     TEXT NOT NULL,
    auth       TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_habits_user_id     ON habits(user_id);
CREATE INDEX IF NOT EXISTS idx_checkins_habit_id  ON checkins(habit_id);
CREATE INDEX IF NOT EXISTS idx_checkins_date      ON checkins(date DESC);
CREATE INDEX IF NOT EXISTS idx_push_user_id       ON push_subscriptions(user_id);
"""
