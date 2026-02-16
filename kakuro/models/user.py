from __future__ import annotations

import sqlite3
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

from .domain import User


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "db" / "kakuro.sqlite"
DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "db" / "schema.sql"


def _connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH, schema_path: Path = DEFAULT_SCHEMA_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        schema_sql = schema_path.read_text(encoding="utf-8")
        conn.executescript(schema_sql)


def _row_to_user(row: Optional[sqlite3.Row]) -> Optional[User]:
    if row is None:
        return None
    return User(
        userId=row["id"],
        username=row["username"],
        email=row["email"],
        passwordHash=row["password_hash"],
    )


def get_user_by_id(user_id: int, db_path: Path = DEFAULT_DB_PATH) -> Optional[User]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT id, username, email, password_hash FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return _row_to_user(row)


def get_user_by_username(username: str, db_path: Path = DEFAULT_DB_PATH) -> Optional[User]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT id, username, email, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    return _row_to_user(row)


def get_user_by_email(email: str, db_path: Path = DEFAULT_DB_PATH) -> Optional[User]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT id, username, email, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    return _row_to_user(row)


def create_user(username: str, email: str, password_hash: str, db_path: Path = DEFAULT_DB_PATH) -> User:
    created_at = datetime.now(UTC).isoformat()
    with _connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, password_hash, created_at),
        )
        user_id = cursor.lastrowid
    return User(userId=user_id, username=username, email=email, passwordHash=password_hash)
