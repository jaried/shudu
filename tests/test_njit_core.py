"""验证全部产品逻辑核心都由 Numba nopython 内核承载。"""

import numpy as np
import pytest
from sudoku_logic import NumbaLogicSolver
from sudoku_njit_core import (
    candidate_masks,
    find_box_line,
    find_hidden_pair,
    find_hidden_single,
    find_hidden_triple,
    find_naked_pair,
    find_naked_single,
    find_naked_triple,
    find_pointing_pair,
    find_x_wing,
    find_xy_wing,
)
from sudoku_rules import box_cells, col_cells, row_cells

from logical_solver import LogicSolver
from shudu_solver import ShuduSolver

CORE_FINDERS = (
    find_hidden_single,
    find_naked_single,
    find_naked_pair,
    find_hidden_pair,
    find_naked_triple,
    find_hidden_triple,
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


@pytest.mark.parametrize(
    "unit,cells",
    (
        (row_cells(0), ((0, 0), (0, 4), (0, 8))),
        (col_cells(0), ((0, 0), (4, 0), (8, 0))),
        (box_cells(3, 3), ((3, 5), (4, 4), (4, 5))),
    ),
)
def test_hidden_triple_finder_covers_rows_columns_and_boxes(unit, cells):
    board = np.zeros((9, 9), dtype=np.int64)
    masks = candidate_masks(board)
    triple = (1 << 2) | (1 << 5) | (1 << 8)
    for cell in unit:
        masks[cell] &= ~triple
    for cell, digits in zip(cells, ({1, 2, 5}, {2, 4, 5, 8}, {5, 8, 9})):
        masks[cell] = sum(1 << digit for digit in digits)
    before = masks.copy()
    hit = find_hidden_triple(board, masks)
    assert hit[0] >= 0 and hit[-1] == triple
    assert {(hit[1], hit[2]), (hit[3], hit[4]), (hit[5], hit[6])} == set(cells)
    np.testing.assert_array_equal(masks, before)


@pytest.mark.parametrize("case", ("four_cells", "missing_digit", "no_extras", "filled_cell"))
def test_hidden_triple_finder_requires_three_present_digits_and_real_deletion(case):
    board = np.zeros((9, 9), dtype=np.int64)
    masks = candidate_masks(board)
    triple = (1 << 2) | (1 << 5) | (1 << 8)
    for cell in row_cells(0):
        masks[cell] &= ~triple
    for col, digits in ((0, {1, 2, 5}), (4, {2, 4, 5, 8}), (8, {5, 8, 9})):
        masks[0, col] = sum(1 << digit for digit in digits)
    if case == "four_cells":
        masks[0, 6] |= 1 << 8
    elif case == "missing_digit":
        masks[0] &= ~(1 << 8)
    elif case == "no_extras":
        for col in (0, 4, 8):
            masks[0, col] &= triple
    else:
        board[0, 8] = 9
    assert find_hidden_triple(board, masks)[0] == -1
