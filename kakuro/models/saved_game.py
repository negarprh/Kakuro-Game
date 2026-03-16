from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

from .domain import GameSession, SavedGame
from .user import DEFAULT_DB_PATH


def _connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def upsert_saved_game(game_session: GameSession, db_path: Path = DEFAULT_DB_PATH) -> None:
    if game_session.userId is None:
        raise ValueError("Cannot save game without a user id.")

    saved_at = datetime.now(UTC).isoformat()
    board_state = json.dumps(game_session.board.to_dict(), separators=(",", ":"))

    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO saved_games (
                session_id,
                user_id,
                board_state,
                difficulty,
                elapsed_time,
                status,
                saved_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                user_id = excluded.user_id,
                board_state = excluded.board_state,
                difficulty = excluded.difficulty,
                elapsed_time = excluded.elapsed_time,
                status = excluded.status,
                saved_at = excluded.saved_at
            """,
            (
                game_session.sessionId,
                game_session.userId,
                board_state,
                str(game_session.difficulty),
                int(game_session.elapsedTime),
                game_session.status,
                saved_at,
            ),
        )


def get_latest_saved_game_for_user(user_id: int, db_path: Path = DEFAULT_DB_PATH) -> Optional[GameSession]:
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT session_id, user_id, board_state, difficulty, elapsed_time, status
            FROM saved_games
            WHERE user_id = ?
            ORDER BY saved_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

    if row is None:
        return None

    saved_game = SavedGame(
        saveId=None,
        sessionId=row["session_id"],
        userId=row["user_id"],
        boardState=json.loads(row["board_state"]),
        difficulty=row["difficulty"],
        elapsedTime=int(row["elapsed_time"] or 0),
        status=row["status"],
        savedAt="",
    )
    return saved_game.restore()
