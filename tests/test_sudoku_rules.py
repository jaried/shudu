"""验证共享数独规则不会与旧求解器或游戏候选发生漂移。"""

from logical_solver import init_candidates
from sudoku_game import Game
from sudoku_rules import BOXES, CELLS, COLS, PEERS, ROWS, UNITS, candidate_grid, related


def test_topology_has_expected_shape_and_peer_count():
    assert len(CELLS) == 81
    assert len(ROWS) == 9 and len(COLS) == 9 and len(BOXES) == 9
    assert len(UNITS) == 27
    assert all(len(unit) == 9 for unit in UNITS)
    assert all(len(PEERS[cell]) == 20 for cell in CELLS)


def test_related_is_symmetric_and_matches_peers():
    for cell in CELLS:
        for other in CELLS:
            assert related(cell, other) == related(other, cell)
            if cell != other:
                assert (other in PEERS[cell]) == related(cell, other)


def test_shared_candidates_match_legacy_solver_candidates():
    board = Game().board
    assert candidate_grid(board) == init_candidates(board)


def test_candidate_grid_does_not_mutate_board():
    game = Game()
    before = [row[:] for row in game.board]
    candidate_grid(game.board)
    assert game.board == before


def test_filled_cells_have_no_candidates():
    game = Game()
    candidates = candidate_grid(game.board)
    for row, col in CELLS:
        if game.value((row, col)):
            assert candidates[row][col] == set()
