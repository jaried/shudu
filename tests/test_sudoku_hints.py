"""验证只读提示和自动笔记不改变玩家盘面。"""

from copy import deepcopy

import pytest

from logical_solver import LogicSolver, parse
from test_logical_solver import SECOND_PUZZLE
from sudoku_puzzles import Puzzle
from sudoku_game import CELLS, PEERS, Game
from sudoku_hints import make_hint, pending_step
from sudoku_puzzles import PUZZLES


def play_state(game):
    result = (deepcopy(game.board), deepcopy(game.notes), game.selected,
              game.notes_mode, deepcopy(game.history), game.mistakes)
    return result


def elimination_board():
    solver = LogicSolver(parse(SECOND_PUZZLE))
    result = None
    for _ in range(81):
        before_board = deepcopy(solver.board)
        before_cands = deepcopy(solver.cands)
        if not solver._apply_next_step():
            break
        if solver.board == before_board and solver.cands != before_cands:
            result = before_board
            break
    return result


def elimination_game():
    board = elimination_board()
    rows = tuple("".join(str(value) for value in row) for row in board)
    result = Game(Puzzle("逻辑排除", "测试", rows))
    result.auto_notes()
    return result


def test_hint_round_trip_preserves_all_play_data():
    game = Game()
    game.auto_notes()
    before = play_state(game)
    game.hint()
    assert play_state(game) == before
    assert game.status == "hint" and game.hints_used == 1
    game.close_hint()
    assert play_state(game) == before and game.status == "playing"


def test_hint_uses_existing_solver_priority_without_placing_value():
    game = Game()
    legacy = LogicSolver(game.board)
    assert legacy._apply_next_step()
    expected = legacy.board
    game.hint()
    step = game.hint_preview.step
    assert step is not None and step.placements
    r, c, digit = step.placements[0]
    assert expected[r][c] == digit and game.value((r, c)) == 0


def test_reopening_without_manual_action_repeats_same_step():
    game = Game()
    game.hint()
    first = game.hint_preview
    game.close_hint()
    game.hint()
    assert game.hint_preview == first and not game.history


def test_hint_never_calls_full_solver_or_backtracking(monkeypatch):
    game = Game()
    def forbidden(*args, **kwargs):
        raise AssertionError("只读提示不得全盘求解或回溯")
    monkeypatch.setattr(LogicSolver, "solve", forbidden)
    monkeypatch.setattr(LogicSolver, "_try_backtracking_fallback", forbidden)
    monkeypatch.setattr("sudoku_backtracking.DEFAULT_BACKTRACKING_SOLVER.solve", forbidden)
    game.hint()
    assert game.hint_preview.step is not None


def test_stalled_logic_returns_explanation_without_guessing():
    board = [[0] * 9 for _ in range(9)]
    result = make_hint(board, {}, set())
    assert result.step is None and result.title == "暂无逻辑提示"
    assert not any(any(row) for row in board)


def test_wrong_board_returns_warning_without_logic_step():
    game = Game()
    game.select(0, 0)
    game.enter(2)
    game.hint()
    assert game.hint_preview.step is None
    assert game.hint_preview.attention == {(0, 0)}


def test_auto_notes_covers_every_empty_cell_with_legal_candidates():
    game = Game()
    game.auto_notes()
    assert len(game.notes) == 57 and game.notes_mode
    for cell in CELLS:
        expected = set(range(1, 10)) - {game.value(peer) for peer in PEERS[cell]}
        assert game.notes.get(cell) == (expected if not game.value(cell) else None)


def test_auto_notes_only_writes_small_numbers_even_for_single_candidate():
    game = Game(PUZZLES[1])
    before = deepcopy(game.board)
    game.auto_notes()
    assert game.board == before and any(len(notes) == 1 for notes in game.notes.values())


def test_auto_notes_recalculates_and_is_one_step_undoable():
    game = Game()
    game.notes = {(0, 0): {1, 9}, (0, 1): {4}}
    before = deepcopy(game.notes)
    game.auto_notes()
    game.auto_notes()
    assert len(game.history) == 1
    game.undo()
    assert game.notes == before


def test_auto_notes_honors_correct_player_numbers():
    game = Game()
    game.select(0, 0)
    game.enter(8)
    game.auto_notes()
    assert (0, 0) not in game.notes
    assert all(8 not in game.notes.get(peer, ()) for peer in PEERS[(0, 0)])


def test_auto_notes_refuses_erroneous_board_without_mutation():
    game = Game()
    game.auto_notes()
    game.toggle_notes()
    game.select(0, 0)
    game.enter(2)
    before = play_state(game)
    game.auto_notes()
    assert play_state(game) == before and "修正" in game.message


@pytest.mark.parametrize("status", ["paused", "hint", "won", "blocked"])
def test_auto_notes_and_hint_are_disabled_outside_playing(status):
    game = Game()
    game.status = status
    before = play_state(game)
    game.auto_notes()
    game.hint()
    assert play_state(game) == before and game.hints_used == 0


def test_pending_step_does_not_mutate_input_board():
    board = Game().board
    before = deepcopy(board)
    assert pending_step(board, {}) is not None
    assert board == before


def test_hint_message_keeps_existing_technique_name():
    board = parse("""
6...89..4
.........
23...5..9
..34..5..
.....1.4.
4.8.53.27
.5.72....
3..51.472
7.2...6..
""")
    step = pending_step(board, {})
    assert step is not None and ":" in step.message
