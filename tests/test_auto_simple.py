"""验证简单算法自动求解、候选状态与自动笔记联动。
自动范围包含 Single、Naked Pair、Naked Triple、Pointing Pair。
自动简单算法必须持续到固定点，并用最终算法候选刷新全部小数字。
算法推理不得读取用户手工笔记，也不得增加错误次数。
"""

from copy import deepcopy

from shudu_solver import ShuduSolver
from sudoku_game import Game
from sudoku_njit_core import ALL_DIGITS_MASK
from sudoku_rules import CELLS, candidate_grid


def test_simple_techniques_include_triple_and_pointing():
    solver = ShuduSolver(Game().board)
    names = [technique.__name__ for technique in solver.simple_techniques()]
    assert names == [
        "hidden_single",
        "naked_single",
        "naked_pair",
        "naked_triple",
        "pointing_pair",
    ]
    assert "hidden_pair" not in names
    assert "box_line_reduction" not in names
    assert "x_wing" not in names
    assert "xy_wing" not in names


def test_simple_solver_advances_board_and_generates_notes():
    game = Game(auto_simple=True)
    before = deepcopy(game.board)
    count = game.auto_solve_simple()
    assert count > 0
    assert game.board != before
    assert game.notes
    assert game.notes_mode
    assert game.mistakes == 0
    assert not game.history


def test_simple_solver_runs_until_no_simple_step_remains():
    solver = ShuduSolver(Game(auto_simple=False).board)
    solver.solve_simple_result()
    assert not solver.apply_simple_step()


def test_enabling_switch_runs_solver_and_auto_notes_as_one_undoable_action():
    game = Game(auto_simple=False)
    before = deepcopy(game.board)
    game.set_auto_simple(True)
    assert game.auto_simple
    assert game.board != before
    assert game.notes
    assert game.notes_mode
    assert len(game.history) == 1
    game.undo()
    assert game.board == before
    assert not game.notes


def test_disabling_switch_does_not_change_board():
    game = Game(auto_simple=False)
    before = deepcopy(game.board)
    game.set_auto_simple(False)
    assert game.board == before
    assert not game.history


def test_auto_solver_ignores_user_notes_and_replaces_them_with_algorithm_candidates():
    first = Game(auto_simple=True)
    second = Game(auto_simple=True)
    second.notes = {(0, 0): {1}, (0, 1): {2, 3}, (8, 8): {9}}
    first.auto_solve_simple()
    second.auto_solve_simple()
    assert second.board == first.board
    assert second.notes == first.notes
    assert second.mistakes == 0


def test_simple_result_records_real_naked_pair_candidate_eliminations():
    solver = ShuduSolver([[0] * 9 for _ in range(9)])
    solver._masks[:, :] = ALL_DIGITS_MASK
    pair_mask = (1 << 1) | (1 << 2)
    solver._masks[0, 0] = pair_mask
    solver._masks[0, 1] = pair_mask
    solver._masks[0, 2] = pair_mask | (1 << 3)
    result = solver.solve_simple_result()
    assert (0, 2, 1) in result.eliminations
    assert (0, 2, 2) in result.eliminations


def test_simple_result_records_naked_triple_eliminations():
    solver = ShuduSolver([[0] * 9 for _ in range(9)])
    solver._masks[:, :] = ALL_DIGITS_MASK
    solver._masks[0, 0] = (1 << 1) | (1 << 2)
    solver._masks[0, 1] = (1 << 1) | (1 << 3)
    solver._masks[0, 2] = (1 << 2) | (1 << 3)
    solver.simple_techniques = lambda: [solver.naked_triple]
    result = solver.solve_simple_result()
    assert (0, 3, 1) in result.eliminations
    assert (0, 3, 2) in result.eliminations
    assert (0, 3, 3) in result.eliminations


def test_simple_result_records_pointing_pair_eliminations():
    solver = ShuduSolver([[0] * 9 for _ in range(9)])
    solver._masks[:, :] = ALL_DIGITS_MASK
    bit = 1 << 1
    for row in range(3):
        for col in range(3):
            solver._masks[row, col] &= ~bit
    solver._masks[0, 0] |= bit
    solver._masks[0, 1] |= bit
    solver.simple_techniques = lambda: [solver.pointing_pair]
    result = solver.solve_simple_result()
    assert (0, 3, 1) in result.eliminations
    assert (0, 8, 1) in result.eliminations


def test_prior_algorithm_eliminations_survive_next_solver_and_form_naked_pair():
    board = [
        [6, 7, 4, 0, 5, 0, 0, 0, 2],
        [0, 0, 2, 0, 0, 7, 5, 0, 0],
        [9, 0, 0, 0, 0, 3, 0, 0, 7],
        [0, 9, 0, 0, 7, 1, 0, 0, 8],
        [0, 2, 0, 9, 3, 4, 7, 6, 1],
        [0, 0, 7, 0, 8, 0, 0, 0, 9],
        [0, 4, 9, 0, 0, 0, 0, 2, 0],
        [0, 8, 0, 0, 4, 5, 0, 0, 0],
        [0, 0, 1, 3, 0, 0, 0, 7, 0],
    ]
    solver = ShuduSolver(board)
    solver.apply_candidate_eliminations(((6, 6, 1), (6, 6, 3)))
    result = solver.solve_simple_result()
    assert (6, 3, 6) in result.eliminations
    assert (6, 3, 8) in result.eliminations


def test_auto_simple_notes_equal_final_solver_candidates():
    game = Game(auto_simple=False)
    solver = ShuduSolver(game.board)
    expected_result = solver.solve_simple_result()
    expected_candidates = solver.algorithm_candidates()
    expected_notes = {
        cell: set(expected_candidates[cell[0]][cell[1]])
        for cell in CELLS
        if not solver.board[cell[0]][cell[1]] and expected_candidates[cell[0]][cell[1]]
    }
    game.set_auto_simple(True)
    assert game.notes == expected_notes
    assert game.simple_eliminations == set(expected_result.eliminations)


def test_auto_notes_uses_algorithm_candidates_when_auto_simple_enabled():
    game = Game(auto_simple=False)
    game.auto_simple = True
    game.auto_notes()
    solver = ShuduSolver(game.givens)
    solver.solve_simple_result()
    expected = solver.algorithm_candidates()
    for cell in CELLS:
        if not game.value(cell):
            assert game.notes.get(cell, set()) == set(expected[cell[0]][cell[1]])
    assert game.notes_mode
    assert len(game.history) == 1


def test_plain_auto_notes_still_uses_basic_candidates_when_auto_simple_disabled():
    game = Game(auto_simple=False)
    expected = candidate_grid(game.board)
    game.auto_notes()
    for cell in CELLS:
        if not game.value(cell):
            assert game.notes[cell] == set(expected[cell[0]][cell[1]])
