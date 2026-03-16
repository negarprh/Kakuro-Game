import sqlite3

from kakuro.models.domain import Board, Cell, GameSession
from kakuro.models.saved_game import upsert_saved_game
from kakuro.models.user import create_user


def _board_3x3() -> Board:
    # Layout:
    # B  Cd4 Cd3
    # Cr4 P   P
    # Cr3 P   P
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
    return Board(boardId="b-test", difficulty="easy", size=(3, 3), cells=cells)


def _set_guest(client) -> None:
    with client.session_transaction() as sess:
        sess["is_guest"] = True
        sess["username"] = "Guest"


def _set_registered(client, app):
    db_path = app.config["DB_PATH"]
    user = create_user("player1", "player1@example.com", "hash", db_path)
    with client.session_transaction() as sess:
        sess["user_id"] = user.userId
        sess["username"] = user.username
        sess["is_guest"] = False
    return user


def test_submit_incorrect_keeps_game_in_progress(client):
    _set_guest(client)
    board = _board_3x3()

    board.get_cell(1, 1).value = 2
    board.get_cell(1, 2).value = 2
    board.get_cell(2, 1).value = 1
    board.get_cell(2, 2).value = 1

    game = GameSession(
        sessionId="gs-test-incorrect",
        difficulty="easy",
        status="InProgress",
        board=board,
        result=None,
    )

    with client.session_transaction() as sess:
        sess["active_game"] = game.to_dict()

    response = client.post("/game/submit", follow_redirects=False)

    assert response.status_code == 302
    with client.session_transaction() as sess:
        stored = GameSession.from_dict(sess["active_game"])
        assert stored is not None
        assert stored.status == "InProgress"
        assert stored.result is None
        assert len(sess.get("wrong_cells", [])) > 0


def test_submit_correct_finishes_game(client):
    _set_guest(client)
    board = _board_3x3()

    board.get_cell(1, 1).value = 3
    board.get_cell(1, 2).value = 1
    board.get_cell(2, 1).value = 1
    board.get_cell(2, 2).value = 2

    game = GameSession(
        sessionId="gs-test-correct",
        difficulty="easy",
        status="InProgress",
        board=board,
        result=None,
    )

    with client.session_transaction() as sess:
        sess["active_game"] = game.to_dict()

    response = client.post("/game/submit", follow_redirects=False)

    assert response.status_code == 302
    with client.session_transaction() as sess:
        stored = GameSession.from_dict(sess["active_game"])
        assert stored is not None
        assert stored.status == "Finished"
        assert stored.result is not None
        assert stored.result.isWin is True
        assert sess.get("wrong_cells", []) == []


def test_registered_user_can_save_game(client, app):
    user = _set_registered(client, app)
    board = _board_3x3()
    board.get_cell(1, 1).value = 3

    game = GameSession(
        sessionId="gs-save-1",
        difficulty="easy",
        status="InProgress",
        board=board,
        userId=user.userId,
        elapsedTime=0,
        result=None,
    )

    with client.session_transaction() as sess:
        sess["active_game"] = game.to_dict()

    response = client.post("/game/save", data={"elapsed_time": "91"}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/menu")

    with sqlite3.connect(app.config["DB_PATH"]) as conn:
        row = conn.execute(
            "SELECT session_id, user_id, elapsed_time, status FROM saved_games WHERE session_id = ?",
            ("gs-save-1",),
        ).fetchone()

    assert row is not None
    assert row[0] == "gs-save-1"
    assert row[1] == user.userId
    assert row[2] == 91
    assert row[3] == "InProgress"


def test_guest_user_cannot_save_game(client, app):
    _set_guest(client)
    board = _board_3x3()
    game = GameSession(
        sessionId="gs-guest-save",
        difficulty="easy",
        status="InProgress",
        board=board,
        result=None,
    )

    with client.session_transaction() as sess:
        sess["active_game"] = game.to_dict()

    response = client.post("/game/save", data={"elapsed_time": "20"}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/game")

    with sqlite3.connect(app.config["DB_PATH"]) as conn:
        count = conn.execute("SELECT COUNT(*) FROM saved_games").fetchone()[0]

    assert count == 0


def test_load_game_restores_saved_session(client, app):
    user = _set_registered(client, app)
    board = _board_3x3()
    board.get_cell(1, 1).value = 3
    board.get_cell(2, 2).value = 2

    saved = GameSession(
        sessionId="gs-load-1",
        difficulty="easy",
        status="InProgress",
        board=board,
        userId=user.userId,
        elapsedTime=44,
        result=None,
    )
    upsert_saved_game(saved, app.config["DB_PATH"])

    response = client.get("/game/load", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/game")

    with client.session_transaction() as sess:
        restored = GameSession.from_dict(sess["active_game"])
        assert restored is not None
        assert restored.sessionId == "gs-load-1"
        assert restored.elapsedTime == 44
        assert restored.status == "InProgress"
        assert restored.board.get_cell(1, 1).value == 3
        assert restored.board.get_cell(2, 2).value == 2


def test_pause_blocks_move_entry(client):
    _set_guest(client)
    board = _board_3x3()
    game = GameSession(
        sessionId="gs-paused",
        difficulty="easy",
        status="InProgress",
        board=board,
        result=None,
    )

    with client.session_transaction() as sess:
        sess["active_game"] = game.to_dict()
        sess["game_paused"] = True

    response = client.post(
        "/game/enter",
        data={"row": "1", "col": "1", "value": "3"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["ok"] is False
    assert "paused" in payload["message"].lower()
