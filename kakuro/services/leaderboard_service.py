from __future__ import annotations

from pathlib import Path

from ..models.domain import GameSession
from ..models.leaderboard import add_leaderboard_entry, get_top_leaderboard_entries


DIFFICULTY_BASE_POINTS = {
    "easy": 800,
    "medium": 1400,
    "hard": 2200,
}

MAX_SPEED_BONUS_SECONDS = 1800


def calculate_score(difficulty: str, elapsed_time: int) -> int:
    normalized = str(difficulty or "easy").strip().lower()
    base_points = DIFFICULTY_BASE_POINTS.get(normalized, DIFFICULTY_BASE_POINTS["easy"])
    speed_bonus = max(0, MAX_SPEED_BONUS_SECONDS - max(0, int(elapsed_time)))
    return int(base_points + speed_bonus)


def record_completed_game(db_path: Path, user_id: int | None, game_session: GameSession | None) -> int | None:
    if not user_id or game_session is None:
        return None

    if game_session.status != "Finished":
        return None

    if not game_session.result or not game_session.result.isWin:
        return None

    score = calculate_score(game_session.difficulty, game_session.elapsedTime)
    add_leaderboard_entry(
        user_id=user_id,
        difficulty=game_session.difficulty,
        elapsed_time=game_session.elapsedTime,
        score=score,
        db_path=db_path,
    )
    return score


def get_leaderboard(db_path: Path, limit: int = 10) -> list[dict]:
    entries = get_top_leaderboard_entries(db_path=db_path, limit=limit)
    for idx, entry in enumerate(entries, start=1):
        entry["rank"] = idx
    return entries
