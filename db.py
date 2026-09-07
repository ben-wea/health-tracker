import os
import sqlite3

USE_POSTGRES = bool(os.getenv("DATABASE_URL"))
DATABASE = "health_tracker.db"

if USE_POSTGRES:
    import psycopg
    from psycopg.rows import dict_row

# Postgres uses %s placeholders; SQLite uses ?.
PH = "%s" if USE_POSTGRES else "?"


def get_connection():
    """Open a connection to whichever database this environment uses."""
    if USE_POSTGRES:
        return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def run_query(sql, params=(), fetch=None):
    """Execute a statement against either backend.

    fetch: None for writes, 'one' for a single row, 'all' for a list.
    """
    conn = get_connection()
    result = None
    try:
        if USE_POSTGRES:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if fetch == "one":
                    result = cur.fetchone()
                elif fetch == "all":
                    result = cur.fetchall()
        else:
            cur = conn.execute(sql, params)
            if fetch == "one":
                result = cur.fetchone()
            elif fetch == "all":
                result = cur.fetchall()
        conn.commit()
    finally:
        conn.close()
    return result


def init_db():
    """Create tables if they do not already exist."""
    filename = "schema_pg.sql" if USE_POSTGRES else "schema.sql"
    with open(filename, "r") as f:
        schema = f.read()

    conn = get_connection()
    try:
        if USE_POSTGRES:
            with conn.cursor() as cur:
                cur.execute(schema)
        else:
            conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()
    print(f"Initialized using {filename}")


def reset_db():
    """Drop all tables and recreate them. Destructive."""
    conn = get_connection()
    try:
        statements = "DROP TABLE IF EXISTS meal_entries; DROP TABLE IF EXISTS workouts;"
        if USE_POSTGRES:
            with conn.cursor() as cur:
                cur.execute(statements)
        else:
            conn.executescript(statements)
        conn.commit()
    finally:
        conn.close()
    init_db()
    print("Reset complete.")


def add_meal_entry(user_id, log_date, meal_type, fdc_id, description, quantity_g,
                   calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g):
    """Insert one logged food item for a user. Returns the new row's id."""
    sql = f"""
        INSERT INTO meal_entries
            (user_id, log_date, meal_type, fdc_id, description, quantity_g,
             calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g)
        VALUES ({PH}, {PH}, {PH}, {PH}, {PH}, {PH}, {PH}, {PH}, {PH}, {PH})
        RETURNING id
    """
    row = run_query(
        sql,
        (user_id, log_date, meal_type, fdc_id, description, quantity_g,
         calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g),
        fetch="one",
    )
    return row["id"]


def get_meal_entries(user_id, log_date):
    """Return all meal entries for a user on a date, with consumed amounts computed."""
    sql = f"""
        SELECT
            id,
            meal_type,
            description,
            quantity_g,
            calories_per_100g * quantity_g / 100 AS calories,
            protein_per_100g  * quantity_g / 100 AS protein,
            carbs_per_100g    * quantity_g / 100 AS carbs,
            fat_per_100g      * quantity_g / 100 AS fat
        FROM meal_entries
        WHERE user_id = {PH} AND log_date = {PH}
        ORDER BY
            CASE meal_type
                WHEN 'breakfast' THEN 1
                WHEN 'lunch'     THEN 2
                WHEN 'dinner'    THEN 3
                WHEN 'snack'     THEN 4
            END,
            created_at
    """
    return run_query(sql, (user_id, log_date), fetch="all")


def get_daily_totals(user_id, log_date):
    """Return summed calories and macros for a user on a date."""
    sql = f"""
        SELECT
            COALESCE(SUM(calories_per_100g * quantity_g / 100), 0) AS calories,
            COALESCE(SUM(protein_per_100g  * quantity_g / 100), 0) AS protein,
            COALESCE(SUM(carbs_per_100g    * quantity_g / 100), 0) AS carbs,
            COALESCE(SUM(fat_per_100g      * quantity_g / 100), 0) AS fat
        FROM meal_entries
        WHERE user_id = {PH} AND log_date = {PH}
    """
    return run_query(sql, (user_id, log_date), fetch="one")


def get_daily_summaries(user_id, days=7):
    """Return per-day totals for a user's most recent `days` dates with entries."""
    sql = f"""
        SELECT
            log_date,
            COUNT(*)                                   AS entry_count,
            SUM(calories_per_100g * quantity_g / 100)  AS calories,
            SUM(protein_per_100g  * quantity_g / 100)  AS protein,
            SUM(carbs_per_100g    * quantity_g / 100)  AS carbs,
            SUM(fat_per_100g      * quantity_g / 100)  AS fat
        FROM meal_entries
        WHERE user_id = {PH}
        GROUP BY log_date
        ORDER BY log_date DESC
        LIMIT {PH}
    """
    return run_query(sql, (user_id, days), fetch="all")


def delete_meal_entry(user_id, entry_id):
    """Delete one meal entry, but only if it belongs to this user."""
    sql = f"DELETE FROM meal_entries WHERE id = {PH} AND user_id = {PH}"
    run_query(sql, (entry_id, user_id))


def create_user(username, password_hash):
    """Insert a new user. Returns the new user's id."""
    sql = f"""
        INSERT INTO users (username, password_hash)
        VALUES ({PH}, {PH})
        RETURNING id
    """
    row = run_query(sql, (username, password_hash), fetch="one")
    return row["id"]


def get_user_by_username(username):
    """Return a user row, or None if no such username exists."""
    sql = f"SELECT id, username, password_hash FROM users WHERE username = {PH}"
    return run_query(sql, (username,), fetch="one")