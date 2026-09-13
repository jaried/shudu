"""验证数独游戏的确定性状态转换。
使用真实公共求解器，不替换数独规则。
覆盖截图题面、笔记、错误、撤销和计时边界。
测试不依赖窗口、网络或用户文件。
"""

import pytest

from sudoku_backtracking import DEFAULT_BACKTRACKING_SOLVER
from sudoku_game import CELLS, PEERS, Game, related, solve_puzzle
from sudoku_puzzles import PUZZLES, Puzzle, SCREENSHOT_PUZZLE


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
    game.toggle_notes()


def test_screenshot_board_has_exactly_24_givens(game):
    assert sum(bool(value) for row in game.givens for value in row) == 24
    assert SCREENSHOT_PUZZLE.rows == (
        "....9.6.7", ".......1.", "9.7.2.53.",
        "4...5....", ".....8...", "13..4.79.",
        "6.89.....", ".1.5....2", ".......5.",
    )
    assert game.selected == (1, 3)


@pytest.mark.parametrize("puzzle", PUZZLES)
def test_builtin_solution_obeys_all_constraints(puzzle):
    original = puzzle.grid()
    solution = solve_puzzle(puzzle)
    assert DEFAULT_BACKTRACKING_SOLVER.validate(solution) is None
    assert all(set(row) == set(range(1, 10)) for row in solution)
    assert all(not original[r][c] or original[r][c] == solution[r][c] for r, c in CELLS)
    assert puzzle.grid() == original


def _has_alternative(puzzle, solution):
    board = puzzle.grid()
    found = False
    for row, col in CELLS:
        if not board[row][col] and _alternative_at(board, solution, row, col):
            found = True
            break
    return found


def _alternative_at(board, solution, row, col):
    found = False
    for digit in range(1, 10):
        if digit != solution[row][col]:
            board[row][col] = digit
            found = DEFAULT_BACKTRACKING_SOLVER.solve(board).solved
            if found:
                break
    board[row][col] = 0
    return found


@pytest.mark.parametrize("puzzle", PUZZLES)
def test_builtin_puzzle_has_unique_solution(puzzle):
    # 任意另一解至少有一格与已知解不同；逐格强制其他数字检查有无解。
    assert not _has_alternative(puzzle, solve_puzzle(puzzle))


def test_solution_comes_from_shared_solver(monkeypatch):
    original = DEFAULT_BACKTRACKING_SOLVER.solve
    calls = []
    def tracked(board):
        calls.append(board)
        result = original(board)
        return result
    monkeypatch.setattr(DEFAULT_BACKTRACKING_SOLVER, "solve", tracked)
    puzzle = Puzzle("复用验证", "测试", SCREENSHOT_PUZZLE.rows)
    assert Game(puzzle).solution == solve_puzzle(SCREENSHOT_PUZZLE)
    assert len(calls) == 1


@pytest.mark.parametrize("rows", [(".........",)*8, ("........",)*9, ("..........",)*9, ("........x",)*9, ("........９",)*9])
def test_rejects_malformed_puzzle(rows):
    with pytest.raises(ValueError):
        Game(Puzzle("非法题面", "测试", rows))


def test_rejects_duplicate_clues():
    with pytest.raises(ValueError, match="重复"):
        Game(Puzzle("冲突", "测试", ("11.......",) + (".........",)*8))


def test_rejects_unsolvable_puzzle_without_duplicate_clues():
    rows = ("2...9.6.7",) + SCREENSHOT_PUZZLE.rows[1:]
    assert DEFAULT_BACKTRACKING_SOLVER.validate(Puzzle("无解", "测试", rows).grid()) is None
    with pytest.raises(ValueError, match="无解"):
        Game(Puzzle("无解", "测试", rows))


def test_peers_are_exactly_20_distinct_cells():
    assert all(len(PEERS[cell]) == 20 and cell not in PEERS[cell] for cell in CELLS)
    assert related((0, 0), (2, 2))
    assert not related((0, 0), (4, 4))


def test_givens_are_immutable(game):
    put(game, (0, 4), 1)
    game.erase()
    game.toggle_notes()
    game.enter(2)
    assert game.value((0, 4)) == 9
    assert not game.notes and not game.history
    assert game.mistakes == 0


def test_selection_and_arrow_wrapping(game):
    game.select(0, 0)
    game.move(-1, -1)
    assert game.selected == (8, 8)
    game.select(9, -1)
    assert game.selected == (8, 8)


def test_notes_toggle_independently_without_errors(game):
    game.select(0, 0)
    game.toggle_notes()
    for digit in (1, 4, 9, 4):
        game.enter(digit)
    assert game.notes[(0, 0)] == {1, 9}
    assert game.value((0, 0)) == 0
    assert game.mistakes == 0
    game.enter(1)
    game.enter(9)
    assert (0, 0) not in game.notes


def test_note_on_filled_cell_does_not_overwrite_number(game):
    put(game, (0, 0), 8)
    game.toggle_notes()
    game.enter(4)
    assert game.value((0, 0)) == 8
    assert not game.notes
    assert len(game.history) == 1


def test_correct_entry_cleans_only_peer_notes_and_undo_restores_them(game):
    note(game, (0, 0), 1, 8)
    note(game, (0, 1), 4, 8)
    note(game, (8, 8), 8)
    put(game, (0, 0), 8)
    assert (0, 0) not in game.notes
    assert game.notes[(0, 1)] == {4}
    assert game.notes[(8, 8)] == {8}
    game.undo()
    assert game.notes == {(0, 0): {1, 8}, (0, 1): {4, 8}, (8, 8): {8}}
    assert game.value((0, 0)) == 0


