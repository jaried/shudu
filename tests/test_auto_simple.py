"""验证简单算法自动求解的边界与设置行为。
只覆盖 Naked Pair 及以下技巧，不允许 Hidden Pair 及更高技巧混入自动路径。
Naked Pair 的算法候选删除需要同步到当前小数字笔记。
自动求解不得把用户笔记作为算法推理前提或增加错误次数。
"""

from copy import deepcopy

from shudu_solver import ShuduSolver, SimpleSolveResult
from sudoku_game import Game
from sudoku_njit_core import ALL_DIGITS_MASK


def test_simple_techniques_stop_at_naked_pair():
    solver = ShuduSolver(Game().board)
    names = [technique.__name__ for technique in solver.simple_techniques()]
    assert names == [
        "hidden_single",
        "naked_single",
        "naked_pair",
    ]
    assert "hidden_pair" not in names
    assert "naked_triple" not in names
    assert "pointing_pair" not in names
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


def test_naked_pair_eliminations_remove_matching_small_notes_and_undo(monkeypatch):
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
    assert "Naked Pair" in game.message
    assert len(game.history) == 1
    game.undo()
    assert game.notes == before
