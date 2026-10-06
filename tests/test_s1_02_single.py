"""S1-02 单步 capability 的公开 Interface 回归。"""

from copy import deepcopy

import pytest
from test_sudoku_hints import LEVEL119_PUZZLE, SCREENSHOT_NOTES

from shudu.logic_solver import LogicStep, ShuduSolver, next_hint_step
from shudu.sudoku_game import Game


def test_next_hint_step_returns_hidden_single_and_keeps_inputs_read_only():
    board = Game().board
    notes = {}
    board_before = deepcopy(board)
    notes_before = deepcopy(notes)

    step = next_hint_step(board, notes)

    assert step is not None
    assert step.name == "Hidden Single"
    assert step.technique_name == "Hidden Single"
    assert step.placements
    assert board == board_before
    assert notes == notes_before


def test_next_hint_step_projects_existing_notes_into_hidden_triple():
    board = LEVEL119_PUZZLE.grid()
    notes = deepcopy(SCREENSHOT_NOTES)

    step = next_hint_step(board, notes)

    assert step is not None
    assert step.technique_name == "Hidden Triple"
    assert step.name == "Hidden Triple"
    assert step.eliminations == (
        (3, 5, 1),
        (3, 5, 4),
        (4, 4, 1),
        (4, 4, 9),
        (4, 5, 1),
        (4, 5, 4),
    )


def test_next_hint_step_returns_none_for_stalled_board():
    board = [[0] * 9 for _ in range(9)]

    assert next_hint_step(board, {}) is None
    assert board == [[0] * 9 for _ in range(9)]


def test_next_hint_step_calls_one_project_step(monkeypatch):
    calls = []
    original = ShuduSolver.next_step

    def tracked(solver):
        calls.append(1)
        return original(solver)

    monkeypatch.setattr(ShuduSolver, "next_step", tracked)

    next_hint_step(Game().board, {})

    assert calls == [1]


def test_logic_step_keeps_six_positional_fields_and_optional_identity():
    step = LogicStep("Hidden Single: test", (), (), (), (), ())

    assert step.name == "Hidden Single"
    assert step.technique_name is None


def test_next_step_exception_does_not_poison_following_call(monkeypatch):
    solver = ShuduSolver(Game().board)
    original = solver._apply_next_step

    def raise_once():
        monkeypatch.setattr(solver, "_apply_next_step", original)
        raise RuntimeError("probe exception")

    monkeypatch.setattr(solver, "_apply_next_step", raise_once)

    with pytest.raises(RuntimeError, match="probe exception"):
        solver.next_step()

    step = solver.next_step()
    assert step is not None
    assert step.technique_name == "Hidden Single"
