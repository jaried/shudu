"""项目级逻辑求解器的 CLI 与历史导入 Adapter。"""

from __future__ import annotations

from logical_solver import parse, print_board
from shudu.auto_techniques import (
    AUTO_TECHNIQUE_NAMES,
    AUTO_TECHNIQUE_SPECS,
    DEFAULT_AUTO_TECHNIQUES,
    validate_auto_techniques,
)
from shudu.logic_solver import (
    Change,
    LogicStep,
    NumbaLogicSolver,
    ShuduSolver,
    SimpleSolveResult,
    capture_candidates,
    step_changes,
)


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
    main(DEFAULT_BOARD)
