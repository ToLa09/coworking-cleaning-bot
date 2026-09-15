import sqlite3
from datetime import date, timedelta
from pathlib import Path

from config import CLEANING_INTERVAL_WEEKS

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

def get_open_cleaning():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM cleanings
            WHERE status = 'OPEN'
            ORDER BY start_date DESC
            LIMIT 1
            """
        ).fetchone()

def create_cleaning(start_date: str, end_date: str):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO cleanings (
                start_date,
                end_date
            )
            VALUES (?, ?)
            """,
            (start_date, end_date),
        )
        return cursor.lastrowid

def get_cleaning(cleaning_id: int):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM cleanings
            WHERE id = ?
            """,
            (cleaning_id,),
        ).fetchone()

def complete_cleaning(cleaning_id: int):
    with get_connection() as connection:
        cleaning = connection.execute(
            """
            SELECT *
            FROM cleanings
            WHERE id = ?
            """,
            (cleaning_id,),
        ).fetchone()
        if not cleaning:
            return None
        if cleaning["status"] != "OPEN":
            return None

        connection.execute(
            """
            UPDATE cleanings
            SET status = 'COMPLETED'
            WHERE id = ?
            """,
            (cleaning_id,),
        )
        start_date = date.fromisoformat(cleaning["start_date"])
        end_date = date.fromisoformat(cleaning["end_date"])

        new_start_date = start_date + timedelta(
            weeks=CLEANING_INTERVAL_WEEKS
        )
        new_end_date = end_date + timedelta(
            weeks=CLEANING_INTERVAL_WEEKS
        )
        cursor = connection.execute(
            """
            INSERT INTO cleanings (
                start_date,
                end_date
            )
            VALUES (?, ?)
            """,
            (
                new_start_date.isoformat(),
                new_end_date.isoformat(),
            ),
        )
        return cursor.lastrowid

def add_participation(cleaning_id: int, member_id: int):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO participations (
                cleaning_id,
                member_id
            )
            VALUES (?, ?)
            """,
            (cleaning_id, member_id),
        )

def get_participants(cleaning_id: int):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT members.*
            FROM members
            JOIN participations
                ON participations.member_id = members.id
            WHERE participations.cleaning_id = ?
            ORDER BY participations.created_at
            """,
            (cleaning_id,),
        ).fetchall()

def is_participating(cleaning_id: int, member_id: int):
    with get_connection() as connection:
        participation = connection.execute(
            """
            SELECT 1
            FROM participations
            WHERE cleaning_id = ?
              AND member_id = ?
            """,
            (cleaning_id, member_id),
        ).fetchone()
        return participation is not None

if __name__ == "__main__":
    initialize_database()

    cleaning = get_open_cleaning()

    if cleaning is None:
        cleaning_id = create_cleaning(
            "2026-09-14",
            "2026-09-20",
        )
    else:
        cleaning_id = cleaning["id"]

    print("Reinigung:", cleaning_id)