def test_wrong_input_keeps_peers_notes_and_matches_screenshot(game):
    note(game, (4, 6), 8)
    put(game, (4, 7), 8)
    assert game.notes[(4, 6)] == {8}
    assert game.mistakes == 1
    assert game.wrong_cells() == {(4, 7)}
    assert game.conflict_cells() == {(4, 5), (4, 7)}
    assert (6, 2) not in game.conflict_cells()


def test_wrong_value_without_local_duplicate_is_still_marked_wrong(game):
    put(game, (0, 0), 2)
    assert game.mistakes == 1
    assert game.wrong_cells() == {(0, 0)}
    assert game.conflict_cells() == set()


def test_repeated_same_error_is_not_counted_twice(game):
    put(game, (4, 7), 8)
    game.enter(8)
    assert game.mistakes == 1
    assert len(game.history) == 1


def test_erase_and_undo_never_refund_mistakes(game):
    put(game, (4, 7), 8)
    game.erase()
    game.undo()
    assert game.value((4, 7)) == 8 and game.mistakes == 1
    game.undo()
    assert game.value((4, 7)) == 0 and game.mistakes == 1
    game.undo()
    assert game.mistakes == 1


def test_third_error_locks_game(game):
    game.select(4, 7)
    for digit in (8, 9, 1):
        game.enter(digit)
    assert game.status == "lost" and game.mistakes == 3
    before = game.board[4][7]
    game.erase()
    game.undo()
    game.hint()
    game.enter(4)
    assert game.value((4, 7)) == before and game.mistakes == 3


def test_turning_off_auto_clean_keeps_manual_notes(game):
    note(game, (0, 1), 8)
    game.auto_clean = False
    put(game, (0, 0), 8)
    assert game.notes[(0, 1)] == {8}


def test_erase_notes_is_undoable_without_mutable_snapshot_aliasing(game):
    note(game, (0, 0), 1, 4)
    game.erase()
    assert not game.notes
    game.undo()
    assert game.notes[(0, 0)] == {1, 4}
    game.undo()
    assert game.notes[(0, 0)] == {1}


def test_hint_corrects_error_using_original_puzzle(game):
    put(game, (4, 7), 8)
    game.hint()
    assert game.value((4, 7)) == 4
    assert game.mistakes == 1 and game.hints_used == 1
    assert not game.wrong_cells()
    game.undo()
    assert game.value((4, 7)) == 8
    assert game.hints_used == 1


def test_hint_fills_one_number_even_in_notes_mode(game):
    note(game, (0, 0), 1, 4)
    game.toggle_notes()
    game.hint()
    assert game.value((0, 0)) == 8 and game.notes_mode
    assert (0, 0) not in game.notes
    game.undo()
    assert game.notes[(0, 0)] == {1, 4}


def test_hint_on_given_selects_first_unfinished_cell(game):
    game.select(0, 4)
    game.hint()
    assert game.selected == (0, 0)
    assert game.value((0, 0)) == 8
    assert game.value((0, 4)) == 9


def test_pause_stops_clock_and_blocks_editing():
    now = [100.0]
    game = Game(clock=lambda: now[0])
    now[0] = 165.5
    game.toggle_pause()
    now[0] = 265.5
    game.enter(2)
    game.hint()
    game.toggle_notes()
    assert game.elapsed == 65 and game.time_text == "01:05"
    assert not game.history and not game.notes_mode


def test_resume_excludes_paused_time():
    now = [0.0]
    game = Game(clock=lambda: now[0])
    now[0] = 10.5
    game.toggle_pause()
    now[0] = 100.0
    game.toggle_pause()
    now[0] = 110.5
    assert game.elapsed == 21


def _complete_game(game):
    for row, col in CELLS:
        if not game.given((row, col)):
            put(game, (row, col), game.solution[row][col])


def test_completion_stops_clock_and_locks_inputs():
    now = [0.0]
    game = Game(clock=lambda: now[0])
    now[0] = 75.0
    _complete_game(game)
    assert game.status == "won" and game.elapsed == 75
    now[0] = 200.0
    game.erase()
    game.toggle_pause()
    assert game.elapsed == 75 and game.status == "won"
    assert not game.wrong_cells()


def test_completed_digit_ignores_wrong_copies(game):
    put(game, (4, 7), 8)
    assert not game.completed_digit(8)
    for cell in CELLS:
        if game.solution[cell[0]][cell[1]] == 8 and not game.given(cell):
            put(game, cell, 8)
    assert game.completed_digit(8)


@pytest.mark.parametrize("digit", [0, 10, -1, True, False, 1.5, "2", None])
def test_invalid_digit_is_rejected_without_mutating_state(game, digit):
    with pytest.raises(ValueError):
        game.enter(digit)
    assert not game.history and game.mistakes == 0


def test_completed_digit_cannot_be_entered_but_notes_remain_editable(game):
    for cell in CELLS:
        if game.solution[cell[0]][cell[1]] == 8 and not game.given(cell):
            put(game, cell, 8)
    put(game, (0, 2), 8)
    assert game.value((0, 2)) == 0 and game.mistakes == 0
    game.toggle_notes()
    game.enter(8)
    game.enter(8)
    assert (0, 2) not in game.notes
