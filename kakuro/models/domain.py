from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    userId: Optional[int]
    username: str
    email: str
    passwordHash: str


@dataclass
class Cell:
    row: int
    col: int
    value: Optional[int]
    isPlayable: bool
    clueDown: Optional[int] = None
    clueRight: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "row": self.row,
            "col": self.col,
            "value": self.value,
            "isPlayable": self.isPlayable,
            "clueDown": self.clueDown,
            "clueRight": self.clueRight,
        }

    @staticmethod
    def from_dict(data: dict) -> "Cell":
        return Cell(
            row=data["row"],
            col=data["col"],
            value=data.get("value"),
            isPlayable=data["isPlayable"],
            clueDown=data.get("clueDown", data.get("downSum", data.get("verticalSum"))),
            clueRight=data.get("clueRight", data.get("rightSum", data.get("horizontalSum"))),
        )


@dataclass
class Board:
    boardId: str
    difficulty: str
    size: tuple[int, int]
    cells: list[Cell] = field(default_factory=list)

    def get_cell(self, row: int, col: int) -> Optional[Cell]:
        for cell in self.cells:
            if cell.row == row and cell.col == col:
                return cell
        return None

    def matrix(self) -> list[list[Cell]]:
        rows, cols = self.size
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        for cell in self.cells:
            grid[cell.row][cell.col] = cell
        return grid

    def to_dict(self) -> dict:
        return {
            "boardId": self.boardId,
            "difficulty": self.difficulty,
            "size": [self.size[0], self.size[1]],
            "cells": [cell.to_dict() for cell in self.cells],
        }

    @staticmethod
    def from_dict(data: dict) -> "Board":
        return Board(
            boardId=data["boardId"],
            difficulty=data["difficulty"],
            size=(data["size"][0], data["size"][1]),
            cells=[Cell.from_dict(cell) for cell in data["cells"]],
        )


@dataclass
class Result:
    resultId: str
    isWin: bool

    def to_dict(self) -> dict:
        return {
            "resultId": self.resultId,
            "isWin": self.isWin,
        }

    @staticmethod
    def from_dict(data: Optional[dict]) -> Optional["Result"]:
        if not data:
            return None
        return Result(
            resultId=data["resultId"],
            isWin=data["isWin"],
        )


@dataclass
class GameSession:
    sessionId: str
    difficulty: str
    status: str
    board: Board
    result: Optional[Result] = None

    def to_dict(self) -> dict:
        return {
            "sessionId": self.sessionId,
            "difficulty": self.difficulty,
            "status": self.status,
            "board": self.board.to_dict(),
            "result": self.result.to_dict() if self.result else None,
        }

    @staticmethod
    def from_dict(data: Optional[dict]) -> Optional["GameSession"]:
        if not data:
            return None
        return GameSession(
            sessionId=data["sessionId"],
            difficulty=data["difficulty"],
            status=data["status"],
            board=Board.from_dict(data["board"]),
            result=Result.from_dict(data.get("result")),
        )
