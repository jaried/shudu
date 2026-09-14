"""提供 shudu 使用的项目级逻辑求解器入口。
核心候选与所有技巧搜索继承共享 Numba 实现。
本层定义项目技巧选择、自动求解优先级和结构化 next_step() Interface。
算法执行时直接产出提示证据，提示层不再复制高级数独规则。
"""

from __future__ import annotations

from dataclasses import dataclass

from logical_solver import parse, print_board
from shudu.auto_techniques import (
    AUTO_TECHNIQUE_NAMES,
    AUTO_TECHNIQUE_SPECS,
    DEFAULT_AUTO_TECHNIQUES,
    validate_auto_techniques,
)
from shudu.sudoku_logic import NumbaLogicSolver
from shudu.sudoku_rules import CELLS, box_cells, col_cells, related, row_cells
from shudu.sudoku_step import Change, LogicStep, capture_candidates, step_changes


@dataclass(frozen=True)
class SimpleSolveResult:
    placements: int
    eliminations: tuple[Change, ...]


class ShuduSolver(NumbaLogicSolver):
    """shudu 项目求解器：按统一目录选择并执行逻辑算法。"""

    def _non_marking_techniques(self):
        result = [self.hidden_single, self.naked_single]
        return result

    def techniques_for(self, names) -> list:
        """按固定优先级返回指定算法，未知名称立即失败。"""
        selected = validate_auto_techniques(names)
        result = [
            getattr(self, name)
            for name in AUTO_TECHNIQUE_NAMES
            if name in selected
        ]
        return result

    def simple_techniques(self):
        """兼容既有简单算法接口；内容等于默认自动算法集合。"""
        result = self.techniques_for(DEFAULT_AUTO_TECHNIQUES)
        return result

    def apply_candidate_eliminations(self, eliminations) -> None:
        """恢复此前自动算法已证明的候选删除，不读取用户手工笔记。"""
        for row, col, digit in eliminations:
            if not self.board[row][col]:
                self._masks[row, col] = int(self._masks[row, col]) & ~(1 << digit)
        return

    def apply_technique_step(self, names) -> bool:
        """执行指定自动算法中的一步；没有可执行步骤时返回 False。"""
        result, _ = self._apply_technique_step_with_eliminations(names)
        return result

    def apply_simple_step(self) -> bool:
        """兼容既有简单算法接口。"""
        result = self.apply_technique_step(DEFAULT_AUTO_TECHNIQUES)
        return result

    def _apply_technique_step_with_eliminations(self, names) -> tuple[bool, tuple[Change, ...]]:
        """执行一步并返回这一步在算法候选中产生的全部删除。"""
        result = False
        eliminations: tuple[Change, ...] = ()
        for technique in self.techniques_for(names):
            before = capture_candidates(self.cands)
            if technique():
                result = True
                eliminations = _candidate_eliminations(before, self.cands)
                break
        return result, eliminations

    def solve_techniques_result(self, names) -> SimpleSolveResult:
        """反复从最高优先级扫描，直到所选自动算法都无法继续。"""
        selected = tuple(names)
        before = sum(bool(value) for row in self.board for value in row)
        removed: list[Change] = []
        while True:
            progressed, eliminations = self._apply_technique_step_with_eliminations(selected)
            if not progressed:
                break
            removed.extend(eliminations)
        after = sum(bool(value) for row in self.board for value in row)
        result = SimpleSolveResult(after - before, tuple(dict.fromkeys(removed)))
        return result

    def solve_simple_result(self) -> SimpleSolveResult:
        """兼容既有简单算法接口，执行默认自动算法直到固定点。"""
        result = self.solve_techniques_result(DEFAULT_AUTO_TECHNIQUES)
        return result

    def solve_simple(self) -> int:
        """连续执行默认自动算法直到稳定，返回本轮自动填入数量。"""
        result = self.solve_simple_result().placements
        return result

    def next_step(self) -> LogicStep | None:
        """执行并返回完整一步事实；不使用回溯，也不要求提示层重建证据。"""
        before = [row[:] for row in self.board]
        candidates = capture_candidates(self.cands)
        result = None
        if self._apply_next_step():
            placements, eliminations = step_changes(before, self.board, candidates, self.cands)
            message = self._last_message()
            sources, units = self._step_context(message, before, candidates, placements)
            result = LogicStep(
                message,
                placements,
                eliminations,
                sources,
                units,
                candidates,
            )
        return result

    def _step_context(self, message, board, candidates, placements):
        sources = self._last_sources
        units = self._last_units
        if placements and message.startswith("Hidden Single:"):
            row, col, digit = placements[0]
            unit = self._preferred_hidden_single_unit(candidates, row, col, digit)
            units = (unit,)
            sources = self._hidden_single_evidence(board, unit, (row, col), digit)
        result = (sources, units)
        return result

    def _preferred_hidden_single_unit(self, candidates, row: int, col: int, digit: int):
        preferred = (box_cells(row, col), row_cells(row), col_cells(col))
        result = next(
            (
                unit
                for unit in preferred
                if sum(digit in candidates[item_row][item_col] for item_row, item_col in unit) == 1
            ),
            self._last_units[0],
        )
        return result

    def _hidden_single_evidence(self, board, unit, target, digit: int) -> tuple:
        empty_others = tuple(
            cell
            for cell in unit
            if cell != target and not board[cell[0]][cell[1]]
        )
        result = tuple(
            cell
            for cell in CELLS
            if board[cell[0]][cell[1]] == digit
            and any(related(cell, other) for other in empty_others)
        )
        return result

    def _last_message(self) -> str:
        result = self.steps[-1].split("] ", 1)[-1] if self.steps else ""
        return result


def _candidate_eliminations(before, after) -> tuple[Change, ...]:
    result = tuple(
        (row, col, digit)
        for row in range(9)
        for col in range(9)
        for digit in sorted(before[row][col] - set(after[row][col]))
    )
    return result


DEFAULT_BOARD = """
....9.6.7
.......1.
9.7.2.53.
4...5....
.....8...
13..4.79.
6.89.....
.1.5....2
.......5.
"""


def main(board_text: str = DEFAULT_BOARD) -> None:
    board = parse(board_text)
    solver = ShuduSolver(board)
    solved = solver.solve()
    if solved:
        print_board(solver.board)
    return


if __name__ == "__main__":
    CUSTOM_BOARD = DEFAULT_BOARD
    main(CUSTOM_BOARD)
