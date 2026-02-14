from kakuro.services.validation_service import validate_board


def _sample_board():
    return [
        [
            {"type": "BLOCK"},
            {"type": "CLUE", "down_sum": 4, "across_sum": None},
            {"type": "CLUE", "down_sum": 3, "across_sum": None},
            {"type": "BLOCK"},
        ],
        [
            {"type": "CLUE", "down_sum": None, "across_sum": 4},
            {"type": "PLAY", "value": ""},
            {"type": "PLAY", "value": ""},
            {"type": "BLOCK"},
        ],
        [
            {"type": "CLUE", "down_sum": None, "across_sum": 3},
            {"type": "PLAY", "value": ""},
            {"type": "PLAY", "value": ""},
            {"type": "BLOCK"},
        ],
        [
            {"type": "BLOCK"},
            {"type": "BLOCK"},
            {"type": "BLOCK"},
            {"type": "BLOCK"},
        ],
    ]


def test_duplicate_in_run_fails_validation():
    board = _sample_board()
    board[1][1]["value"] = 2
    board[1][2]["value"] = 2
    board[2][1]["value"] = 1
    board[2][2]["value"] = 2

    result = validate_board(board)

    assert result["is_valid"] is False
    assert any("Duplicate digit" in error for error in result["errors"])


def test_completed_run_with_wrong_sum_fails_validation():
    board = _sample_board()
    board[1][1]["value"] = 1
    board[1][2]["value"] = 1
    board[2][1]["value"] = 3
    board[2][2]["value"] = 2

    result = validate_board(board)

    assert result["is_valid"] is False
    assert any("Sum mismatch" in error for error in result["errors"])


def test_full_valid_board_is_win():
    board = _sample_board()
    board[1][1]["value"] = 3
    board[1][2]["value"] = 1
    board[2][1]["value"] = 1
    board[2][2]["value"] = 2

    result = validate_board(board)

    assert result["is_valid"] is True
    assert result["is_win"] is True
    assert result["errors"] == []
