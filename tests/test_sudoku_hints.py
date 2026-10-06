"""验证只读提示和自动笔记不改变玩家盘面。"""

from copy import deepcopy

import pytest
from sudoku_game import CELLS, PEERS, Game
from sudoku_hint_view import hint_background
from sudoku_hints import make_hint, pending_step
from sudoku_puzzles import PUZZLES, Puzzle, puzzle_from_text
from sudoku_rules import candidate_grid
from sudoku_theme import SAME
from test_logical_solver import SECOND_PUZZLE

from logical_solver import LogicSolver, parse
from shudu_solver import AUTO_TECHNIQUE_NAMES, DEFAULT_AUTO_TECHNIQUES, ShuduSolver

LEVEL119_PUZZLE = Puzzle(
    "关卡 119",
    "回归",
    (
        "7183..459",
        "6924..738",
        "453879126",
        "2...3.9..",
        "...6...7.",
        "5......82",
        ".....7.4.",
        "146583297",
        "........3",
    ),
)


SCREENSHOT_NOTES = {
    (0, 4): {2, 6}, (0, 5): {2, 6}, (1, 4): {1, 5}, (1, 5): {1, 5},
    (3, 1): {6, 7, 8}, (3, 2): {1, 4, 7}, (3, 3): {1, 7},
    (3, 5): {1, 4, 5, 8}, (3, 7): {1, 6}, (3, 8): {1, 4, 5},
    (4, 0): {3, 8, 9}, (4, 1): {3, 8}, (4, 2): {1, 4, 9},
    (4, 4): {1, 2, 5, 9}, (4, 5): {1, 2, 4, 5, 8},
    (4, 6): {3, 5}, (4, 8): {1, 4, 5},
    (5, 1): {3, 6}, (5, 2): {1, 4, 7, 9}, (5, 3): {1, 7, 9},
    (5, 4): {1, 4, 9}, (5, 5): {1, 4}, (5, 6): {3, 6},
    (6, 0): {3, 8, 9}, (6, 1): {2, 3, 8}, (6, 2): {5, 9},
    (6, 3): {1, 2, 9}, (6, 4): {1, 6, 9}, (6, 6): {5, 6, 8}, (6, 8): {1, 5},
    (8, 0): {8, 9}, (8, 1): {2, 7, 8}, (8, 2): {5, 7, 9},
    (8, 3): {1, 2, 9}, (8, 4): {1, 4, 6, 9}, (8, 5): {1, 4, 6},
    (8, 6): {5, 6, 8}, (8, 7): {1, 6},
}


@pytest.mark.parametrize(
    "auto_techniques",
    (frozenset(), DEFAULT_AUTO_TECHNIQUES, {"hidden_pair"}, AUTO_TECHNIQUE_NAMES),
)
def test_screenshot_hint_finds_hidden_triple_from_current_notes(auto_techniques):
    game = Game(LEVEL119_PUZZLE, auto_techniques=auto_techniques)
    game.notes = deepcopy(SCREENSHOT_NOTES)
    before = play_state(game)
    game.hint()
    hint = game.hint_preview
    assert hint.step is not None and hint.step.name == "Hidden Triple"
    assert hint.title == "隐性三数组"
    assert hint.pending_eliminations == (
        (3, 5, 1), (3, 5, 4), (4, 4, 1), (4, 4, 9), (4, 5, 1), (4, 5, 4),
    )
    assert hint.sources == {(3, 5), (4, 4), (4, 5)}
    assert len(hint.units) == 1 and set(hint.units[0]) == {
        (row, col) for row in range(3, 6) for col in range(3, 6)
    }
    assert all(hint_background(hint, cell, 0) == SAME for cell in hint.sources)
    assert "[2, 5, 8]" in hint.message and "绿色三格" in hint.message
    assert play_state(game) == before


def test_hidden_triple_uses_public_solver_step_and_does_not_repeat_removed_notes():
    notes = deepcopy(SCREENSHOT_NOTES)
    first = pending_step(LEVEL119_PUZZLE.grid(), notes)
    assert first is not None and first.name == "Hidden Triple"
    solver = ShuduSolver(LEVEL119_PUZZLE.grid())
    base = solver.algorithm_candidates()
    solver.apply_candidate_eliminations(
        (row, col, digit)
        for (row, col), values in notes.items()
        for digit in base[row][col] - values
    )
    assert solver.apply_technique_step({"hidden_triple"})
    assert solver.algorithm_candidates()[3][5] == {5, 8}
    assert solver.algorithm_candidates()[4][4] == {2, 5}
    assert solver.algorithm_candidates()[4][5] == {2, 5, 8}
    followup = solver.next_step()
    assert followup is not None and followup.name == "Hidden Pair"
    assert set(first.eliminations).isdisjoint(followup.eliminations)
    for row, col, digit in first.eliminations:
        notes[(row, col)].remove(digit)
    second = pending_step(LEVEL119_PUZZLE.grid(), notes)
    assert second is not None and second.name == "Hidden Pair"
    assert second == followup
    assert set(first.eliminations).isdisjoint(second.eliminations)



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


