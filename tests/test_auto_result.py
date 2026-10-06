from copy import deepcopy
from dataclasses import fields

import numpy as np
import pytest

from shudu.logic_solver import AutoSolveResult, ShuduSolver, solve_auto
from shudu.logic_solver._diff import mask_diff
from shudu.sudoku_game import Game
from shudu.sudoku_puzzles import Puzzle

AUTO_NOTES_PUZZLE = Puzzle(
    "自动结果测试",
    "测试",
    ("12345678.",) + (".........",) * 8,
)


def _single_masks() -> tuple[np.ndarray, np.ndarray]:
    before = np.zeros((9, 9), dtype=np.int64)
    before[0, 0] = 1 << 1
    before[0, 1] = (1 << 1) | (1 << 2)
    before[0, 3] = (1 << 1) | (1 << 5)
    before[1, 0] = (1 << 1) | (1 << 3)
    before[1, 1] = (1 << 1) | (1 << 4)
    before[3, 0] = (1 << 1) | (1 << 6)
    before[3, 3] = (1 << 1) | (1 << 7)
    after = before.copy()
    after[0, 0] = 0
    for row, col in ((0, 1), (0, 3), (1, 0), (1, 1), (3, 0)):
        after[row, col] &= ~(1 << 1)
    return before, after


def _snapshot(game: Game) -> tuple:
    return (
        deepcopy(game.board),
        deepcopy(game.notes),
        deepcopy(game.history),
        set(game.simple_eliminations),
        game.status,
        game.active_digit,
        game.message,
        game.completed_units(),
    )


def test_solve_auto_returns_four_field_owned_envelope_without_mutating_input():
    board = AUTO_NOTES_PUZZLE.grid()
    before = deepcopy(board)
    first = solve_auto(board, {"hidden_single"}, ())
    second = solve_auto(board, {"hidden_single"}, ())

    assert tuple(field.name for field in fields(AutoSolveResult)) == (
        "board",
        "notes",
        "placements",
        "eliminations",
    )
    assert board == before
    assert first.placements == 1
    assert first.board[0][8] == 9
    assert first.board is not board
    assert first.board is not second.board
    assert first.notes is not second.notes
    assert all(first.notes[cell] is not second.notes[cell] for cell in first.notes)


def test_solve_auto_does_not_use_step_or_backtracking(monkeypatch):
    monkeypatch.setattr(ShuduSolver, "next_step", lambda self: pytest.fail("auto must not request LogicStep"))
    monkeypatch.setattr(
        ShuduSolver,
        "_try_backtracking_fallback",
        lambda self: pytest.fail("auto must not use backtracking"),
    )

    result = solve_auto(AUTO_NOTES_PUZZLE.grid(), {"hidden_single"}, ())

    assert result.placements == 1


def test_mask_diff_reports_single_placement_and_peer_propagation_in_order():
    before, after = _single_masks()

    raw, count = mask_diff(before, after)
    changes = tuple(tuple(int(value) for value in row) for row in raw[:count])

    assert changes == (
        (0, 0, 1),
        (0, 1, 1),
        (0, 3, 1),
        (1, 0, 1),
        (1, 1, 1),
        (3, 0, 1),
    )
    assert (3, 3, 1) not in changes
    assert mask_diff.nopython_signatures


def test_metadata_result_path_does_not_capture_candidates_or_final_notes(monkeypatch):
    calls = {"capture": 0, "notes": 0, "logic_step": 0}

    import shudu.logic_solver._project as project

    monkeypatch.setattr(
        project,
        "capture_candidates",
        lambda candidates: calls.__setitem__("capture", calls["capture"] + 1),
    )
    monkeypatch.setattr(
        ShuduSolver,
        "algorithm_candidates",
        lambda self: calls.__setitem__("notes", calls["notes"] + 1),
    )

    result = ShuduSolver([[0] * 9 for _ in range(9)]).solve_simple_result()

    assert result.placements == 0
    assert result.eliminations == ()
    assert calls == {"capture": 0, "notes": 0, "logic_step": 0}


def test_production_execution_surface_constructs_one_solver_and_one_final_notes(monkeypatch):
    import shudu.logic_solver._engine as engine
    import shudu.logic_solver._project as project
    from shudu.auto_techniques import AUTO_TECHNIQUE_NAMES

    counts = {
        "solver": 0,
        "finder": {name: 0 for name in AUTO_TECHNIQUE_NAMES},
        "candidate_sets": 0,
        "final_notes": 0,
        "capture_candidates": 0,
        "logic_step": 0,
    }
    original_solver = ShuduSolver
    original_algorithm_candidates = original_solver.algorithm_candidates
    original_candidate_sets = engine.candidate_sets

    def tracked_candidate_sets(masks):
        counts["candidate_sets"] += 1
        return original_candidate_sets(masks)

    def tracked_algorithm_candidates(self):
        counts["final_notes"] += 1
        return original_algorithm_candidates(self)

    def factory(board):
        counts["solver"] += 1
        solver = original_solver(board)
        for name in AUTO_TECHNIQUE_NAMES:
            original = getattr(solver, name)

            def tracked(original=original, name=name):
                counts["finder"][name] += 1
                return original()

            setattr(solver, name, tracked)
        return solver

    monkeypatch.setattr("shudu.logic_solver._auto.ShuduSolver", factory)
    monkeypatch.setattr(engine, "candidate_sets", tracked_candidate_sets)
    monkeypatch.setattr(original_solver, "algorithm_candidates", tracked_algorithm_candidates)
    monkeypatch.setattr(
        project,
        "capture_candidates",
        lambda candidates: counts.__setitem__("capture_candidates", counts["capture_candidates"] + 1),
    )

    result = solve_auto(AUTO_NOTES_PUZZLE.grid(), {"hidden_single"}, ())

    assert result.placements == 1
    assert counts["solver"] == 1
    assert counts["finder"]["hidden_single"] > 0
    assert all(counts["finder"][name] == 0 for name in AUTO_TECHNIQUE_NAMES if name != "hidden_single")
    assert counts["candidate_sets"] == 1
    assert counts["final_notes"] == 1
    assert counts["capture_candidates"] == 0
    assert counts["logic_step"] == 0


