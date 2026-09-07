import sqlite3

DATABASE = "health_tracker.db"


def get_connection():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the database tables by running schema.sql."""
    with open("schema.sql", "r") as f:
        schema = f.read()
    conn = get_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()
    print(f"Initialized {DATABASE}")


def add_meal_entry(log_date, meal_type, fdc_id, description, quantity_g,
                   calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g):
    """Insert one logged food item. Returns the new row's id."""
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO meal_entries
            (log_date, meal_type, fdc_id, description, quantity_g,
             calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (log_date, meal_type, fdc_id, description, quantity_g,
         calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_meal_entries(log_date):
    """Return all meal entries for a date, with consumed amounts computed."""
    conn = get_connection()
    rows = conn.execute(
        """
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
        WHERE log_date = ?
        ORDER BY
            CASE meal_type
                WHEN 'breakfast' THEN 1
                WHEN 'lunch'     THEN 2
                WHEN 'dinner'    THEN 3
                WHEN 'snack'     THEN 4
            END,
            created_at
        """,
        (log_date,),
    ).fetchall()
    conn.close()
    return rows


def get_daily_totals(log_date):
    """Return summed calories and macros for a date."""
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            COALESCE(SUM(calories_per_100g * quantity_g / 100), 0) AS calories,
            COALESCE(SUM(protein_per_100g  * quantity_g / 100), 0) AS protein,
            COALESCE(SUM(carbs_per_100g    * quantity_g / 100), 0) AS carbs,
            COALESCE(SUM(fat_per_100g      * quantity_g / 100), 0) AS fat
        FROM meal_entries
        WHERE log_date = ?
        """,
        (log_date,),
    ).fetchone()
    conn.close()
    return row


def delete_meal_entry(entry_id):
    """Delete one meal entry by id."""
    conn = get_connection()
    conn.execute("DELETE FROM meal_entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

def get_daily_summaries(days=7):
    """Return per-day totals for the most recent `days` dates that have entries."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            log_date,
            COUNT(*)                                   AS entry_count,
            SUM(calories_per_100g * quantity_g / 100)  AS calories,
            SUM(protein_per_100g  * quantity_g / 100)  AS protein,
            SUM(carbs_per_100g    * quantity_g / 100)  AS carbs,
            SUM(fat_per_100g      * quantity_g / 100)  AS fat
        FROM meal_entries
        GROUP BY log_date
        ORDER BY log_date DESC
        LIMIT ?
        """,
        (days,),
    ).fetchall()
    conn.close()
    return rows