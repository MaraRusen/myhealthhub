"""SQLite layer for persistent user actions.

Evolution from DanceFinder (which used SQLite for community ratings) — here we use it
to persist reminders, claim submissions, and chat history across sessions.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "myhealthhub.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                appointment_id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS claim_submissions (
                claim_id TEXT PRIMARY KEY,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'submitted'
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


# ---------------------------------------------------------------- reminders
def set_reminder(appointment_id: str, email: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO reminders (appointment_id, email) VALUES (?, ?)",
            (appointment_id, email),
        )


def get_reminders() -> set[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT appointment_id FROM reminders").fetchall()
        return {row["appointment_id"] for row in rows}


def clear_reminder(appointment_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM reminders WHERE appointment_id = ?", (appointment_id,))


# ---------------------------------------------------------------- claims
def mark_claim_submitted(claim_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO claim_submissions (claim_id, status) VALUES (?, 'submitted')",
            (claim_id,),
        )


def get_submitted_claims() -> set[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT claim_id FROM claim_submissions").fetchall()
        return {row["claim_id"] for row in rows}


# ---------------------------------------------------------------- chat history
def save_chat_message(role: str, content: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO chat_history (role, content) VALUES (?, ?)",
            (role, content),
        )


def load_chat_history(limit: int = 20) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM chat_history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


def clear_chat_history() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM chat_history")


# ---------------------------------------------------------------- stats for Insights tab
def count_reminders() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM reminders").fetchone()
        return row["c"] if row else 0


def count_chat_messages() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM chat_history").fetchone()
        return row["c"] if row else 0
