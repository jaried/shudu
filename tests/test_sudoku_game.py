"""验证数独游戏的确定性状态转换。
使用真实公共求解器，不替换数独规则。
覆盖截图题面、笔记、错误、撤销和计时边界。
测试不依赖窗口、网络或用户文件。
"""

import pytest

from sudoku_backtracking import DEFAULT_BACKTRACKING_SOLVER
from sudoku_game import Game, solve_puzzle
from sudoku_puzzles import PUZZLES, Puzzle, SCREENSHOT_PUZZLE
from sudoku_rules import CELLS, PEERS, related


@pytest.fixture
def game():
    result = Game()
    return result


def put(game, cell, digit):
    game.select(*cell)
    game.enter(digit)


def note(game, cell, *digits):
    game.select(*cell)
    if not game.notes_mode:
        game.toggle_notes()
    for digit in digits:
        game.enter(digit)


def test_givens_are_transcribed_from_screenshot():
    assert game_givens() == SCREENSHOT_PUZZLE.grid()


def game_givens():
    return [list(row) for row in Game().givens]


def test_solution_uses_public_solver_and_matches_all_givens(monkeypatch):
    puzzle = PUZZLES[1]
    calls = []
    original = DEFAULT_BACKTRACKING_SOLVER.solve

    def tracked(board):
        calls.append(board)
        return original(board)

    solve_puzzle.cache_clear()
    monkeypatch.setattr(DEFAULT_BACKTRACKING_SOLVER, "solve", tracked)
    current = Game(puzzle)
    assert calls
    assert all(
        not current.givens[row][col] or current.solution[row][col] == current.givens[row][col]
        for row, col in CELLS
    )
    solve_puzzle.cache_clear()


def test_given_cell_cannot_be_edited(game):
    given = next(cell for cell in CELLS if game.given(cell))
    before = game.value(given)
    game.select(*given)
    game.enter(1 if before != 1 else 2)
    assert game.value(given) == before
    assert not game.history


def test_correct_digit_is_accepted_without_error(game):
    cell = (0, 0)
    put(game, cell, game.solution[0][0])
    assert game.value(cell) == game.solution[0][0]
    assert game.mistakes == 0


def test_wrong_digit_marks_error_and_counts_once_for_same_value(game):
    cell = (0, 0)
    wrong = next(digit for digit in range(1, 10) if digit != game.solution[0][0])
    put(game, cell, wrong)
    put(game, cell, wrong)
    assert game.value(cell) == wrong
    assert game.mistakes == 1
    assert cell in game.wrong_cells()


def test_changing_wrong_value_counts_another_error(game):
    cell = (0, 0)
    wrong = [digit for digit in range(1, 10) if digit != game.solution[0][0]][:2]
    put(game, cell, wrong[0])
    put(game, cell, wrong[1])
    assert game.mistakes == 2


def test_errors_do_not_end_game(game):
    cell = (0, 0)
    wrong = [digit for digit in range(1, 10) if digit != game.solution[0][0]]
    for digit in wrong:
        put(game, cell, digit)
    assert game.status == "playing"
    assert game.mistakes == len(wrong)


def test_erase_does_not_reduce_error_count(game):
    cell = (0, 0)
    wrong = next(digit for digit in range(1, 10) if digit != game.solution[0][0])
    put(game, cell, wrong)
    game.erase()
    assert game.value(cell) == 0
    assert game.mistakes == 1


def test_undo_restores_board_but_not_error_count(game):
    cell = (0, 0)
    wrong = next(digit for digit in range(1, 10) if digit != game.solution[0][0])
    put(game, cell, wrong)
    game.undo()
    assert game.value(cell) == 0
    assert game.mistakes == 1


def test_notes_toggle_without_counting_error(game):
    game.select(0, 0)
    game.toggle_notes()
    game.enter(1)
    game.enter(3)
    assert game.notes[(0, 0)] == {1, 3}
    assert game.value((0, 0)) == 0
    assert game.mistakes == 0
    game.enter(1)
    assert game.notes[(0, 0)] == {3}


def test_formal_entry_clears_current_notes(game):
    cell = (0, 0)
    note(game, cell, 1, 2)
    game.toggle_notes()
    put(game, cell, game.solution[0][0])
    assert cell not in game.notes


def test_auto_clean_removes_peer_note_for_correct_entry(game):
    source = (0, 0)
    digit = game.solution[0][0]
    peer = next(cell for cell in PEERS[source] if not game.given(cell))
    note(game, peer, digit)
    game.toggle_notes()
    put(game, source, digit)
    assert digit not in game.notes.get(peer, set())


