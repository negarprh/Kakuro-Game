from kakuro.models.domain import Board, Cell
from kakuro.services.validation_service import validate_entire_board, validate_move


def _board_3x3_for_validation():
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
    return Board(boardId="b1", difficulty="easy", size=(3, 3), cells=cells)


def test_validate_move_rejects_duplicates():
    board = _board_3x3_for_validation()

    assert validate_move(board, 1, 1, "2")["ok"] is True
    result = validate_move(board, 1, 2, "2")

    assert result["ok"] is False
    assert "Duplicate" in result["message"]


def test_validate_move_allows_wrong_sum_until_submit():
    board = _board_3x3_for_validation()

    # Across clue is 4, but 1 + 1 is wrong. Move-level should still allow this.
    first = validate_move(board, 1, 1, "1")
    second = validate_move(board, 1, 2, "1")

    assert first["ok"] is True
    assert second["ok"] is False  # duplicate still blocked

    # Use distinct values that still produce wrong sum (1 + 2 = 3, clue 4)
    second = validate_move(board, 1, 2, "2")
    assert second["ok"] is True


def test_submit_marks_wrong_cells_for_sum_and_duplicate():
    board = _board_3x3_for_validation()

    board.get_cell(1, 1).value = 2
    board.get_cell(1, 2).value = 2
    board.get_cell(2, 1).value = 1
    board.get_cell(2, 2).value = 1

    result = validate_entire_board(board)

    assert result["isSolved"] is False
    assert len(result["wrongCells"]) >= 2


def test_submit_win_case():
    board = _board_3x3_for_validation()

    validate_move(board, 1, 1, "3")
    validate_move(board, 1, 2, "1")
    validate_move(board, 2, 1, "1")
    validate_move(board, 2, 2, "2")

    result = validate_entire_board(board)

    assert result["isSolved"] is True
    assert result["wrongCells"] == []
    assert result["message"] == "Win"