def test_game_gate_calls_no_capability_for_disabled_empty_paused_or_wrong(monkeypatch):
    calls = []
    monkeypatch.setattr("shudu.sudoku_game.solve_auto", lambda *args: calls.append(args))

    disabled = Game(AUTO_NOTES_PUZZLE, auto_techniques={"hidden_single"}, auto_solve=False)
    assert disabled.auto_solve_enabled() == 0

    empty = Game(AUTO_NOTES_PUZZLE, auto_techniques=set(), auto_solve=True)
    assert empty.auto_solve_enabled() == 0

    paused = Game(AUTO_NOTES_PUZZLE, auto_techniques={"hidden_single"}, auto_solve=True)
    paused.status = "paused"
    assert paused.auto_solve_enabled() == 0

    wrong = Game(AUTO_NOTES_PUZZLE, auto_techniques={"hidden_single"}, auto_solve=True)
    wrong.board[0][8] = 1
    assert wrong.auto_solve_enabled() == 0

    assert calls == []


def test_game_takes_owned_envelope_and_remembers_once(monkeypatch):
    game = Game(AUTO_NOTES_PUZZLE, auto_techniques={"hidden_single"}, auto_solve=True)
    result_board = deepcopy(game.board)
    result_board[0][8] = 9
    result_notes = {(1, 0): {1, 2}}
    result = AutoSolveResult(result_board, result_notes, 1, ((0, 0, 1),))
    monkeypatch.setattr("shudu.sudoku_game.solve_auto", lambda *args: result)

    assert game.auto_solve_enabled(remember=True) == 1
    assert game.board is result_board
    assert game.notes is result_notes
    assert game.simple_eliminations == {(0, 0, 1)}
    assert len(game.history) == 1


def test_game_full_envelope_noop_does_not_remember_or_update_status(monkeypatch):
    game = Game(AUTO_NOTES_PUZZLE, auto_techniques={"hidden_single"}, auto_solve=True)
    game.notes = {(1, 0): {1, 2}}
    game.simple_eliminations = {(1, 1, 2)}
    before = _snapshot(game)
    result = AutoSolveResult(deepcopy(game.board), deepcopy(game.notes), 0, ())
    monkeypatch.setattr("shudu.sudoku_game.solve_auto", lambda *args: result)
    monkeypatch.setattr(game, "_remember", lambda: pytest.fail("full no-op must not remember"))
    monkeypatch.setattr(game, "_check_finished", lambda: pytest.fail("full no-op must not check completion"))

    assert game.auto_solve_enabled(remember=True) == 0
    assert _snapshot(game) == before


def test_game_notes_only_result_still_applies_and_keeps_original_state_updates(monkeypatch):
    game = Game(AUTO_NOTES_PUZZLE, auto_techniques={"hidden_single"}, auto_solve=True)
    game.selected = (1, 0)
    game.active_digit = 4
    game.message = "原消息"
    result = AutoSolveResult(deepcopy(game.board), {(1, 0): {1, 2}}, 0, ())
    monkeypatch.setattr("shudu.sudoku_game.solve_auto", lambda *args: result)

    assert game.auto_solve_enabled(remember=True) == 0
    assert game.notes is result.notes
    assert len(game.history) == 1
    assert game.active_digit == 0
    assert "固定点" in game.message
    assert game.status == "playing"


@pytest.mark.parametrize("seam", ("solver", "finder", "diff", "final_notes"))
def test_game_keeps_full_snapshot_when_auto_capability_raises(monkeypatch, seam):
    game = Game(AUTO_NOTES_PUZZLE, auto_techniques={"hidden_single"}, auto_solve=True)
    game.notes = {(1, 0): {1, 2}}
    game.simple_eliminations = {(1, 1, 2)}
    game.active_digit = 4
    game.message = "原消息"
    before = _snapshot(game)

    if seam == "solver":
        def raise_solver(*args, **kwargs):
            raise RuntimeError(seam)

        monkeypatch.setattr("shudu.logic_solver._auto.ShuduSolver", raise_solver)
    elif seam == "finder":
        def raise_finder(*args, **kwargs):
            raise RuntimeError(seam)

        monkeypatch.setattr(ShuduSolver, "hidden_single", raise_finder)
    elif seam == "diff":
        def raise_diff(*args, **kwargs):
            raise RuntimeError(seam)

        monkeypatch.setattr("shudu.logic_solver._project.diff_changes", raise_diff)
    else:
        def raise_final_notes(*args, **kwargs):
            raise RuntimeError(seam)

        monkeypatch.setattr(ShuduSolver, "algorithm_candidates", raise_final_notes)

    with pytest.raises(RuntimeError, match=seam):
        game.auto_solve_enabled(remember=True)

    assert _snapshot(game) == before
