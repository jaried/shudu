"""
Shared Sudoku backtracking solver.

This module centralizes the fallback solving capability used by both
`solver.py` and `logical_solver.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np
from numba import njit


Grid = List[List[int]]
BoardLike = Sequence[Sequence[Optional[int]]]
ALL_DIGITS_MASK = 0x3FE


def normalize_board(board: BoardLike) -> Grid:
    """Convert a board to a 9x9 int grid where 0 means empty."""
    return [
        [0 if value is None else int(value) for value in row]
        for row in board
    ]


@njit(cache=True)
def _count_bits(mask: int) -> int:
    count = 0
    while mask:
        mask &= mask - 1
        count += 1
    return count


@njit(cache=True)
def _bit_to_digit(bit: int) -> int:
    for digit in range(1, 10):
        if bit == (1 << digit):
            return digit
    return 0


@njit(cache=True)
def _search(grid: np.ndarray, row_masks: np.ndarray, col_masks: np.ndarray, box_masks: np.ndarray) -> bool:
    best_row = -1
    best_col = -1
    best_mask = 0
    best_count = 10

    for row in range(9):
        for col in range(9):
            if grid[row, col] != 0:
                continue
            box = (row // 3) * 3 + (col // 3)
            used_mask = row_masks[row] | col_masks[col] | box_masks[box]
            candidate_mask = ALL_DIGITS_MASK & ~used_mask
            candidate_count = _count_bits(candidate_mask)
            if candidate_count == 0:
                return False
            if candidate_count < best_count:
                best_count = candidate_count
                best_mask = candidate_mask
                best_row = row
                best_col = col
                if candidate_count == 1:
                    break
        if best_count == 1:
            break

    if best_row == -1:
        return True

    box = (best_row // 3) * 3 + (best_col // 3)
    candidate_mask = best_mask

    while candidate_mask:
        bit = candidate_mask & -candidate_mask
        digit = _bit_to_digit(bit)

        grid[best_row, best_col] = digit
        row_masks[best_row] |= bit
        col_masks[best_col] |= bit
        box_masks[box] |= bit

        if _search(grid, row_masks, col_masks, box_masks):
            return True

        grid[best_row, best_col] = 0
        row_masks[best_row] &= ~bit
        col_masks[best_col] &= ~bit
        box_masks[box] &= ~bit
        candidate_mask ^= bit

    return False


@dataclass
class BacktrackingResult:
    solved: bool
    solution: Optional[Grid]
    invalid_reason: Optional[str] = None


class BacktrackingSolver:
    """Validate a Sudoku board and solve it with a shared JIT fallback."""

    def validate(self, board: BoardLike) -> Optional[str]:
        grid = normalize_board(board)

        for row in range(9):
            seen = set()
            for value in grid[row]:
                if value == 0:
                    continue
                if value < 1 or value > 9:
                    return f"第 {row + 1} 行存在非法数字 {value}"
                if value in seen:
                    return f"第 {row + 1} 行数字 {value} 重复"
                seen.add(value)

        for col in range(9):
            seen = set()
            for row in range(9):
                value = grid[row][col]
                if value == 0:
                    continue
                if value in seen:
                    return f"第 {col + 1} 列数字 {value} 重复"
                seen.add(value)

        for box_row in range(0, 9, 3):
            for box_col in range(0, 9, 3):
                seen = set()
                for row in range(box_row, box_row + 3):
                    for col in range(box_col, box_col + 3):
                        value = grid[row][col]
                        if value == 0:
                            continue
                        if value in seen:
                            return f"宫 ({box_row + 1},{box_col + 1}) 中数字 {value} 重复"
                        seen.add(value)

        return None

    def solve(self, board: BoardLike) -> BacktrackingResult:
        invalid_reason = self.validate(board)
        if invalid_reason is not None:
            return BacktrackingResult(False, None, invalid_reason)

        grid = np.array(normalize_board(board), dtype=np.int64)
        row_masks = np.zeros(9, dtype=np.int64)
        col_masks = np.zeros(9, dtype=np.int64)
        box_masks = np.zeros(9, dtype=np.int64)

        for row in range(9):
            for col in range(9):
                value = int(grid[row, col])
                if value == 0:
                    continue
                bit = 1 << value
                box = (row // 3) * 3 + (col // 3)
                row_masks[row] |= bit
                col_masks[col] |= bit
                box_masks[box] |= bit

        solved = _search(grid, row_masks, col_masks, box_masks)
        if not solved:
            return BacktrackingResult(False, None, "当前盘面无解，可能输入错误")

        return BacktrackingResult(True, grid.tolist(), None)


DEFAULT_BACKTRACKING_SOLVER = BacktrackingSolver()
