"""共享的 Numba 数独逻辑求解器。
候选状态使用 1–9 的整数位掩码，全部核心技巧搜索由 njit 内核执行。
Python 层只负责日志、兼容接口和控制流，避免 UI/提示层触碰算法内部实现。
回溯仅在完整 solve() 卡住时作为既有 fallback，不参与单步逻辑提示。
"""

from __future__ import annotations

from typing import Iterable

import numpy as np

from sudoku_backtracking import DEFAULT_BACKTRACKING_SOLVER
from sudoku_njit_core import (
    apply_placement,
    candidate_sets,
    find_box_line,
    find_hidden_pair,
    find_hidden_single,
    find_naked_pair,
    find_naked_single,
    find_naked_triple,
    find_pointing_pair,
    find_x_wing,
    find_xy_wing,
    mask_digits,
    masks_from_board,
)
from sudoku_rules import BOXES, COLS, ROWS, Cell, box_cells, col_cells, row_cells, unit_name


class NumbaLogicSolver:
    """共享逻辑求解器：候选位掩码为唯一算法状态，模式搜索均走 njit。"""

    def __init__(self, board):
        self.board = [list(row) for row in board]
        self._masks = masks_from_board(self.board)
        self.steps: list[str] = []
        self.step_no = 0
        self.elim_count = 0
        self.fallback_used = False
        self.error_message: str | None = None
        return

    @property
    def cands(self):
        """兼容旧只读候选接口；真实热路径状态保存在整数位掩码中。"""
        result = candidate_sets(self._masks)
        return result

    def _board_array(self) -> np.ndarray:
        result = np.asarray(self.board, dtype=np.int64)
        return result

    def _non_marking_techniques(self):
        result = [self.naked_single, self.hidden_single]
        return result

    def algorithm_candidates(self):
        result = candidate_sets(self._masks)
        return result

    def _marking_techniques(self):
        result = [
            self.naked_pair,
            self.hidden_pair,
            self.naked_triple,
            self.pointing_pair,
            self.box_line_reduction,
            self.x_wing,
            self.xy_wing,
        ]
        return result

    def _techniques(self):
        result = self._non_marking_techniques() + self._marking_techniques()
        return result

    def _apply_next_step(self) -> bool:
        result = False
        for technique in self._techniques():
            if technique():
                result = True
                break
        return result

    def _place(self, row: int, col: int, digit: int) -> None:
        self.board[row][col] = digit
        apply_placement(self._masks, row, col, digit)
        return

    def _propagate_placement(self, row: int, col: int, digit: int) -> None:
        apply_placement(self._masks, row, col, digit)
        return

    def _rebuild_candidates(self) -> None:
        self._masks = masks_from_board(self.board)
        return

    def hidden_single(self) -> bool:
        unit_index, row, col, digit = find_hidden_single(self._board_array(), self._masks)
        result = unit_index >= 0
        if result:
            unit = _legacy_unit(unit_index)
            self._log(f"Hidden Single: {_format_cell(row, col)} = {digit}（{unit_name(unit)} 唯一可能位置）")
            self._place(row, col, digit)
        return result

    def naked_single(self) -> bool:
        row, col, digit = find_naked_single(self._board_array(), self._masks)
        result = row >= 0
        if result:
            self._log(f"Naked Single: {_format_cell(row, col)} = {digit}")
            self._place(row, col, digit)
        return result

    def naked_pair(self) -> bool:
        hit = find_naked_pair(self._board_array(), self._masks)
        result = hit[0] >= 0
        if result:
            self._apply_naked_pair(hit)
        return result

    def _apply_naked_pair(self, hit) -> None:
        unit_index, row_a, col_a, row_b, col_b, mask = hit
        source_order = ((row_a, col_a), (row_b, col_b))
        sources = set(source_order)
        targets = self._unit_targets(unit_index, mask, sources)
        numbers = mask_digits(mask)
        self._log(
            f"Naked Pair: {_format_cells(source_order)} 共享 {sorted(numbers)}，"
            f"{unit_name(_legacy_unit(unit_index))} 内 {_format_cells(targets)} 排除"
        )
        self._discard_mask(targets, mask)
        self.elim_count += len(targets)
        return

    def hidden_pair(self) -> bool:
        hit = find_hidden_pair(self._board_array(), self._masks)
        result = hit[0] >= 0
        if result:
            self._apply_hidden_pair(hit)
        return result

    def _apply_hidden_pair(self, hit) -> None:
        unit_index, row_a, col_a, row_b, col_b, digit_a, digit_b = hit
        cells = ((row_a, col_a), (row_b, col_b))
        pair_mask = (1 << digit_a) | (1 << digit_b)
        extras = set()
        for row, col in cells:
            extras.update(mask_digits(int(self._masks[row, col]) & ~pair_mask))
        self._log(
            f"Hidden Pair: {_format_cells(cells)} 在 {unit_name(_legacy_unit(unit_index))} 中出现数字 "
            f"{digit_a},{digit_b}，排除其他候选 {sorted(extras)}"
        )
        self._retain_mask(cells, pair_mask)
        self.elim_count += len(cells)
        return

    def naked_triple(self) -> bool:
        hit = find_naked_triple(self._board_array(), self._masks)
        result = hit[0] >= 0
        if result:
            self._apply_naked_triple(hit)
        return result

    def _apply_naked_triple(self, hit) -> None:
        unit_index, row_a, col_a, row_b, col_b, row_c, col_c, mask = hit
        source_order = ((row_a, col_a), (row_b, col_b), (row_c, col_c))
        targets = self._unit_targets(unit_index, mask, set(source_order))
        self._log(
            f"Naked Triple: {_format_cells(source_order)} 共享 {sorted(mask_digits(mask))}，"
            f"{unit_name(_legacy_unit(unit_index))} 内 {_format_cells(targets)} 排除"
        )
        self._discard_mask(targets, mask)
        self.elim_count += len(targets)
        return

    def pointing_pair(self) -> bool:
        hit = find_pointing_pair(self._board_array(), self._masks)
        result = hit[0] >= 0
        if result:
            self._apply_pointing_pair(hit)
        return result

    def _apply_pointing_pair(self, hit) -> None:
        base_row, base_col, digit, axis, line = hit
        targets = self._pointing_targets(base_row, base_col, digit, axis, line)
        axis_name = "行" if axis == 0 else "列"
        self._log(
            f"Pointing Pair: 宫 ({base_row + 1},{base_col + 1}) 中数字 {digit} 只在{axis_name} {line + 1}，"
            f"{_format_cells(targets)} 排除 {digit}"
        )
        self._discard_mask(targets, 1 << digit)
        self.elim_count += len(targets)
        return

    def box_line_reduction(self) -> bool:
        hit = find_box_line(self._board_array(), self._masks)
        result = hit[0] >= 0
        if result:
            self._apply_box_line(hit)
        return result

    def _apply_box_line(self, hit) -> None:
        axis, line, digit, base_row, base_col = hit
        targets = self._box_line_targets(axis, line, digit, base_row, base_col)
        axis_name = "行" if axis == 0 else "列"
        self._log(
            f"Box-Line: {axis_name} {line + 1} 中数字 {digit} 只在宫 ({base_row + 1},{base_col + 1})，"
            f"{_format_cells(targets)} 排除 {digit}"
        )
        self._discard_mask(targets, 1 << digit)
        self.elim_count += len(targets)
        return

    def x_wing(self) -> bool:
        hit = find_x_wing(self._board_array(), self._masks)
        result = hit[0] >= 0
        if result:
            self._apply_x_wing(hit)
        return result

    def _apply_x_wing(self, hit) -> None:
        axis, digit, row_a, row_b, col_a, col_b = hit
        targets = self._x_wing_targets(axis, digit, row_a, row_b, col_a, col_b)
        if axis == 0:
            message = f"X-Wing: 数字 {digit} 在行 {row_a + 1},{row_b + 1} 只出现在列 {col_a + 1},{col_b + 1}"
        else:
            message = f"X-Wing: 数字 {digit} 在列 {col_a + 1},{col_b + 1} 只出现在行 {row_a + 1},{row_b + 1}"
        self._log(f"{message}，{_format_cells(targets)} 排除 {digit}")
        self._discard_mask(targets, 1 << digit)
        self.elim_count += len(targets)
        return

    def xy_wing(self) -> bool:
        hit = find_xy_wing(self._board_array(), self._masks)
        result = hit[0] >= 0
        if result:
            self._apply_xy_wing(hit)
        return result

    def _apply_xy_wing(self, hit) -> None:
        pivot_row, pivot_col, row_a, col_a, row_b, col_b, digit = hit
        targets = self._xy_wing_targets(row_a, col_a, row_b, col_b, digit, (pivot_row, pivot_col))
        pivot = sorted(mask_digits(int(self._masks[pivot_row, pivot_col])))
        wing_a = sorted(mask_digits(int(self._masks[row_a, col_a])))
        wing_b = sorted(mask_digits(int(self._masks[row_b, col_b])))
        self._log(
            f"XY-Wing: 枢纽 {_format_cell(pivot_row, pivot_col)} {pivot}，"
            f"翼 {_format_cell(row_a, col_a)} {wing_a} + {_format_cell(row_b, col_b)} {wing_b}，"
            f"{_format_cells(targets)} 排除 {digit}"
        )
        self._discard_mask(targets, 1 << digit)
        self.elim_count += len(targets)
        return

    def _unit_targets(self, unit_index: int, mask: int, excluded: set[Cell]) -> list[Cell]:
        unit = _legacy_unit(unit_index)
        result = [cell for cell in unit if cell not in excluded and self._candidate_has(cell, mask)]
        return result

    def _candidate_has(self, cell: Cell, mask: int) -> bool:
        row, col = cell
        result = not self.board[row][col] and bool(int(self._masks[row, col]) & mask)
        return result

    def _pointing_targets(self, base_row: int, base_col: int, digit: int, axis: int, line: int) -> list[Cell]:
        bit = 1 << digit
        unit = row_cells(line) if axis == 0 else col_cells(line)
        box = set(box_cells(base_row, base_col))
        result = [cell for cell in unit if cell not in box and self._candidate_has(cell, bit)]
        return result

    def _box_line_targets(self, axis: int, line: int, digit: int, base_row: int, base_col: int) -> list[Cell]:
        bit = 1 << digit
        result = [
            cell
            for cell in box_cells(base_row, base_col)
            if (cell[0] != line if axis == 0 else cell[1] != line) and self._candidate_has(cell, bit)
        ]
        return result

    def _x_wing_targets(self, axis: int, digit: int, row_a: int, row_b: int, col_a: int, col_b: int) -> list[Cell]:
        bit = 1 << digit
        if axis == 0:
            cells = ((row, col) for row in range(9) if row not in (row_a, row_b) for col in (col_a, col_b))
        else:
            cells = ((row, col) for col in range(9) if col not in (col_a, col_b) for row in (row_a, row_b))
        result = [cell for cell in cells if self._candidate_has(cell, bit)]
        return result

    def _xy_wing_targets(self, row_a: int, col_a: int, row_b: int, col_b: int, digit: int, pivot: Cell) -> list[Cell]:
        bit = 1 << digit
        excluded = {pivot, (row_a, col_a), (row_b, col_b)}
        result = [
            (row, col)
            for row in range(9)
            for col in range(9)
            if (row, col) not in excluded
            and self._candidate_has((row, col), bit)
            and _sees((row, col), (row_a, col_a))
            and _sees((row, col), (row_b, col_b))
        ]
        return result

    def _discard_mask(self, cells: Iterable[Cell], mask: int) -> None:
        for row, col in cells:
            self._masks[row, col] = int(self._masks[row, col]) & ~mask
        return

    def _retain_mask(self, cells: Iterable[Cell], mask: int) -> None:
        for row, col in cells:
            self._masks[row, col] = int(self._masks[row, col]) & mask
        return

    def _try_backtracking_fallback(self) -> bool:
        result = DEFAULT_BACKTRACKING_SOLVER.solve(self.board)
        solved = result.solved and result.solution is not None
        if solved:
            self.fallback_used = True
            self.board = [row[:] for row in result.solution]
            self._rebuild_candidates()
            self._log("Fallback Backtracking: 逻辑推理无法继续，已用公共回溯能力补全解")
            print("检测到逻辑推理无法继续，已切换到公共回溯求解。")
        else:
            self.error_message = result.invalid_reason or "当前盘面无解，可能输入错误"
            print(f"错误：{self.error_message}")
        return solved

    def solve(self) -> bool:
        self._print_initial_state()
        result = False
        while True:
            if self._board_solved():
                self._print_solution()
                result = True
                break
            if self._apply_next_step():
                continue
            self._print_stalled_state()
            if not self._try_backtracking_fallback():
                break
        return result

    def _print_initial_state(self) -> None:
        print("初始棋盘：")
        _print_board(self.board)
        print()
        print("初始候选数：")
        self._show_candidates()
        print()
        return

    def _print_solution(self) -> None:
        print()
        print("✓ 解题完成！")
        print()
        self._print_steps()
        _print_board(self.board)
        print(f"共 {self.step_no} 步推理，{self.elim_count} 次排除")
        return

    def _print_stalled_state(self) -> None:
        print()
        print("⚠ 卡住了！以下技巧不足：")
        print("  Naked/Hidden Single ✓   Naked/Hidden Pair ✓")
        print("  Naked Triple ✓   Pointing Pair ✓   Box-Line ✓   X-Wing ✓")
        print()
        print("已填入：")
        _print_board(self.board)
        print("剩余候选：")
        self._show_candidates()
        print()
        print("开始使用公共回溯能力确认当前盘面是否有解。")
        return

    def _print_steps(self) -> None:
        print("推理步骤：")
        print()
        for line in self.steps:
            print(line)
        print()
        return

    def _show_candidates(self) -> None:
        candidates = self.cands
        horizontal = "+" + "-" * (9 * 8 + 2) + "+"
        print(horizontal)
        for row in range(9):
            line = "|"
            for col in range(9):
                line += self._candidate_text(row, col, candidates)
            print(line + "|")
            if row in (2, 5):
                print(horizontal)
        print(horizontal)
        return

    def _candidate_text(self, row: int, col: int, candidates) -> str:
        value = self.board[row][col]
        result = f"  {value}   "
        if not value:
            digits = "".join(str(digit) for digit in sorted(candidates[row][col]))
            result = f" {digits:<5} "
        return result

    def _board_solved(self) -> bool:
        result = all(self.board[row][col] != 0 for row in range(9) for col in range(9))
        return result

    def _log(self, message: str) -> None:
        self.step_no += 1
        self.steps.append(f"  [{self.step_no:3d}] {message}")
        return


def _legacy_unit(unit_index: int) -> tuple[Cell, ...]:
    if unit_index < 18:
        index = unit_index // 2
        result = ROWS[index] if unit_index % 2 == 0 else COLS[index]
    else:
        result = BOXES[unit_index - 18]
    return result


def _format_cell(row: int, col: int) -> str:
    result = f"({row + 1},{col + 1})"
    return result


def _format_cells(cells: Iterable[Cell]) -> str:
    result = ", ".join(_format_cell(row, col) for row, col in cells)
    return result


def _sees(first: Cell, second: Cell) -> bool:
    row, col = first
    other_row, other_col = second
    result = row == other_row or col == other_col or (row // 3, col // 3) == (other_row // 3, other_col // 3)
    return result


def _print_board(board) -> None:
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
