from __future__ import annotations

import random
import uuid
from dataclasses import dataclass

from ..models.domain import Board, Cell


DIFFICULTY_SIZES = {
    "easy": (5, 5),
    "medium": (8, 9),
    "hard": (13, 13),
}


@dataclass(frozen=True)
class _DifficultyConfig:
    rows: int
    cols: int
    play_probability: float
    min_ratio: float
    seeds: tuple[int, int]


DIFFICULTY_CONFIGS = {
    "easy": _DifficultyConfig(5, 5, 0.78, 0.32, (101, 133)),
    "medium": _DifficultyConfig(8, 9, 0.68, 0.30, (211, 257)),
    "hard": _DifficultyConfig(13, 13, 0.60, 0.28, (307, 353)),
}

DIGIT_POOLS = {
    "easy": (1, 2, 3, 4, 5, 6),
    "medium": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "hard": (1, 2, 3, 4, 5, 6, 7, 8, 9),
}


def generate_board(difficulty: str) -> Board:
    difficulty = difficulty.lower()
    if difficulty not in DIFFICULTY_CONFIGS:
        raise ValueError("Unsupported difficulty.")

    config = DIFFICULTY_CONFIGS[difficulty]
    template = _build_random_template(difficulty, config)

    cells = [
        Cell(
            row=cell["row"],
            col=cell["col"],
            value=None,
            isPlayable=cell["isPlayable"],
            clueDown=cell.get("clueDown", cell.get("downSum")),
            clueRight=cell.get("clueRight", cell.get("rightSum")),
        )
        for cell in template["cells"]
    ]

    return Board(
        boardId=f"board-{uuid.uuid4().hex[:12]}",
        difficulty=difficulty,
        size=(template["rows"], template["cols"]),
        cells=cells,
    )


def _build_random_template(difficulty: str, config: _DifficultyConfig) -> dict:
    for _ in range(20):
        seed = random.randint(1, 2_147_483_647)
        template = _build_template_from_seed(difficulty, config, seed)
        if template is not None:
            return template

    for seed in config.seeds:
        template = _build_template_from_seed(difficulty, config, seed)
        if template is not None:
            return template

    raise RuntimeError(f"Unable to generate a valid board for difficulty '{difficulty}'.")


def _build_template_from_seed(difficulty: str, config: _DifficultyConfig, seed: int) -> dict | None:
    layout = _build_layout(config, seed)
    try:
        solution = _build_solution(layout, seed, difficulty)
    except RuntimeError:
        return None
    return _build_template(layout, solution, seed, difficulty)


def _build_layout(config: _DifficultyConfig, seed: int) -> list[list[bool]]:
    rows, cols = config.rows, config.cols

    for attempt in range(120):
        rng = random.Random(seed + (attempt * 97))
        layout = [[False for _ in range(cols)] for _ in range(rows)]

        for r in range(1, rows):
            for c in range(1, cols):
                edge_boost = 0.12 if r == 1 or c == 1 else 0.0
                layout[r][c] = rng.random() < min(config.play_probability + edge_boost, 0.92)

        _enforce_max_run_length(layout)
        _remove_short_runs(layout)

        if _is_usable(layout, config.min_ratio):
            return layout

    return _fallback_layout(rows, cols)


def _enforce_max_run_length(layout: list[list[bool]]) -> None:
    rows, cols = len(layout), len(layout[0])

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


def _horizontal_span(layout: list[list[bool]], r: int, c: int) -> int:
    cols = len(layout[0])
    left = c
    right = c

    while left - 1 >= 0 and layout[r][left - 1]:
        left -= 1

    while right + 1 < cols and layout[r][right + 1]:
        right += 1

    return right - left + 1


def _vertical_span(layout: list[list[bool]], r: int, c: int) -> int:
    rows = len(layout)
    top = r
    bottom = r

    while top - 1 >= 0 and layout[top - 1][c]:
        top -= 1

    while bottom + 1 < rows and layout[bottom + 1][c]:
        bottom += 1

    return bottom - top + 1


def _remove_short_runs(layout: list[list[bool]]) -> None:
    rows, cols = len(layout), len(layout[0])

    changed = True
    while changed:
        changed = False
        for r in range(1, rows):
            for c in range(1, cols):
                if not layout[r][c]:
                    continue

                if _horizontal_span(layout, r, c) < 2 or _vertical_span(layout, r, c) < 2:
                    layout[r][c] = False
                    changed = True


def _collect_runs(layout: list[list[bool]], direction: str) -> list[list[tuple[int, int]]]:
    rows, cols = len(layout), len(layout[0])
    runs: list[list[tuple[int, int]]] = []

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