def test_auto_clean_can_be_disabled(game):
    source = (0, 0)
    digit = game.solution[0][0]
    peer = next(cell for cell in PEERS[source] if not game.given(cell))
    note(game, peer, digit)
    game.toggle_notes()
    game.auto_clean = False
    put(game, source, digit)
    assert digit in game.notes.get(peer, set())


def test_undo_restores_notes_removed_by_correct_entry(game):
    source = (0, 0)
    digit = game.solution[0][0]
    peer = next(cell for cell in PEERS[source] if not game.given(cell))
    note(game, peer, digit)
    game.toggle_notes()
    before = {cell: set(values) for cell, values in game.notes.items()}
    put(game, source, digit)
    game.undo()
    assert game.value(source) == 0
    assert game.notes == before


def test_erase_removes_entire_note_cell(game):
    cell = (0, 0)
    note(game, cell, 1, 2, 3)
    game.erase()
    assert cell not in game.notes


def test_completed_digit_blocks_formal_input_but_not_notes(game):
    digit = 1
    for row, col in CELLS:
        if game.solution[row][col] == digit and not game.given((row, col)):
            put(game, (row, col), digit)
    assert game.completed_digit(digit)
    empty = next(cell for cell in CELLS if not game.value(cell) and not game.given(cell))
    game.select(*empty)
    game.enter(digit)
    assert game.value(empty) == 0
    game.toggle_notes()
    game.enter(digit)
    assert digit in game.notes[empty]


def test_conflict_cells_include_both_duplicate_values(game):
    first = (0, 0)
    second = next(cell for cell in PEERS[first] if not game.given(cell))
    digit = next(
        value
        for value in range(1, 10)
        if value != game.solution[first[0]][first[1]]
        and value != game.solution[second[0]][second[1]]
    )
    put(game, first, digit)
    put(game, second, digit)
    assert first in game.conflict_cells()
    assert second in game.conflict_cells()


def test_related_matches_peer_topology():
    for cell in CELLS:
        for other in CELLS:
            if cell == other:
                continue
            assert (other in PEERS[cell]) == related(cell, other)


def test_move_wraps_board_edges(game):
    game.select(0, 0)
    game.move(-1, 0)
    assert game.selected == (8, 0)
    game.move(0, -1)
    assert game.selected == (8, 8)


def test_elapsed_only_runs_while_playing():
    times = iter((10.0, 15.8, 19.2, 24.0, 30.0))
    game = Game(clock=lambda: next(times))
    assert game.elapsed == 5
    game.toggle_pause()
    assert game.elapsed == 9
    game.toggle_pause()
    assert game.elapsed == 14


def test_hint_pauses_timer_and_close_resumes():
    times = iter((10.0, 15.0, 20.0, 27.0, 35.0))
    game = Game(clock=lambda: next(times))
    game.hint()
    assert game.status == "hint"
    assert game.elapsed == 10
    game.close_hint()
    assert game.elapsed == 17


def test_winning_stops_timer():
    times = iter((10.0, 20.0, 30.0, 40.0))
    game = Game(clock=lambda: next(times))
    game.board = [list(row) for row in game.solution]
    game._check_finished()
    assert game.status == "won"
    assert game.elapsed == 10


def test_select_given_message(game):
    given = next(cell for cell in CELLS if game.given(cell))
    game.select(*given)
    assert "题目已知数" in game.message


def test_select_empty_message(game):
    empty = next(cell for cell in CELLS if not game.given(cell))
    game.select(*empty)
    assert "题目已知数" not in game.message


def test_invalid_digit_rejected(game):
    for digit in (0, 10, -1, True, 1.0, "1"):
        with pytest.raises(ValueError):
            game.enter(digit)


def test_custom_invalid_puzzle_rejected():
    puzzle = Puzzle("坏题", "测试", ("11.......",) + (".........",) * 8)
    solve_puzzle.cache_clear()
    with pytest.raises(ValueError, match="重复"):
        Game(puzzle)


def test_cached_solution_reuses_result(monkeypatch):
    puzzle = PUZZLES[2]
    solve_puzzle.cache_clear()
    calls = []
    original = DEFAULT_BACKTRACKING_SOLVER.solve

    def tracked(board):
        calls.append(board)
        return original(board)

    monkeypatch.setattr(DEFAULT_BACKTRACKING_SOLVER, "solve", tracked)
    first = Game(puzzle)
    second = Game(puzzle)
    assert first.solution == second.solution
    assert len(calls) == 1
    solve_puzzle.cache_clear()
