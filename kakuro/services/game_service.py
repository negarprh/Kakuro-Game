"""
Game session service for Iteration 1 gameplay.
Supports flows: Start New Game and Play Game.
"""

from __future__ import annotations

import uuid

from flask import session as flask_session

from ..models.domain import GameSession, Result
from .board_generator import generate_board
from .validation_service import validate_entire_board, validate_move

GAME_KEY = "active_game"
WRONG_CELLS_KEY = "wrong_cells"
MESSAGE_KEY = "game_message"
MOVE_ERROR_KEY = "move_error"


def create_new_game(difficulty: str) -> GameSession:
    # Diagram mapping: selectDifficulty(difficulty) creates a fresh board/session.
    board = generate_board(difficulty)
    return GameSession(
        sessionId=f"gs-{uuid.uuid4().hex[:12]}",
        difficulty=difficulty,
        status="InProgress",
        board=board,
        result=None,
    )


def save_game(game_session: GameSession) -> None:
    # Postcondition: active GameSession is stored in server session state.
    flask_session[GAME_KEY] = game_session.to_dict()


def get_game() -> GameSession | None:
    return GameSession.from_dict(flask_session.get(GAME_KEY))


def clear_feedback() -> None:
    # Reset UI feedback for next move/check cycle.
    flask_session[WRONG_CELLS_KEY] = []
    flask_session[MESSAGE_KEY] = ""
    flask_session[MOVE_ERROR_KEY] = ""


def set_feedback(wrong_cells: list[tuple[int, int]], message: str) -> None:
    flask_session[WRONG_CELLS_KEY] = [[r, c] for r, c in wrong_cells]
    flask_session[MESSAGE_KEY] = message


def set_move_error(message: str) -> None:
    flask_session[MOVE_ERROR_KEY] = message


def get_feedback() -> dict:
    wrong_cells = [tuple(item) for item in flask_session.get(WRONG_CELLS_KEY, [])]
    return {
        "wrongCells": wrong_cells,
        "message": flask_session.get(MESSAGE_KEY, ""),
        "moveError": flask_session.get(MOVE_ERROR_KEY, ""),
    }


def enter_number(row: int, col: int, raw_value: str) -> dict:
    # Diagram mapping: enterNumber(row, col, value).
    game_session = get_game()
    if game_session is None:
        return {"ok": False, "message": "No active game session."}

    if game_session.status == "Finished":
        return {
            "ok": False,
            "message": "Game is finished. Start a new game.",
        }

    result = validate_move(game_session.board, row, col, raw_value)
    if result["ok"]:
        # Postcondition: cell update is persisted in active session.
        save_game(game_session)
        clear_feedback()
    return result


def submit_solution() -> dict:
    # Diagram mapping: submitSolution() with win/error branches.
    game_session = get_game()
    if game_session is None:
        return {"ok": False, "message": "No active game session."}

    result = validate_entire_board(game_session.board)
    if result["isSolved"]:
        # Success path: mark game finished and store win result.
        game_session.status = "Finished"
        game_session.result = Result(resultId=f"res-{uuid.uuid4().hex[:10]}", isWin=True)
    else:
        # ALT path: keep game in progress and return wrong-cell feedback.
        game_session.status = "InProgress"
        game_session.result = None

    save_game(game_session)
    set_feedback(result["wrongCells"], result["message"])
    set_move_error("")

    return {
        "ok": True,
        "isSolved": result["isSolved"],
        "message": result["message"],
        "wrongCells": result["wrongCells"],
    }
