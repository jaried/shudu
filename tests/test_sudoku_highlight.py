"""验证同值大数字的全局行列宫高亮。
使用真实游戏状态和独立坐标集合检查覆盖范围。
笔记不作为扩展高亮来源，空格只突出当前行列宫。
测试不依赖图形窗口，不修改游戏规则或答案。
"""

import pytest

from sudoku_game import CELLS, Game


@pytest.fixture
def game():
    result = Game()
    return result


def expected_region(anchors):
    rows = {row for row, col in anchors}
    cols = {col for row, col in anchors}
    boxes = {(row // 3, col // 3) for row, col in anchors}
    result = {cell for cell in CELLS if cell[0] in rows or cell[1] in cols or (cell[0] // 3, cell[1] // 3) in boxes}
    return result


@pytest.mark.parametrize("selected", [(1, 7), (2, 4), (2, 7), (5, 4), (3, 4), (0, 6), (0, 8), (4, 5), (0, 4)])
def test_each_digit_highlights_all_its_rows_columns_and_boxes(game, selected):
    game.select(*selected)
    anchors = {cell for cell in CELLS if game.value(cell) == game.value(selected)}
    assert game.highlighted_cells() == expected_region(anchors)


def test_selected_four_includes_remote_row_column_and_box_only_cells(game):
    game.select(5, 4)
    highlighted = game.highlighted_cells()
    assert {(3, 8), (8, 0), (4, 2)} <= highlighted
    assert (0, 8) not in highlighted
    assert highlighted == expected_region({(3, 0), (5, 4)})


def test_empty_cell_highlights_only_its_own_units(game):
    game.select(0, 0)
    assert game.highlighted_cells() == expected_region({(0, 0)})
    assert len(game.highlighted_cells()) == 21


def test_active_note_digit_does_not_expand_empty_cell_region(game):
    game.select(0, 0)
    game.toggle_notes()
    game.enter(4)
    assert game.active_digit == 4 and game.notes[(0, 0)] == {4}
    assert game.highlighted_cells() == expected_region({(0, 0)})


def test_note_cells_are_not_sources_when_selecting_a_large_digit(game):
    game.select(8, 8)
    game.toggle_notes()
    game.enter(4)
    game.select(5, 4)
    assert game.notes[(8, 8)] == {4} and game.notes_mode
    assert game.highlighted_cells() == expected_region({(3, 0), (5, 4)})
    assert (8, 8) not in game.highlighted_cells()


def test_player_entered_large_digit_is_included(game):
    game.select(0, 0)
    game.enter(8)
    game.select(4, 5)
    assert not game.given((0, 0)) and game.value((0, 0)) == 8
    assert game.highlighted_cells() == expected_region({(0, 0), (4, 5), (6, 2)})


def test_erase_removes_source_and_undo_restores_it(game):
    game.select(0, 0)
    game.enter(8)
    game.erase()
    game.select(4, 5)
    assert game.highlighted_cells() == expected_region({(4, 5), (6, 2)})
    game.undo()
    game.select(4, 5)
    assert game.highlighted_cells() == expected_region({(0, 0), (4, 5), (6, 2)})


def test_switch_to_empty_cell_clears_expanded_region(game):
    game.select(5, 4)
    assert (8, 0) in game.highlighted_cells()
    game.select(0, 8)
    assert game.highlighted_cells() == expected_region({(0, 8), (2, 2), (5, 6)})
    game.select(8, 8)
    assert game.highlighted_cells() == expected_region({(8, 8)})
    assert (3, 0) not in game.highlighted_cells()


def test_wrong_large_digit_preserves_existing_selected_region(game):
    game.select(4, 7)
    game.enter(8)
    assert game.mistakes == 1
    assert game.highlighted_cells() == expected_region({(4, 7), (4, 5), (6, 2)})
    assert game.wrong_cells() == {(4, 7)}


def test_highlight_queries_do_not_change_game_or_return_shared_mutable_state(game):
    game.select(5, 4)
    before = [row[:] for row in game.board]
    game.highlighted_cells().clear()
    assert game.highlighted_cells() == expected_region({(3, 0), (5, 4)})
    assert game.board == before and not game.history and not game.notes
    assert game.mistakes == 0 and game.selected == (5, 4)