def _is_usable(layout: list[list[bool]], min_ratio: float) -> bool:
    rows, cols = len(layout), len(layout[0])
    play_count = sum(1 for row in layout for is_play in row if is_play)
    if play_count < int(rows * cols * min_ratio):
        return False

    across = _collect_runs(layout, "across")
    down = _collect_runs(layout, "down")
    return bool(across and down)


def _fallback_layout(rows: int, cols: int) -> list[list[bool]]:
    layout = [[False for _ in range(cols)] for _ in range(rows)]

    for r in range(1, rows):
        for c in range(1, cols):
            layout[r][c] = True

    for r in range(2, rows):
        if (r - 1) % 3 == 0:
            for c in range(2, cols):
                layout[r][c] = False

    for c in range(2, cols):
        if (c - 1) % 3 == 0:
            for r in range(2, rows):
                layout[r][c] = False

    _enforce_max_run_length(layout)
    _remove_short_runs(layout)
    return layout


def _build_solution(layout: list[list[bool]], seed: int, difficulty: str) -> list[list[int]]:
    rows, cols = len(layout), len(layout[0])

    across_id: dict[tuple[int, int], int] = {}
    down_id: dict[tuple[int, int], int] = {}

    across_runs = _collect_runs(layout, "across")
    down_runs = _collect_runs(layout, "down")

    for idx, run in enumerate(across_runs):
        for rc in run:
            across_id[rc] = idx

    for idx, run in enumerate(down_runs):
        for rc in run:
            down_id[rc] = idx

    across_used = [set() for _ in across_runs]
    down_used = [set() for _ in down_runs]

    positions = [(r, c) for r in range(rows) for c in range(cols) if layout[r][c]]
    rng = random.Random(seed * 13 + 7)
    allowed_digits = DIGIT_POOLS[difficulty]

    assigned: dict[tuple[int, int], int] = {}

    def candidates_for(pos: tuple[int, int]) -> list[int]:
        r, c = pos
        a_id = across_id[(r, c)]
        d_id = down_id[(r, c)]
        options = [d for d in allowed_digits if d not in across_used[a_id] and d not in down_used[d_id]]
        if difficulty == "easy":
            options.sort(key=lambda d: d + (rng.random() * 0.8))
        else:
            rng.shuffle(options)
        return options

    def pick_next() -> tuple[int, int] | None:
        open_cells = [pos for pos in positions if pos not in assigned]
        if not open_cells:
            return None

        best_pos = None
        best_options = None
        for pos in open_cells:
            options = candidates_for(pos)
            if best_options is None or len(options) < len(best_options):
                best_pos = pos
                best_options = options
                if len(best_options) <= 1:
                    break
        return best_pos

    def solve() -> bool:
        pos = pick_next()
        if pos is None:
            return True

        options = candidates_for(pos)
        if not options:
            return False

        r, c = pos
        a_id = across_id[(r, c)]
        d_id = down_id[(r, c)]

        for value in options:
            assigned[pos] = value
            across_used[a_id].add(value)
            down_used[d_id].add(value)

            if solve():
                return True

            across_used[a_id].remove(value)
            down_used[d_id].remove(value)
            del assigned[pos]

        return False

    if not solve():
        raise RuntimeError("Failed to build template solution")

    solution = [[0 for _ in range(cols)] for _ in range(rows)]
    for (r, c), value in assigned.items():
        solution[r][c] = value

    return solution


def _build_template(
    layout: list[list[bool]],
    solution: list[list[int]],
    seed: int,
    difficulty: str,
) -> dict:
    rows, cols = len(layout), len(layout[0])

    def right_run_sum(r: int, c: int) -> int | None:
        cc = c + 1
        run = []
        while cc < cols and layout[r][cc]:
            run.append(solution[r][cc])
            cc += 1
        if len(run) >= 2:
            return sum(run)
        return None

    def down_run_sum(r: int, c: int) -> int | None:
        rr = r + 1
        run = []
        while rr < rows and layout[rr][c]:
            run.append(solution[rr][c])
            rr += 1
        if len(run) >= 2:
            return sum(run)
        return None

    cells = []
    for r in range(rows):
        for c in range(cols):
            if layout[r][c]:
                cells.append(
                    {
                        "row": r,
                        "col": c,
                        "isPlayable": True,
                        "clueDown": None,
                        "clueRight": None,
                    }
                )
            else:
                cells.append(
                    {
                        "row": r,
                        "col": c,
                        "isPlayable": False,
                        "clueDown": down_run_sum(r, c),
                        "clueRight": right_run_sum(r, c),
                    }
                )

    return {
        "templateId": f"{difficulty}-t{seed}",
        "rows": rows,
        "cols": cols,
        "cells": cells,
    }
