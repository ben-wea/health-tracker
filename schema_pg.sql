CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      TEXT      NOT NULL UNIQUE,
    password_hash TEXT      NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS meal_entries (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER NOT NULL REFERENCES users(id),
    log_date          TEXT             NOT NULL,
    meal_type         TEXT             NOT NULL CHECK (meal_type IN ('breakfast','lunch','dinner','snack')),
    fdc_id            BIGINT,
    description       TEXT             NOT NULL,
    quantity_g        DOUBLE PRECISION NOT NULL CHECK (quantity_g > 0),
    calories_per_100g DOUBLE PRECISION NOT NULL,
    protein_per_100g  DOUBLE PRECISION NOT NULL,
    carbs_per_100g    DOUBLE PRECISION NOT NULL,
    fat_per_100g      DOUBLE PRECISION NOT NULL,
    created_at        TIMESTAMP        NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workouts (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    log_date     TEXT             NOT NULL,
    exercise     TEXT             NOT NULL,
    sets         INTEGER,
    reps         INTEGER,
    weight_lbs   DOUBLE PRECISION,
    duration_min DOUBLE PRECISION,
    notes        TEXT,
    created_at   TIMESTAMP        NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_meal_entries_date ON meal_entries(log_date);
CREATE INDEX IF NOT EXISTS idx_workouts_date     ON workouts(log_date);
CREATE INDEX IF NOT EXISTS idx_meal_entries_user ON meal_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_workouts_user     ON workouts(user_id);

