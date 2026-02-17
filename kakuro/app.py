"""
Main Flask app for Iteration 1.
Supports flows: Sign Up, Log In, Start New Game, Play Game.
"""

from __future__ import annotations

from pathlib import Path

from flask_session import Session
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

from .config import Config
from .models.user import init_db
from .services.auth_service import submit_login, submit_signup
from .services.game_service import (
    clear_feedback,
    create_new_game,
    enter_number,
    get_feedback,
    get_game,
    save_game,
    set_move_error,
    submit_solution,
)


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    session_dir = Path(app.config["SESSION_FILE_DIR"])
    session_dir.mkdir(parents=True, exist_ok=True)
    Session(app)

    db_path = Path(app.config["DB_PATH"])
    schema_path = Path(app.config["SCHEMA_PATH"])
    init_db(db_path=db_path, schema_path=schema_path)

    def has_player_context() -> bool:
        return bool(session.get("is_guest") or session.get("user_id"))

    def require_player_context():
        if not has_player_context():
            flash("Please continue as guest or login first.", "warning")
            return redirect(url_for("welcome"))
        return None

    @app.context_processor
    def inject_layout_context():
        username = "Guest" if session.get("is_guest") else session.get("username")
        return {
            "current_username": username,
            "is_guest": bool(session.get("is_guest")),
            "is_logged_in": bool(session.get("user_id")),
        }

    @app.get("/")
    def welcome():
        # Flow support: entry page with guest/login/signup choices.
        if has_player_context():
            return redirect(url_for("menu"))
        return render_template("welcome.html")

    @app.post("/guest")
    def continue_as_guest():
        # Iteration 1 scope: guest users can play without an account.
        session.clear()
        session["is_guest"] = True
        session["username"] = "Guest"
        clear_feedback()
        return redirect(url_for("menu"))

    @app.get("/menu")
    def menu():
        # Flow #3 entry: Start New Game begins from the main menu.
        guard = require_player_context()
        if guard:
            return guard
        return render_template("main_menu.html")

    @app.post("/logout")
    def logout():
        # Session cleanup for both guest and logged-in users.
        session.clear()
        flash("Logged out.", "info")
        return redirect(url_for("welcome"))

    @app.get("/signup")
    def open_signup_page():
        # Diagram mapping: System Operation openSignUpPage() / SSD 1.1 displaySignUpForm().
        return render_template("signup.html")

    @app.post("/signup")
    def submit_signup_form():
        # Diagram mapping: System Operation submitSignUp(username, email, password).
        ok, message = submit_signup(
            db_path,
            request.form.get("username", ""),
            request.form.get("email", ""),
            request.form.get("password", ""),
        )

        if not ok:
            # SSD ALT path: displayError(message) and keep user on sign-up form.
            flash(message, "danger")
            return render_template(
                "signup.html",
                username=request.form.get("username", ""),
                email=request.form.get("email", ""),
            )

        # SSD success path: displaySuccess and redirectToLogin.
        flash(message, "success")
        return redirect(url_for("open_login_page"))

    @app.get("/login")
    def open_login_page():
        # Diagram mapping: System Operation openLoginPage() / SSD 1.1 displayLoginForm().
        return render_template("login.html")

    @app.post("/login")
    def submit_login_form():
        # Diagram mapping: System Operation submitLogin(email, password).
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        user = submit_login(db_path, email, password)
        if user is None:
            # SSD ALT path: invalid credentials -> error + stay on login form.
            flash("Invalid email or password.", "danger")
            return render_template("login.html", email=email)

        # Postcondition: user is marked as logged in by creating session keys.
        session.clear()
        session["user_id"] = user.userId
        session["username"] = user.username
        session["is_guest"] = False
        clear_feedback()

        flash("Login successful.", "success")
        return redirect(url_for("menu"))

    @app.get("/new-game")
    def open_new_game_page():
        # Diagram mapping: System Operation startNewGame() -> displayDifficultyOptions().
        guard = require_player_context()
        if guard:
            return guard
        return render_template("difficulty.html")

    @app.post("/new-game")
    def start_new_game():
        # Diagram mapping: System Operation selectDifficulty(difficulty).
        guard = require_player_context()
        if guard:
            return guard

        difficulty = (request.form.get("difficulty", "easy") or "easy").lower()
        if difficulty not in {"easy", "medium", "hard"}:
            # ALT path: invalid difficulty input.
            flash("Please select a valid difficulty.", "danger")
            return redirect(url_for("open_new_game_page"))

        # Postcondition: create and store a new GameSession with generated board.
        game_session = create_new_game(difficulty)
        save_game(game_session)
        clear_feedback()

        return redirect(url_for("game_screen"))

    @app.get("/game")
    def game_screen():
        # Diagram mapping: SSD 1 displayGameBoard(board).
        guard = require_player_context()
        if guard:
            return guard

        game_session = get_game()
        if game_session is None:
            # ALT path: no active game yet.
            flash("Start a new game first.", "warning")
            return redirect(url_for("open_new_game_page"))

        feedback = get_feedback()
        wrong_keys = {f"{r}-{c}" for r, c in feedback["wrongCells"]}

        return render_template(
            "game.html",
            game_session=game_session,
            board_matrix=game_session.board.matrix(),
            wrong_keys=wrong_keys,
            wrong_cells=feedback["wrongCells"],
            game_message=feedback["message"],
            move_error=feedback["moveError"],
        )

    @app.post("/game/enter")
    def enter_number_route():
        # Diagram mapping: System Operation enterNumber(row, col, value).
        game_session = get_game()
        if game_session is None:
            return _move_response(False, "No active game session.", "", request)

        try:
            row = int(request.form.get("row", "-1"))
            col = int(request.form.get("col", "-1"))
        except ValueError:
            return _move_response(False, "Invalid cell coordinates.", "", request)

        value = request.form.get("value", "")
        result = enter_number(row, col, value)

        if not result["ok"]:
            # ALT path: move rejected by coordinate/value/rule validation.
            set_move_error(result["message"])
        else:
            set_move_error("")

        return _move_response(result["ok"], result["message"], value, request)

    @app.post("/game/submit")
    def submit_solution_route():
        # Diagram mapping: System Operation submitSolution().
        result = submit_solution()
        if not result.get("ok"):
            # ALT path: submit attempted without active session.
            flash(result["message"], "danger")
            return redirect(url_for("game_screen"))

        if result["isSolved"]:
            # Success path: solved board.
            flash("Win! Puzzle solved correctly.", "success")
        else:
            # ALT path: not solved/incorrect with wrong-cell highlight feedback.
            flash("Not solved / incorrect. Wrong cells are highlighted.", "danger")

        return redirect(url_for("game_screen"))

    return app


def _move_response(ok: bool, message: str, value: str, req):
    if req.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": ok, "message": message, "value": value})

    if ok:
        flash(message, "info")
    else:
        flash(message, "danger")
    return redirect(url_for("game_screen"))
