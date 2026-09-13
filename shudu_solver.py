"""提供 shudu 使用的逻辑求解器入口。
在既有 LogicSolver 上定义项目需要的技巧优先级和稳定一步 API。
算法候选来自求解器自己的 cands，不读取 GUI 用户笔记。
高级技巧继续复用既有实现，避免复制规则和制造第二套求解器。
"""

from __future__ import annotations

from logical_solver import LogicSolver, parse, print_board
from sudoku_rules import box_cells, col_cells, row_cells
from sudoku_step import LogicStep, capture_candidates, step_changes


class ShuduSolver(LogicSolver):
    """项目级逻辑求解器：行、列、宫唯一落点优先。"""

    def _non_marking_techniques(self):
        result = [self.hidden_single, self.naked_single]
        return result

    def algorithm_candidates(self):
        """返回算法内部候选快照；调用方修改快照不会影响求解器。"""
        result = [[set(values) for values in row] for row in self.cands]
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


if __name__ == "__main__":
    # 直接修改这里即可像 GUI 一样自定义题面；0 或 . 表示空格。
    CUSTOM_BOARD = DEFAULT_BOARD
    main(CUSTOM_BOARD)
