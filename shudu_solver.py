"""提供 shudu 使用的项目级逻辑求解器。
核心候选与所有技巧搜索继承共享 Numba 实现。
本层定义项目技巧优先级、简单算法边界、结构化一步 API 和命令行入口。
算法候选独立于 GUI 用户笔记，不复制高级数独规则。
"""

from __future__ import annotations

from logical_solver import parse, print_board
from sudoku_logic import NumbaLogicSolver
from sudoku_rules import box_cells, col_cells, row_cells
from sudoku_step import LogicStep, capture_candidates, step_changes


class ShuduSolver(NumbaLogicSolver):
    """shudu 项目求解器：行、列、宫唯一落点优先。"""

    def _non_marking_techniques(self):
        result = [self.hidden_single, self.naked_single]
        return result

    def simple_techniques(self):
        """返回 Naked Pair 及以下简单算法；Hidden Pair 起不自动执行。"""
        result = [
            self.hidden_single,
            self.naked_single,
            self.naked_pair,
        ]
        return result

    def apply_simple_step(self) -> bool:
        """执行一个简单算法步骤；没有可执行步骤时返回 False。"""
        result = False
        for technique in self.simple_techniques():
            if technique():
                result = True
                break
        return result

    def solve_simple(self) -> int:
        """连续执行简单算法直到稳定，返回本轮自动填入的大数字数量。"""
        before = sum(bool(value) for row in self.board for value in row)
        while self.apply_simple_step():
            pass
        after = sum(bool(value) for row in self.board for value in row)
        result = after - before
        return result

    def next_step(self) -> LogicStep | None:
        """执行且返回一个结构化逻辑步骤；不使用回溯。"""
        before = [row[:] for row in self.board]
        candidates = capture_candidates(self.cands)
        result = None
        if self._apply_next_step():
            placements, eliminations = step_changes(before, self.board, candidates, self.cands)
            result = LogicStep(
                self._last_message(),
                placements,
                eliminations,
                (),
                self._placement_units(placements),
                candidates,
            )
        return result

    def _last_message(self) -> str:
        result = self.steps[-1].split("] ", 1)[-1] if self.steps else ""
        return result

    def _placement_units(self, placements) -> tuple:
        result = ()
        if placements:
            row, col, _ = placements[0]
            result = (row_cells(row), col_cells(col), box_cells(row, col))
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
