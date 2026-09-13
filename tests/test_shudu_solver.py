"""验证 shudu-solver 的候选所有权和技巧优先级。"""

from copy import deepcopy

from sudoku_game import Game
from shudu_solver import ShuduSolver


def test_hidden_single_is_highest_priority_non_marking_rule():
    solver = ShuduSolver(Game().board)
    names = [technique.__name__ for technique in solver._non_marking_techniques()]
    assert names == ["hidden_single", "naked_single"]


def test_first_step_uses_hidden_single_when_available():
    solver = ShuduSolver(Game().board)
    assert solver._apply_next_step()
    assert solver.steps[-1].find("Hidden Single:") >= 0


def test_algorithm_candidates_do_not_depend_on_user_notes():
    game = Game()
    solver = ShuduSolver(game.board)
    before = solver.algorithm_candidates()
    game.notes = {(0, 0): {1}, (0, 1): {2, 3}}
    after = solver.algorithm_candidates()
    assert after == before


def test_algorithm_candidate_snapshot_is_not_live_state():
    solver = ShuduSolver(Game().board)
    snapshot = solver.algorithm_candidates()
    original = deepcopy(solver.cands)
    snapshot[0][0].clear()
    assert solver.cands == original


def test_hidden_single_directly_places_from_internal_candidates():
    solver = ShuduSolver(Game().board)
    before = deepcopy(solver.board)
    assert solver.hidden_single()
    assert solver.board != before
    assert solver.steps[-1].find("唯一可能位置") >= 0
