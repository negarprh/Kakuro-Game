"""
Validation rules for move-level and board-level checks.
Supports flow: Play Game.
"""

from __future__ import annotations

from collections import defaultdict

from ..models.domain import Board, Cell


def _parse_value(raw_value: str | int | None) -> int | None:
    if raw_value is None:
        return None

    if isinstance(raw_value, int):
        return raw_value if 1 <= raw_value <= 9 else None

    raw_value = str(raw_value).strip()
    if raw_value == "":
        return None

    if not raw_value.isdigit():
        return None

    value = int(raw_value)
    return value if 1 <= value <= 9 else None


def _board_matrix(board: Board) -> list[list[Cell]]:
    return board.matrix()


def _get_across_run(matrix: list[list[Cell]], row: int, col: int) -> tuple[list[Cell], int | None]:
    cols = len(matrix[0])

    left = col
    while left - 1 >= 0 and matrix[row][left - 1].isPlayable:
        left -= 1

    right = col
    while right + 1 < cols and matrix[row][right + 1].isPlayable:
        right += 1

    run = [matrix[row][cc] for cc in range(left, right + 1)]
    clue_col = left - 1
    clue = matrix[row][clue_col].clueRight if clue_col >= 0 else None

    return run, clue


def _get_down_run(matrix: list[list[Cell]], row: int, col: int) -> tuple[list[Cell], int | None]:
    rows = len(matrix)

    top = row
    while top - 1 >= 0 and matrix[top - 1][col].isPlayable:
        top -= 1

    bottom = row
    while bottom + 1 < rows and matrix[bottom + 1][col].isPlayable:
        bottom += 1

    run = [matrix[rr][col] for rr in range(top, bottom + 1)]
    clue_row = top - 1
    clue = matrix[clue_row][col].clueDown if clue_row >= 0 else None

    return run, clue


def validate_move(board: Board, row: int, col: int, raw_value: str | None) -> dict:
    # Diagram mapping: validate move during enterNumber(row, col, value).
    # Preconditions: active board exists, target cell is editable, value is empty or 1-9.
    matrix = _board_matrix(board)
    rows, cols = board.size

    if row < 0 or col < 0 or row >= rows or col >= cols:
        return {"ok": False, "message": "Invalid cell coordinates."}

    cell = matrix[row][col]
    if not cell.isPlayable:
        return {"ok": False, "message": "Selected cell is not playable."}

    new_value = _parse_value(raw_value)
    if raw_value is not None and str(raw_value).strip() != "" and new_value is None:
        return {"ok": False, "message": "Value must be empty or a digit 1-9."}

    old_value = cell.value
    cell.value = new_value

    across_run, across_clue = _get_across_run(matrix, row, col)
    down_run, down_clue = _get_down_run(matrix, row, col)

    for run in (across_run, down_run):
        seen = set()
        for run_cell in run:
            if run_cell.value is None:
                continue
            if run_cell.value in seen:
                cell.value = old_value
                # ALT path: duplicate value inside a run is rejected immediately.
                return {"ok": False, "message": "Duplicate value in run is not allowed."}
            seen.add(run_cell.value)

    # Postcondition: cell value is updated when validation passes.
    return {"ok": True, "message": "Move accepted.", "value": new_value}


def validate_entire_board(board: Board) -> dict:
    # Diagram mapping: submitSolution() -> Validate Entire Board + Highlight Wrong Cells.
    matrix = _board_matrix(board)
    rows, cols = board.size

    wrong_cells: set[tuple[int, int]] = set()

    for r in range(rows):
        for c in range(cols):
            clue_cell = matrix[r][c]
            if clue_cell.isPlayable:
                continue

            if clue_cell.clueRight is not None:
                run = []
                cc = c + 1
                while cc < cols and matrix[r][cc].isPlayable:
                    run.append(matrix[r][cc])
                    cc += 1
                _mark_run_errors(run, clue_cell.clueRight, wrong_cells)

            if clue_cell.clueDown is not None:
                run = []
                rr = r + 1
                while rr < rows and matrix[rr][c].isPlayable:
                    run.append(matrix[rr][c])
                    rr += 1
                _mark_run_errors(run, clue_cell.clueDown, wrong_cells)

    playable_cells = [cell for row in matrix for cell in row if cell.isPlayable]
    all_filled = all(cell.value is not None for cell in playable_cells)
    is_solved = all_filled and not wrong_cells

    ordered_wrong = sorted(wrong_cells)
    coords_message = ", ".join(f"({r + 1},{c + 1})" for r, c in ordered_wrong)

    if is_solved:
        message = "Win"
    else:
        # ALT path on submit: board is incomplete/incorrect, so wrong cells are returned.
        message = "Not solved / incorrect"
        if coords_message:
            message += f". Wrong cells: {coords_message}"

    return {
        "isSolved": is_solved,
        "wrongCells": ordered_wrong,
        "message": message,
    }


def _mark_run_errors(run: list[Cell], clue: int, wrong_cells: set[tuple[int, int]]) -> None:
    value_positions: dict[int, list[tuple[int, int]]] = defaultdict(list)

    for cell in run:
        if cell.value is None:
            continue
        value_positions[cell.value].append((cell.row, cell.col))

    for positions in value_positions.values():
        if len(positions) > 1:
            wrong_cells.update(positions)

    if run and all(cell.value is not None for cell in run):
        if sum(cell.value for cell in run) != clue:
            for cell in run:
                wrong_cells.add((cell.row, cell.col))
