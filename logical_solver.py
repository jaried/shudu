"""纯逻辑数独求解器兼容入口。
核心候选与技巧搜索统一委托给 shudu 包内的 Numba 实现。
本模块保留既有公开 helpers、CLI 和默认技巧顺序，避免入口调用方迁移成本。
完整 solve 卡住时仍使用共享回溯 fallback；单步逻辑本身不试数。
"""

from __future__ import annotations

from typing import List, Set, Tuple

from shudu.sudoku_logic import NumbaLogicSolver
from shudu.sudoku_rules import BOXES, COLS, ROWS, candidate_grid, unit_name as shared_unit_name

Board = List[List[int]]
Cands = List[List[Set[int]]]
Cell = Tuple[int, int]


def parse(text: str) -> Board:
    board = [[0] * 9 for _ in range(9)]
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    for row in range(min(9, len(lines))):
        for col in range(min(9, len(lines[row]))):
            char = lines[row][col]
            board[row][col] = int(char) if char.isdigit() and char != "." else 0
    return board


def format_cell(row: int, col: int) -> str:
    result = f"({row + 1},{col + 1})"
    return result


def format_cells(cells: List[Cell]) -> str:
    result = ", ".join(format_cell(*cell) for cell in cells)
    return result


def print_board(board: Board) -> None:
    horizontal = "+-------+-------+-------+"
    print(horizontal)
    for row in range(9):
        line = "| "
        for col in range(9):
            line += f"{board[row][col] if board[row][col] else '.'} "
            if col in (2, 5):
                line += "| "
        print(line + "|")
        if row in (2, 5):
            print(horizontal)
    print(horizontal)
    return


def board_solved(board: Board) -> bool:
    result = all(board[row][col] != 0 for row in range(9) for col in range(9))
    return result


def init_candidates(board: Board) -> Cands:
    result = candidate_grid(board)
    return result


def _eliminate(board: Board, candidates, row: int, col: int, digit: int) -> None:
    """兼容旧 helper：从一维候选数组的同行、列、宫删除 digit。"""
    for other_col in range(9):
        if board[row][other_col] == 0:
            candidates[row * 9 + other_col].discard(digit)
    for other_row in range(9):
        if board[other_row][col] == 0:
            candidates[other_row * 9 + col].discard(digit)
    base_row = row // 3 * 3
    base_col = col // 3 * 3
    for other_row in range(base_row, base_row + 3):
        for other_col in range(base_col, base_col + 3):
            if board[other_row][other_col] == 0:
                candidates[other_row * 9 + other_col].discard(digit)
    return


def row_cells(row: int) -> List[Cell]:
    result = list(ROWS[row])
    return result


def col_cells(col: int) -> List[Cell]:
    result = list(COLS[col])
    return result


def box_cells(row: int, col: int) -> List[Cell]:
    index = row // 3 * 3 + col // 3
    result = list(BOXES[index])
    return result


def all_units() -> List[List[Cell]]:
    result = []
    for index in range(9):
        result.append(row_cells(index))
        result.append(col_cells(index))
    result.extend(list(unit) for unit in BOXES)
    return result


UNITS = all_units()


def unit_name(cells: List[Cell]) -> str:
    result = shared_unit_name(cells)
    return result


class LogicSolver(NumbaLogicSolver):
    """兼容旧接口的 Numba 逻辑求解器；Naked Single 保持旧优先级。"""

    pass


HARDEST = """
..3..5.1.
..893.45.
2.57.436.
53..4719.
78.193.45
..956..73
..7.5..2.
..4..9.3.
..1....8.
"""


if __name__ == "__main__":
    board = parse(HARDEST)
    solver = LogicSolver(board)
    solver.solve()
