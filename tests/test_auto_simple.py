"""验证简单算法自动求解的边界与设置行为。
只覆盖 Naked Pair 及以下技巧，不允许 Hidden Pair 及更高技巧混入自动路径。
Game 单元测试显式控制开关，产品入口负责默认开启。
自动求解不得读取用户笔记或增加错误次数。
"""

from copy import deepcopy

from shudu_solver import ShuduSolver
from sudoku_game import Game


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
