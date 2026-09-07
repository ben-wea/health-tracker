-- Health Tracker schema
-- Nutrition values are stored per 100g as returned by the USDA API.
-- Actual consumed amounts are computed at query time from quantity_g.



CREATE TABLE IF NOT EXISTS meal_entries (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    log_date          TEXT    NOT NULL,
    meal_type         TEXT    NOT NULL CHECK (meal_type IN ('breakfast','lunch','dinner','snack')),
    fdc_id            INTEGER,
    description       TEXT    NOT NULL,
    quantity_g        REAL    NOT NULL CHECK (quantity_g > 0),
    calories_per_100g REAL    NOT NULL,
    protein_per_100g  REAL    NOT NULL,
    carbs_per_100g    REAL    NOT NULL,
    fat_per_100g      REAL    NOT NULL,
    created_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS workouts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    log_date     TEXT    NOT NULL,
    exercise     TEXT    NOT NULL,
    sets         INTEGER,
    reps         INTEGER,
    weight_lbs   REAL,
    duration_min REAL,
    notes        TEXT,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_meal_entries_date ON meal_entries(log_date);
CREATE INDEX IF NOT EXISTS idx_workouts_date     ON workouts(log_date);
CREATE INDEX IF NOT EXISTS idx_meal_entries_user ON meal_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_workouts_user     ON workouts(user_id);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);