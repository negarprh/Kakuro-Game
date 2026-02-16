from kakuro.models.domain import Board, Cell, GameSession


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