@pytest.mark.parametrize(
    "auto_techniques",
    (frozenset(), DEFAULT_AUTO_TECHNIQUES),
)
def test_level119_hint_uses_hidden_pair_from_existing_notes_even_when_auto_disabled(auto_techniques):
    game = Game(LEVEL119_PUZZLE, auto_techniques=auto_techniques)
    game.notes = {
        (5, 1): {3, 6, 7},
        (5, 6): {3, 6},
    }
    game.notes_mode = True
    assert "hidden_pair" not in game.auto_techniques
    game.hint()
    hint = game.hint_preview
    assert hint.step is not None and hint.step.name == "Hidden Pair"
    assert hint.pending_eliminations == ((5, 1, 7),)


def test_level119_existing_note_without_7_does_not_repeat_hidden_pair_deletion():
    game = Game(LEVEL119_PUZZLE, auto_techniques=set())
    game.notes = {(5, 1): {3, 6}}
    game.notes_mode = True
    game.hint()
    hint = game.hint_preview
    assert hint.step is None or (5, 1, 7) not in hint.step.eliminations


def test_existing_notes_are_projected_per_cell(monkeypatch):
    board = LEVEL119_PUZZLE.grid()
    base = candidate_grid(board)
    captured = {}
    original = ShuduSolver.next_step

    def tracked(solver):
        captured["candidates"] = solver.algorithm_candidates()
        result = original(solver)
        return result

    monkeypatch.setattr(ShuduSolver, "next_step", tracked)
    pending_step(board, {(5, 1): {3, 6}})
    candidates = captured["candidates"]
    assert candidates[5][1] == {3, 6}
    assert candidates[3][1] == set(base[3][1])


def test_hint_is_identical_for_same_board_and_notes_regardless_of_auto_setting():
    notes = {
        (5, 1): {3, 6, 7},
        (5, 6): {3, 6},
    }
    disabled = Game(LEVEL119_PUZZLE, auto_techniques=set())
    enabled = Game(LEVEL119_PUZZLE, auto_techniques={"hidden_pair"})
    disabled.notes = {cell: set(values) for cell, values in notes.items()}
    enabled.notes = {cell: set(values) for cell, values in notes.items()}
    disabled.hint()
    enabled.hint()
    assert disabled.hint_preview == enabled.hint_preview


def test_hint_requests_one_all_algorithm_step_with_existing_notes(monkeypatch):
    game = Game(LEVEL119_PUZZLE, auto_techniques=set())
    game.notes = {
        (5, 1): {3, 6, 7},
        (5, 6): {3, 6},
    }
    calls = []
    original = ShuduSolver.next_step

    def tracked(solver):
        calls.append(None)
        result = original(solver)
        return result

    monkeypatch.setattr(ShuduSolver, "next_step", tracked)
    game.hint()
    assert game.hint_preview.step is not None
    assert len(calls) == 1


def test_hidden_pair_keeps_both_source_cells_green():
    game = Game(LEVEL119_PUZZLE, auto_techniques=set())
    game.notes = {
        (5, 1): {3, 6, 7},
        (5, 6): {3, 6},
    }
    game.hint()
    hint = game.hint_preview
    assert hint.step is not None and hint.step.name == "Hidden Pair"
    assert len(hint.sources) == 2
    assert all(hint_background(hint, cell, 0) == SAME for cell in hint.sources)

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


def test_naked_pair_marks_both_source_cells():
    solver = LogicSolver(Game().board)
    pair_board = None
    for _ in range(81):
        before = deepcopy(solver.board)
        assert solver._apply_next_step()
        if "Naked Pair:" in solver.steps[-1]:
            pair_board = before
            break
    hint = make_hint(pair_board, {}, set())
    assert hint.step is not None and hint.step.name == "Naked Pair"
    assert len(hint.sources) == 2
    assert all(hint.step.candidates[r][c] == hint.step.candidates[next(iter(hint.sources))[0]][next(iter(hint.sources))[1]]
               for r, c in hint.sources)


def test_custom_puzzle_text_accepts_dots_zeroes_and_spacing():
    puzzle = puzzle_from_text("""
        . . . . 9 . 6 . 7
        0 0 0 0 0 0 0 1 0
        9 . 7 . 2 . 5 3 .
        4 . . . 5 . . . .
        . . . . . 8 . . .
        1 3 . . 4 . 7 9 .
        6 . 8 9 . . . . .
        . 1 . 5 . . . . 2
        . . . . . . . 5 .
    """)
    game = Game(puzzle)
    assert game.givens[0][4] == 9 and game.givens[1][7] == 1
    assert game.puzzle.title == "自定义局"
