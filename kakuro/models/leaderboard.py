from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .user import DEFAULT_DB_PATH


def _connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def add_leaderboard_entry(
    user_id: int,
    difficulty: str,
    elapsed_time: int,
    score: int,
    db_path: Path = DEFAULT_DB_PATH,
) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO leaderboard_entries (
                user_id,
                difficulty,
                elapsed_time,
                score,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                str(difficulty).lower(),
                max(0, int(elapsed_time)),
                int(score),
                datetime.now(UTC).isoformat(),
            ),
        )


def get_top_leaderboard_entries(db_path: Path = DEFAULT_DB_PATH, limit: int = 10) -> list[dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
                u.username AS username,
                e.difficulty AS difficulty,
                e.elapsed_time AS elapsed_time,
                e.score AS score,
                e.created_at AS created_at
            FROM leaderboard_entries e
            JOIN users u ON u.id = e.user_id
            ORDER BY e.score DESC, e.elapsed_time ASC, e.created_at ASC
            LIMIT ?
            """,
            (max(1, int(limit)),),
        ).fetchall()

    return [
        {
            "username": row["username"],
            "difficulty": row["difficulty"],
            "elapsedTime": int(row["elapsed_time"] or 0),
            "score": int(row["score"] or 0),
            "createdAt": row["created_at"],
        }
        for row in rows
    ]
