def _parse_value(value):
    if isinstance(value, int):
        return value if 1 <= value <= 9 else None

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if stripped.isdigit():
            number = int(stripped)
            return number if 1 <= number <= 9 else None

    return None


def apply_form_values(board, form_data):
    for r, row in enumerate(board):
        for c, cell in enumerate(row):
            if cell.get("type") != "PLAY":
                continue

            key = f"cell_{r}_{c}"
            raw = (form_data.get(key) or "").strip()

            if raw == "":
                cell["value"] = ""
                continue

            if raw.isdigit():
                number = int(raw)
                cell["value"] = number if 1 <= number <= 9 else raw
            else:
                cell["value"] = raw


def extract_runs(board):
    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0
    runs = []

    for r in range(rows):
        for c in range(cols):
            cell = board[r][c]
            if cell.get("type") != "CLUE":
                continue

            across_sum = cell.get("across_sum")
            if across_sum is not None:
                run_cells = []
                cc = c + 1
                while cc < cols and board[r][cc].get("type") == "PLAY":
                    run_cells.append((r, cc))
                    cc += 1
                if run_cells:
                    runs.append(
                        {
                            "direction": "across",
                            "sum": across_sum,
                            "cells": run_cells,
                            "start": (r, c),
                        }
                    )

            down_sum = cell.get("down_sum")
            if down_sum is not None:
                run_cells = []
                rr = r + 1
                while rr < rows and board[rr][c].get("type") == "PLAY":
                    run_cells.append((rr, c))
                    rr += 1
                if run_cells:
                    runs.append(
                        {
                            "direction": "down",
                            "sum": down_sum,
                            "cells": run_cells,
                            "start": (r, c),
                        }
                    )

    return runs


def validate_board(board):
    errors = []
    error_cells = set()
    all_filled = True

    for r, row in enumerate(board):
        for c, cell in enumerate(row):
            if cell.get("type") != "PLAY":
                continue

            raw = cell.get("value", "")
            if raw in (None, ""):
                all_filled = False
                continue

            parsed = _parse_value(raw)
            if parsed is None:
                errors.append(f"Invalid value at row {r + 1}, col {c + 1}. Use digits 1-9.")
                error_cells.add((r, c))

    for run in extract_runs(board):
        value_positions = {}
        run_sum = 0
        complete = True

        for r, c in run["cells"]:
            parsed = _parse_value(board[r][c].get("value", ""))
            if parsed is None:
                complete = False
                continue

            value_positions.setdefault(parsed, []).append((r, c))
            run_sum += parsed

        duplicate_cells = []
        for _, cells in value_positions.items():
            if len(cells) > 1:
                duplicate_cells.extend(cells)

        if duplicate_cells:
            for cell in duplicate_cells:
                error_cells.add(cell)

            cell_labels = ", ".join(f"({r + 1}, {c + 1})" for r, c in sorted(duplicate_cells))
            errors.append(
                "Duplicate digit in "
                f"{run['direction']} run starting at ({run['start'][0] + 1}, {run['start'][1] + 1}) "
                f"at cells {cell_labels}."
            )

        if complete and run_sum != run["sum"]:
            for cell in run["cells"]:
                error_cells.add(cell)
            errors.append(
                "Sum mismatch in "
                f"{run['direction']} run starting at ({run['start'][0] + 1}, {run['start'][1] + 1}) "
                f"(expected {run['sum']}, got {run_sum})."
            )

    is_valid = len(errors) == 0
    is_win = is_valid and all_filled

    return {
        "is_valid": is_valid,
        "is_win": is_win,
        "errors": errors,
        "error_cells": sorted(error_cells),
    }
