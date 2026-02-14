import random


DIFFICULTY_SIZES = {
    "easy": (4, 4),
    "medium": (7, 7),
    "hard": (10, 10),
}

PLAY_PROBABILITY = {
    "easy": 0.72,
    "medium": 0.66,
    "hard": 0.60,
}

MIN_PLAY_RATIO = {
    "easy": 0.30,
    "medium": 0.35,
    "hard": 0.40,
}


def generate_new_game(difficulty):
    difficulty = (difficulty or "").lower()
    if difficulty not in DIFFICULTY_SIZES:
        raise ValueError("Unsupported difficulty.")

    rows, cols = DIFFICULTY_SIZES[difficulty]
    layout = None

    for _ in range(60):
        candidate = _random_layout(rows, cols, PLAY_PROBABILITY[difficulty])
        _enforce_max_run_length(candidate)
        _remove_short_runs(candidate)
        if _is_layout_usable(candidate, difficulty):
            layout = candidate
            break

    if layout is None:
        layout = _fallback_layout(rows, cols)

    solution = _build_solution_grid(layout)
    board = _build_board(layout, solution)

    return {
        "board": board,
        "solution": solution,
    }


def _random_layout(rows, cols, play_probability):
    layout = [[False for _ in range(cols)] for _ in range(rows)]

    for r in range(1, rows):
        for c in range(1, cols):
            if r == 1 or c == 1:
                adjusted_probability = min(play_probability + 0.10, 0.92)
            else:
                adjusted_probability = play_probability
            layout[r][c] = random.random() < adjusted_probability

    return layout


def _enforce_max_run_length(layout):
    rows = len(layout)
    cols = len(layout[0])

    for r in range(rows):
        run_len = 0
        for c in range(cols):
            if layout[r][c]:
                run_len += 1
                if run_len > 9:
                    layout[r][c] = False
                    run_len = 0
            else:
                run_len = 0

    for c in range(cols):
        run_len = 0
        for r in range(rows):
            if layout[r][c]:
                run_len += 1
                if run_len > 9:
                    layout[r][c] = False
                    run_len = 0
            else:
                run_len = 0


def _horizontal_run_length(layout, r, c):
    cols = len(layout[0])
    left = c
    right = c

    while left - 1 >= 0 and layout[r][left - 1]:
        left -= 1

    while right + 1 < cols and layout[r][right + 1]:
        right += 1

    return right - left + 1


def _vertical_run_length(layout, r, c):
    rows = len(layout)
    top = r
    bottom = r

    while top - 1 >= 0 and layout[top - 1][c]:
        top -= 1

    while bottom + 1 < rows and layout[bottom + 1][c]:
        bottom += 1

    return bottom - top + 1


def _remove_short_runs(layout):
    rows = len(layout)
    cols = len(layout[0])

    changed = True
    while changed:
        changed = False
        for r in range(1, rows):
            for c in range(1, cols):
                if not layout[r][c]:
                    continue

                horizontal = _horizontal_run_length(layout, r, c)
                vertical = _vertical_run_length(layout, r, c)

                if horizontal < 2 or vertical < 2:
                    layout[r][c] = False
                    changed = True


def _layout_runs(layout, direction):
    rows = len(layout)
    cols = len(layout[0])
    runs = []

    if direction == "across":
        for r in range(rows):
            c = 0
            while c < cols:
                if layout[r][c] and (c == 0 or not layout[r][c - 1]):
                    run = []
                    while c < cols and layout[r][c]:
                        run.append((r, c))
                        c += 1
                    if len(run) >= 2:
                        runs.append(run)
                else:
                    c += 1

    if direction == "down":
        for c in range(cols):
            r = 0
            while r < rows:
                if layout[r][c] and (r == 0 or not layout[r - 1][c]):
                    run = []
                    while r < rows and layout[r][c]:
                        run.append((r, c))
                        r += 1
                    if len(run) >= 2:
                        runs.append(run)
                else:
                    r += 1

    return runs


def _is_layout_usable(layout, difficulty):
    rows = len(layout)
    cols = len(layout[0])
    play_count = sum(1 for row in layout for value in row if value)
    min_play = max(4, int(rows * cols * MIN_PLAY_RATIO[difficulty]))

    if play_count < min_play:
        return False

    across_runs = _layout_runs(layout, "across")
    down_runs = _layout_runs(layout, "down")
    if not across_runs or not down_runs:
        return False

    for run in across_runs + down_runs:
        if len(run) > 9:
            return False

    return True


def _fallback_layout(rows, cols):
    layout = [[False for _ in range(cols)] for _ in range(rows)]

    for r in range(1, rows):
        for c in range(1, cols):
            layout[r][c] = True

    if rows > 6 and cols > 6:
        for r in range(2, rows):
            if (r - 1) % 4 == 0:
                for c in range(2, cols):
                    layout[r][c] = False

        for c in range(2, cols):
            if (c - 1) % 4 == 0:
                for r in range(2, rows):
                    layout[r][c] = False

    _enforce_max_run_length(layout)
    _remove_short_runs(layout)
    return layout


def _build_solution_grid(layout):
    rows = len(layout)
    cols = len(layout[0])
    offset = random.randint(0, 8)

    solution = [[0 for _ in range(cols)] for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if layout[r][c]:
                solution[r][c] = ((r + c + offset) % 9) + 1

    return solution


def _collect_run(layout, r, c, dr, dc):
    rows = len(layout)
    cols = len(layout[0])
    rr = r + dr
    cc = c + dc

    if not (0 <= rr < rows and 0 <= cc < cols):
        return []

    if not layout[rr][cc]:
        return []

    run = []
    while 0 <= rr < rows and 0 <= cc < cols and layout[rr][cc]:
        run.append((rr, cc))
        rr += dr
        cc += dc

    return run


def _build_board(layout, solution):
    rows = len(layout)
    cols = len(layout[0])
    board = [[{"type": "BLOCK"} for _ in range(cols)] for _ in range(rows)]

    for r in range(rows):
        for c in range(cols):
            if layout[r][c]:
                board[r][c] = {
                    "type": "PLAY",
                    "value": "",
                }

    for r in range(rows):
        for c in range(cols):
            if layout[r][c]:
                continue

            across_cells = _collect_run(layout, r, c, 0, 1)
            down_cells = _collect_run(layout, r, c, 1, 0)

            if across_cells or down_cells:
                across_sum = (
                    sum(solution[cell_r][cell_c] for cell_r, cell_c in across_cells)
                    if across_cells
                    else None
                )
                down_sum = (
                    sum(solution[cell_r][cell_c] for cell_r, cell_c in down_cells)
                    if down_cells
                    else None
                )
                board[r][c] = {
                    "type": "CLUE",
                    "across_sum": across_sum,
                    "down_sum": down_sum,
                }

    return board
