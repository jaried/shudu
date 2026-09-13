"""验证全部产品逻辑核心都由 Numba nopython 内核承载。"""

import numpy as np

from logical_solver import LogicSolver
from shudu_solver import ShuduSolver
from sudoku_logic import NumbaLogicSolver
from sudoku_njit_core import (
    candidate_masks,
    find_box_line,
    find_hidden_pair,
    find_hidden_single,
    find_naked_pair,
    find_naked_single,
    find_naked_triple,
    find_pointing_pair,
    find_x_wing,
    find_xy_wing,
)


CORE_FINDERS = (
    find_hidden_single,
    find_naked_single,
    find_naked_pair,
    find_hidden_pair,
    find_naked_triple,
    find_pointing_pair,
    find_box_line,
    find_x_wing,
    find_xy_wing,
)


def test_all_core_finders_compile_in_nopython_mode():
    board = np.zeros((9, 9), dtype=np.int64)
    masks = candidate_masks(board)
    for finder in CORE_FINDERS:
        finder(board, masks)
        assert finder.nopython_signatures
    assert candidate_masks.nopython_signatures


def test_both_public_logic_solvers_share_njit_core():
    assert issubclass(LogicSolver, NumbaLogicSolver)
    assert issubclass(ShuduSolver, NumbaLogicSolver)


def test_shudu_keeps_hidden_single_priority_while_legacy_order_is_compatible():
    legacy = [method.__name__ for method in LogicSolver([[0] * 9 for _ in range(9)])._non_marking_techniques()]
    shudu = [method.__name__ for method in ShuduSolver([[0] * 9 for _ in range(9)])._non_marking_techniques()]
    assert legacy == ["naked_single", "hidden_single"]
    assert shudu == ["hidden_single", "naked_single"]
