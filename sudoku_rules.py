"""数独的共享拓扑与基础候选规则。
本模块不依赖 GUI、求解器状态或用户手工笔记。
所有调用方共享同一套行、列、宫与候选定义，避免规则漂移。
只处理确定性基础约束，不实现高级逻辑技巧。
"""

from __future__ import annotations

from collections.abc import Sequence

SIZE = 9
BOX_SIZE = 3
DIGITS = frozenset(range(1, SIZE + 1))

Cell = tuple[int, int]
BoardLike = Sequence[Sequence[int]]
Candidates = list[list[set[int]]]

CELLS = tuple((row, col) for row in range(SIZE) for col in range(SIZE))


def row_cells(row: int) -> tuple[Cell, ...]:
    result = tuple((row, col) for col in range(SIZE))
    return result


def col_cells(col: int) -> tuple[Cell, ...]:
    result = tuple((row, col) for row in range(SIZE))
    return result


def box_cells(row: int, col: int) -> tuple[Cell, ...]:
    box_row = row // BOX_SIZE * BOX_SIZE
    box_col = col // BOX_SIZE * BOX_SIZE
    result = tuple(
        (box_row + row_offset, box_col + col_offset)
        for row_offset in range(BOX_SIZE)
        for col_offset in range(BOX_SIZE)
    )
    return result


ROWS = tuple(row_cells(row) for row in range(SIZE))
COLS = tuple(col_cells(col) for col in range(SIZE))
BOXES = tuple(
    box_cells(row, col)
    for row in range(0, SIZE, BOX_SIZE)
    for col in range(0, SIZE, BOX_SIZE)
)
UNITS = ROWS + COLS + BOXES


def related(first: Cell, second: Cell) -> bool:
    row, col = first
    other_row, other_col = second
    same_box = (row // BOX_SIZE, col // BOX_SIZE) == (
        other_row // BOX_SIZE,
        other_col // BOX_SIZE,
    )
    result = row == other_row or col == other_col or same_box
    return result


PEERS = {
    cell: frozenset(other for other in CELLS if other != cell and related(cell, other))
    for cell in CELLS
}


def unit_name(cells: Sequence[Cell]) -> str:
    first_row, first_col = cells[0]
    last_row, last_col = cells[-1]
    result = f"宫 ({first_row // BOX_SIZE * BOX_SIZE + 1},{first_col // BOX_SIZE * BOX_SIZE + 1})"
    if first_row == last_row:
        result = f"行 {first_row + 1}"
    elif first_col == last_col:
        result = f"列 {first_col + 1}"
    return result


def candidate_grid(board: BoardLike) -> Candidates:
    """仅依据正式大数字计算每个空格的基础合法候选。"""
    row_used = _row_used(board)
    col_used = _col_used(board)
    box_used = _box_used(board)
    result = [
        [
            set() if board[row][col] else set(DIGITS - row_used[row] - col_used[col] - box_used[_box_index(row, col)])
            for col in range(SIZE)
        ]
        for row in range(SIZE)
    ]
    return result


def _row_used(board: BoardLike) -> list[set[int]]:
    result = [{value for value in board[row] if value} for row in range(SIZE)]
    return result


def _col_used(board: BoardLike) -> list[set[int]]:
    result = [
        {board[row][col] for row in range(SIZE) if board[row][col]}
        for col in range(SIZE)
    ]
    return result


def _box_used(board: BoardLike) -> list[set[int]]:
    result = [set() for _ in range(SIZE)]
    for row, col in CELLS:
        value = board[row][col]
        if value:
            result[_box_index(row, col)].add(value)
    return result


def _box_index(row: int, col: int) -> int:
    result = row // BOX_SIZE * BOX_SIZE + col // BOX_SIZE
    return result
