from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..services.board_service import generate_new_game
from ..services.validation_service import apply_form_values, validate_board


game_bp = Blueprint("game", __name__, url_prefix="/game")


def _require_mode():
    if session.get("user_mode") not in {"guest", "registered"}:
        flash("Please continue as guest or log in first.", "warning")
        return redirect(url_for("main.welcome"))
    return None


def _error_key_set(error_cells):
    return {f"{r}-{c}" for r, c in error_cells}


@game_bp.get("/menu")
def menu():
    guard = _require_mode()
    if guard:
        return guard

    return render_template("menu.html")


@game_bp.get("/difficulty")
def difficulty():
    guard = _require_mode()
    if guard:
        return guard

    return render_template("difficulty.html")


@game_bp.post("/start")
def start_new_game():
    guard = _require_mode()
    if guard:
        return guard

    difficulty = request.form.get("difficulty", "easy").lower()
    try:
        game_data = generate_new_game(difficulty)
    except ValueError:
        flash("Invalid difficulty selected.", "danger")
        return redirect(url_for("game.difficulty"))

    session["difficulty"] = difficulty
    session["current_board"] = game_data["board"]
    session["current_solution"] = game_data["solution"]

    return redirect(url_for("game.play"))


@game_bp.get("/play")
def play():
    guard = _require_mode()
    if guard:
        return guard

    board = session.get("current_board")
    if not board:
        flash("Start a new game first.", "warning")
        return redirect(url_for("game.difficulty"))

    return render_template(
        "game.html",
        board=board,
        difficulty=session.get("difficulty", "easy"),
        errors=[],
        error_keys=set(),
    )


@game_bp.post("/submit")
def submit():
    guard = _require_mode()
    if guard:
        return guard

    board = session.get("current_board")
    if not board:
        flash("No active game found.", "warning")
        return redirect(url_for("game.difficulty"))

    apply_form_values(board, request.form)
    result = validate_board(board)
    session["current_board"] = board

    if result["is_win"]:
        flash("You solved the puzzle. Congratulations!", "success")
    elif result["errors"]:
        flash("Puzzle has validation issues.", "danger")
    else:
        flash("Board checked.", "info")

    return render_template(
        "game.html",
        board=board,
        difficulty=session.get("difficulty", "easy"),
        errors=result["errors"],
        error_keys=_error_key_set(result.get("error_cells", [])),
    )


@game_bp.get("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")
