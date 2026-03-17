from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_value(cls, value: str | "DifficultyLevel") -> "DifficultyLevel":
        if isinstance(value, DifficultyLevel):
            return value

        normalized = str(value or "").strip().lower()
        if normalized == cls.MEDIUM.value:
            return cls.MEDIUM
        if normalized == cls.HARD.value:
            return cls.HARD
        return cls.EASY


@dataclass
class User:
    userId: Optional[int]
    username: str
    email: str
    passwordHash: str

    @staticmethod
    def signUp(username: str, email: str, password: str) -> dict:
        return {"username": username, "email": email, "password": password}

    @staticmethod
    def login(email: str, password: str) -> dict:
        return {"email": email, "password": password}

    def logout(self) -> bool:
        return True


@dataclass
class RegisteredUser(User):
    def saveGame(self) -> bool:
        return True

    def loadGame(self) -> bool:
        return True


@dataclass
class GuestUser(User):
    def playAsGuest(self) -> bool:
        return True


@dataclass
class Cell:
    row: int
    col: int
    value: Optional[int] = None
    isPlayable: bool = True
    clueDown: Optional[int] = None
    clueRight: Optional[int] = None

    @property
    def horizontalSum(self) -> Optional[int]:
        return self.clueRight

    @horizontalSum.setter
    def horizontalSum(self, value: Optional[int]) -> None:
        self.clueRight = value

    @property
    def verticalSum(self) -> Optional[int]:
        return self.clueDown

    @verticalSum.setter
    def verticalSum(self, value: Optional[int]) -> None:
        self.clueDown = value

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
        clue_down = data.get("clueDown", data.get("downSum", data.get("verticalSum")))
        clue_right = data.get("clueRight", data.get("rightSum", data.get("horizontalSum")))
        is_playable = bool(data.get("isPlayable", data.get("cellType") == "play"))

        if is_playable:
            return PlayCell(
                row=data["row"],
                col=data["col"],
                value=data.get("value"),
                clueDown=clue_down,
                clueRight=clue_right,
                correctValue=data.get("correctValue"),
                editable=bool(data.get("editable", True)),
                hinted=bool(data.get("hinted", False)),
            )

        return ClueCell(
            row=data["row"],
            col=data["col"],
            value=None,
            clueDown=clue_down,
            clueRight=clue_right,
        )


@dataclass
class PlayCell(Cell):
    correctValue: Optional[int] = None
    editable: bool = True
    hinted: bool = False

    def __post_init__(self) -> None:
        self.isPlayable = True
        self.clueDown = None
        self.clueRight = None

    def setValue(self, value: Optional[int]) -> bool:
        if not self.editable:
            return False
        self.value = value
        return True

    def clearValue(self) -> bool:
        return self.setValue(None)

    def to_dict(self) -> dict:
        payload = super().to_dict()
        payload.update(
            {
                "cellType": "play",
                "correctValue": self.correctValue,
                "editable": self.editable,
                "hinted": self.hinted,
            }
        )
        return payload


@dataclass
class ClueCell(Cell):
    def __post_init__(self) -> None:
        self.isPlayable = False
        self.value = None

    def to_dict(self) -> dict:
        payload = super().to_dict()
        payload.update({"cellType": "clue"})
        return payload


@dataclass
class Board:
    boardId: str
    difficulty: str
    size: tuple[int, int]
    cells: list[Cell] = field(default_factory=list)

    @property
    def rows(self) -> int:
        return self.size[0]

    @property
    def columns(self) -> int:
        return self.size[1]

    def get_cell(self, row: int, col: int) -> Optional[Cell]:
        for cell in self.cells:
            if cell.row == row and cell.col == col:
                return cell
        return None

    def getCell(self, row: int, col: int) -> Optional[Cell]:
        return self.get_cell(row, col)

    def matrix(self) -> list[list[Cell]]:
        rows, cols = self.size
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        for cell in self.cells:
            grid[cell.row][cell.col] = cell
        return grid

    def validateEntry(self, row: int, col: int, value: Optional[int]) -> tuple[bool, str]:
        cell = self.get_cell(row, col)
        if cell is None:
            return False, "Invalid cell coordinates."
        if not cell.isPlayable:
            return False, "Selected cell is not playable."
        if value is not None and (value < 1 or value > 9):
            return False, "Value must be empty or a digit 1-9."

        matrix = self.matrix()
        old_value = cell.value
        cell.value = value

        for run in (self._across_run(matrix, row, col), self._down_run(matrix, row, col)):
            seen: set[int] = set()
            for run_cell in run:
                if run_cell.value is None:
                    continue
                if run_cell.value in seen:
                    cell.value = old_value
                    return False, "Duplicate value in run is not allowed."
                seen.add(run_cell.value)

        return True, "Move accepted."

    def _across_run(self, matrix: list[list[Cell]], row: int, col: int) -> list[Cell]:
        cols = len(matrix[0])
        left = col
        while left - 1 >= 0 and matrix[row][left - 1].isPlayable:
            left -= 1
        right = col
        while right + 1 < cols and matrix[row][right + 1].isPlayable:
            right += 1
        return [matrix[row][c] for c in range(left, right + 1)]

    def _down_run(self, matrix: list[list[Cell]], row: int, col: int) -> list[Cell]:
        rows = len(matrix)
        top = row
        while top - 1 >= 0 and matrix[top - 1][col].isPlayable:
            top -= 1
        bottom = row
        while bottom + 1 < rows and matrix[bottom + 1][col].isPlayable:
            bottom += 1
        return [matrix[r][col] for r in range(top, bottom + 1)]

    def to_dict(self) -> dict:
        return {
            "boardId": self.boardId,
            "difficulty": str(self.difficulty),
            "size": [self.size[0], self.size[1]],
            "cells": [cell.to_dict() for cell in self.cells],
        }

    @staticmethod
    def from_dict(data: dict) -> "Board":
        return Board(
            boardId=data["boardId"],
            difficulty=str(data["difficulty"]),
            size=(data["size"][0], data["size"][1]),
            cells=[Cell.from_dict(cell) for cell in data["cells"]],
        )


