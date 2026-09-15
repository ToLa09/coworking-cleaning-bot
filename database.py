import sqlite3
from pathlib import Path

DATABASE = Path("data/bot.sqlite")

def get_connection():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection

def initialize_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL UNIQUE,
                first_name TEXT NOT NULL,
                last_name TEXT,
                username TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cleanings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS participations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cleaning_id INTEGER NOT NULL,
                member_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(cleaning_id, member_id),
                FOREIGN KEY(cleaning_id)
                    REFERENCES cleanings(id),
                FOREIGN KEY(member_id)
                    REFERENCES members(id)
            )
            """
        )

def add_member(
    telegram_id: int,
    first_name: str,
    last_name: str | None,
    username: str | None,
):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO members (
                telegram_id,
                first_name,
                last_name,
                username
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                telegram_id,
                first_name,
                last_name,
                username,
            ),
        )

def get_member(telegram_id: int):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM members
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()

def get_all_members():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM members
            ORDER BY first_name
            """
        ).fetchall()
