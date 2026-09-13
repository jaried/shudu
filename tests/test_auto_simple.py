"""验证简单算法自动求解的边界与设置行为。
自动范围包含 Single、Naked Pair、Naked Triple、Pointing Pair。
所有自动简单算法造成的候选删除都需要同步到当前小数字笔记。
自动求解不得把用户笔记作为算法推理前提或增加错误次数。
"""

from copy import deepcopy

from shudu_solver import ShuduSolver, SimpleSolveResult
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


def test_simple_solver_advances_board_without_backtracking():
    game = Game(auto_simple=True)
    before = deepcopy(game.board)
    count = game.auto_solve_simple()
    assert count > 0
    assert game.board != before
    assert game.mistakes == 0
    assert not game.history


def test_enabling_switch_runs_simple_solver_as_one_undoable_action():
    game = Game(auto_simple=False)
    before = deepcopy(game.board)
    game.set_auto_simple(True)
    assert game.auto_simple
    assert game.board != before
    assert len(game.history) == 1
    game.undo()
    assert game.board == before


def test_disabling_switch_does_not_change_board():
    game = Game(auto_simple=False)
    before = deepcopy(game.board)
    game.set_auto_simple(False)
    assert game.board == before
    assert not game.history


def test_auto_solver_ignores_user_notes():
    first = Game(auto_simple=True)
    second = Game(auto_simple=True)
    second.notes = {(0, 0): {1}, (0, 1): {2, 3}, (8, 8): {9}}
    first.auto_solve_simple()
    second.auto_solve_simple()
    assert second.board == first.board
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
    assert all(len(change) == 3 for change in result.eliminations)


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


def test_all_simple_eliminations_remove_matching_small_notes(monkeypatch):
    class FakeSolver:
        def __init__(self, board):
            self.board = [row[:] for row in board]

        def solve_simple_result(self):
            return SimpleSolveResult(0, ((0, 0, 1), (0, 0, 2), (0, 1, 2)))

    monkeypatch.setattr("sudoku_game.ShuduSolver", FakeSolver)
    game = Game(auto_simple=True)
    game.auto_clean = False
    game.notes = {(0, 0): {1, 2, 4}, (0, 1): {2, 3}, (8, 8): {9}}
    before = deepcopy(game.notes)
    count = game.auto_solve_simple(remember=True)
    assert count == 0
    assert game.notes == {(0, 0): {4}, (0, 1): {3}, (8, 8): {9}}
    assert "简单算法自动删除" in game.message
    assert len(game.history) == 1
    game.undo()
    assert game.notes == before


def test_real_simple_solver_syncs_every_reported_elimination_even_when_auto_clean_off():
    game = Game(auto_simple=False)
    candidates = candidate_grid(game.board)
    game.notes = {
        cell: set(candidates[cell[0]][cell[1]])
        for cell in CELLS
        if not game.value(cell)
    }
    solver = ShuduSolver(game.board)
    expected = solver.solve_simple_result()
    assert expected.eliminations
    game.auto_clean = False
    game.set_auto_simple(True)
    for row, col, digit in expected.eliminations:
        assert digit not in game.notes.get((row, col), set())