@dataclass
class Result:
    resultId: str
    isWin: bool
    completionTime: int = 0

    @property
    def isWinner(self) -> bool:
        return self.isWin

    @isWinner.setter
    def isWinner(self, value: bool) -> None:
        self.isWin = bool(value)

    def recordResult(self, completion_time: int, is_winner: bool) -> None:
        self.completionTime = max(0, int(completion_time))
        self.isWin = bool(is_winner)

    def to_dict(self) -> dict:
        return {
            "resultId": self.resultId,
            "isWin": self.isWin,
            "completionTime": self.completionTime,
        }

    @staticmethod
    def from_dict(data: Optional[dict]) -> Optional["Result"]:
        if not data:
            return None
        return Result(
            resultId=data["resultId"],
            isWin=data["isWin"],
            completionTime=int(data.get("completionTime", 0) or 0),
        )


@dataclass
class GameSession:
    sessionId: str
    difficulty: str
    status: str
    board: Board
    userId: Optional[int] = None
    elapsedTime: int = 0
    isPaused: bool = False
    isCompleted: bool = False
    isSubmitted: bool = False
    result: Optional[Result] = None

    def __post_init__(self) -> None:
        self.difficulty = str(DifficultyLevel.from_value(self.difficulty))
        self._sync_state_flags()

    def _sync_state_flags(self) -> None:
        if self.status == "Finished":
            self.isCompleted = True
            self.isSubmitted = True
            self.isPaused = False
        elif self.isCompleted:
            self.status = "Finished"

    def startNewGame(self, difficulty: str) -> None:
        self.difficulty = str(DifficultyLevel.from_value(difficulty))
        self.status = "InProgress"
        self.elapsedTime = 0
        self.isPaused = False
        self.isCompleted = False
        self.isSubmitted = False
        self.result = None

    def enterNumber(self, row: int, col: int, value: Optional[int]) -> tuple[bool, str]:
        # Flow 4A enterNumber: domain operation contract.
        if self.isPaused:
            return False, "Game is paused. Resume to continue."
        return self.board.validateEntry(row, col, value)

    def removeNumber(self, row: int, col: int) -> tuple[bool, str]:
        # Flow 4C removeNumber: domain operation contract (not exposed as a dedicated route).
        if self.isPaused:
            return False, "Game is paused. Resume to continue."
        return self.board.validateEntry(row, col, None)

    def pauseGame(self) -> None:
        # Flow 4E pauseGame: domain state transition.
        if not self.isCompleted:
            self.isPaused = True

    def resumeGame(self) -> None:
        # Flow 4E resumeGame: domain state transition.
        self.isPaused = False

    def submitBoard(self) -> None:
        # Flow 4D submitBoard: domain state transition.
        self.isSubmitted = True

    def checkHint(self) -> Optional[tuple[int, int]]:
        # Flow 4B checkHint: domain operation (currently not wired through route/service/UI).
        for cell in self.board.cells:
            if cell.isPlayable and cell.value is None:
                if isinstance(cell, PlayCell):
                    cell.hinted = True
                return (cell.row, cell.col)
        return None

    def to_dict(self) -> dict:
        return {
            "sessionId": self.sessionId,
            "difficulty": self.difficulty,
            "status": self.status,
            "board": self.board.to_dict(),
            "userId": self.userId,
            "elapsedTime": self.elapsedTime,
            "isPaused": self.isPaused,
            "isCompleted": self.isCompleted,
            "isSubmitted": self.isSubmitted,
            "result": self.result.to_dict() if self.result else None,
        }

    @staticmethod
    def from_dict(data: Optional[dict]) -> Optional["GameSession"]:
        if not data:
            return None
        return GameSession(
            sessionId=data["sessionId"],
            difficulty=data["difficulty"],
            status=data.get("status", "InProgress"),
            board=Board.from_dict(data["board"]),
            userId=data.get("userId"),
            elapsedTime=int(data.get("elapsedTime", 0) or 0),
            isPaused=bool(data.get("isPaused", False)),
            isCompleted=bool(data.get("isCompleted", data.get("status") == "Finished")),
            isSubmitted=bool(data.get("isSubmitted", data.get("status") == "Finished")),
            result=Result.from_dict(data.get("result")),
        )


@dataclass
class SavedGame:
    saveId: Optional[int]
    sessionId: str
    userId: int
    boardState: dict
    difficulty: str
    elapsedTime: int
    status: str
    savedAt: str

    def save(self) -> dict:
        return {
            "saveId": self.saveId,
            "sessionId": self.sessionId,
            "userId": self.userId,
            "boardState": self.boardState,
            "difficulty": self.difficulty,
            "elapsedTime": self.elapsedTime,
            "status": self.status,
            "savedAt": self.savedAt,
        }

    def restore(self) -> GameSession:
        return GameSession(
            sessionId=self.sessionId,
            userId=self.userId,
            board=Board.from_dict(self.boardState),
            difficulty=self.difficulty,
            elapsedTime=self.elapsedTime,
            status=self.status,
            isPaused=False,
            result=None,
        )
