import sqlite3

from kakuro.models.domain import Board, Cell, GameSession
from kakuro.models.leaderboard import add_leaderboard_entry
from kakuro.models.user import create_user
from kakuro.services.leaderboard_service import calculate_score


def _board_3x3() -> Board:
    cells = [
        Cell(0, 0, None, False, None, None),
        Cell(0, 1, None, False, 4, None),
        Cell(0, 2, None, False, 3, None),
        Cell(1, 0, None, False, None, 4),
        Cell(1, 1, None, True, None, None),
        Cell(1, 2, None, True, None, None),
        Cell(2, 0, None, False, None, 3),
        Cell(2, 1, None, True, None, None),
        Cell(2, 2, None, True, None, None),
    ]
    return Board(boardId="b-lb", difficulty="easy", size=(3, 3), cells=cells)


def _set_guest(client) -> None:
    with client.session_transaction() as sess:
        sess["is_guest"] = True
        sess["username"] = "Guest"


def _set_registered(client, app):
    user = create_user("ranker", "ranker@example.com", "hash", app.config["DB_PATH"])
    with client.session_transaction() as sess:
        sess["user_id"] = user.userId
        sess["username"] = user.username
        sess["is_guest"] = False
    return user


def _put_solved_game_in_session(client, user_id=None) -> None:
    board = _board_3x3()
    board.get_cell(1, 1).value = 3
    board.get_cell(1, 2).value = 1
    board.get_cell(2, 1).value = 1
    board.get_cell(2, 2).value = 2
    game = GameSession(
        sessionId="gs-lb-win",
        difficulty="easy",
        status="InProgress",
        board=board,
        userId=user_id,
        elapsedTime=0,
        result=None,
    )
    with client.session_transaction() as sess:
        sess["active_game"] = game.to_dict()


def test_registered_win_records_leaderboard_score(client, app):
    user = _set_registered(client, app)
    _put_solved_game_in_session(client, user.userId)

    response = client.post("/game/submit", data={"elapsed_time": "125"}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/menu")

    with sqlite3.connect(app.config["DB_PATH"]) as conn:
        row = conn.execute(
            """
            SELECT user_id, difficulty, elapsed_time, score
            FROM leaderboard_entries
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    assert row is not None
    assert row[0] == user.userId
    assert row[1] == "easy"
    assert row[2] == 125
    assert row[3] == calculate_score("easy", 125)


def test_guest_win_does_not_enter_leaderboard(client, app):
    _set_guest(client)
    _put_solved_game_in_session(client, None)

    response = client.post("/game/submit", data={"elapsed_time": "90"}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/menu")

    with sqlite3.connect(app.config["DB_PATH"]) as conn:
        count = conn.execute("SELECT COUNT(*) FROM leaderboard_entries").fetchone()[0]

    assert count == 0


def test_guest_can_see_leaderboard_on_main_menu(client, app):
    db_path = app.config["DB_PATH"]
    user = create_user("tableuser", "tableuser@example.com", "hash", db_path)
    add_leaderboard_entry(
        user_id=user.userId,
        difficulty="medium",
        elapsed_time=210,
        score=calculate_score("medium", 210),
        db_path=db_path,
    )
    _set_guest(client)

    response = client.get("/menu")
    assert response.status_code == 200
    assert b"Leaderboard" in response.data
    assert b"tableuser" in response.data
