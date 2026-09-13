"""在真实 Tk 窗口中验证鼠标、键盘与着色。
无显示环境时仅跳过本文件中的 GUI 测试。
Linux 可通过 xvfb-run 启动虚拟显示运行全部交互测试。
这些测试不等同于在 Windows 实机上的人工验收。
"""

import os
import sys
import tkinter as tk

import pytest

from sudoku_game import Game
from sudoku_gui import SudokuWindow
from sudoku_view import BG, CELL, ERROR, ERROR_INK, ERROR_LIGHT, HEIGHT, INK, LEFT, PEER, SAME, SELECTED, TOP, WHITE, WIDTH

pytestmark = pytest.mark.skipif(sys.platform.startswith("linux") and not os.environ.get("DISPLAY"), reason="GUI 测试需要显示环境或 xvfb-run")


@pytest.fixture
def app():
    root = tk.Tk()
    result = SudokuWindow(root)
    root.geometry(f"{WIDTH}x{HEIGHT}+20+20")
    root.update()
    yield result
    result.close()


def click(app, x, y):
    sx, sy = app.view.screen(x, y)
    app.view.event_generate("<Button-1>", x=round(sx), y=round(sy))
    app.root.update()


def cell_click(app, row, col):
    click(app, LEFT+(col+0.5)*CELL, TOP+(row+0.5)*CELL)


def button_click(app, action):
    bounds, enabled = app.view.targets[action]
    assert enabled
    x1, y1, x2, y2 = bounds
    click(app, (x1+x2)/2, (y1+y2)/2)


def color(app, tag):
    item = app.view.find_withtag(tag)[0]
    result = app.view.itemcget(item, "fill")
    return result


def press(app, key, state=0):
    app.root.focus_force()
    app.view.focus_set()
    app.root.update()
    app.view.event_generate("<KeyPress>", keysym=key, state=state)
    app.root.update()


def test_initial_selection_shades_row_column_and_box(app):
    assert color(app, "cell-1-3") == SELECTED
    assert color(app, "cell-1-0") == PEER
    assert color(app, "cell-8-3") == PEER
    assert color(app, "cell-0-4") == PEER
    assert color(app, "cell-8-8") == BG


def test_same_number_and_notes_match_first_screenshot(app):
    cell_click(app, 4, 6)
    button_click(app, "notes-switch")
    button_click(app, "digit:4")
    cell_click(app, 5, 4)
    assert color(app, "cell-5-4") == INK
    assert color(app, "value-5-4") == WHITE
    assert color(app, "cell-3-0") == SAME
    assert color(app, "note-4-6-4") == SAME


def test_wrong_eight_and_conflicting_given_match_second_screenshot(app):
    cell_click(app, 4, 7)
    button_click(app, "digit:8")
    assert color(app, "cell-4-7") == ERROR
    assert color(app, "value-4-7") == WHITE
    assert color(app, "value-4-5") == ERROR_INK
    assert color(app, "cell-4-5") == PEER
    assert color(app, "cell-6-2") == SAME
    assert app.game.mistakes == 1


def test_mouse_note_switch_toggles_mark_instead_of_value(app):
    cell_click(app, 6, 6)
    button_click(app, "notes-switch")
    button_click(app, "digit:4")
    assert app.game.notes[(6, 6)] == {4} and app.game.value((6, 6)) == 0
    assert app.view.find_withtag("note-6-6-4")
    button_click(app, "digit:4")
    assert (6, 6) not in app.game.notes
    assert not app.view.find_withtag("note-6-6-4")


def test_selected_big_digit_highlights_matching_small_notes_even_when_notes_mode_is_off(app):
    cell_click(app, 6, 6)
    button_click(app, "notes-switch")
    button_click(app, "digit:4")
    button_click(app, "notes-switch")
    assert not app.game.notes_mode
    cell_click(app, 5, 4)
    assert app.game.active_digit == 4
    assert color(app, "note-6-6-4") == SAME


def test_turn_off_notes_places_a_formal_digit(app):
    cell_click(app, 0, 0)
    button_click(app, "notes")
    button_click(app, "digit:8")
    button_click(app, "notes-switch")
    button_click(app, "digit:8")
    assert app.game.value((0, 0)) == 8
    assert not app.view.find_withtag("note-0-0-8")
    assert app.view.find_withtag("value-0-0")


def test_mouse_erase_and_undo_restore_number(app):
    cell_click(app, 0, 0)
    button_click(app, "digit:8")
    button_click(app, "erase")
    assert app.game.value((0, 0)) == 0
    button_click(app, "undo")
    assert app.game.value((0, 0)) == 8


def test_keyboard_notes_digit_arrows_and_delete(app):
    cell_click(app, 0, 0)
    press(app, "n")
    press(app, "4")
    assert app.game.notes[(0, 0)] == {4}
    press(app, "Delete")
    assert not app.game.notes
    press(app, "z", state=0x4)
    assert app.game.notes[(0, 0)] == {4}
    press(app, "Right")
    assert app.game.selected == (0, 1)


def test_pause_hides_board_and_blocks_input_until_resume(app):
    button_click(app, "pause")
    assert app.game.status == "paused"
    assert not app.view.find_withtag("cell-0-0")
    press(app, "8")
    assert not app.game.history
    button_click(app, "overlay:pause")
    assert app.game.status == "playing"
    assert app.view.find_withtag("cell-0-0")


def test_small_window_keeps_hit_testing_aligned(app):
    app.root.geometry("430x613")
    app.root.update()
    cell_click(app, 8, 8)
    assert app.game.selected == (8, 8)
    button_click(app, "digit:6")
    assert app.game.value((8, 8)) == 6
    assert abs(app.view.scale_factor - min(430/WIDTH, 613/HEIGHT)) < 0.001


def test_large_letterboxed_window_keeps_hit_testing_aligned(app):
    app.root.geometry("1000x1000")
    app.root.update()
    cell_click(app, 0, 0)
    assert app.game.selected == (0, 0)
    button_click(app, "digit:8")
    assert app.game.value((0, 0)) == 8
    assert app.view.offset[0] > 0


def test_timer_update_does_not_recreate_board_items(app):
    before = app.view.find_all()
    app.view.update_timer()
    assert app.view.find_all() == before
    assert app.view.itemcget("timer", "text") == app.game.time_text


def test_many_errors_keep_game_playable_and_counter_has_no_limit_suffix(app):
    cell_click(app, 4, 7)
    for digit in (8, 9, 1, 2, 3, 5, 6, 7):
        button_click(app, f"digit:{digit}")
    assert app.game.status == "playing"
    assert app.game.mistakes == 8
    assert app.view.targets["hint"][1]
    assert app.view.itemcget("mistake-count", "text") == "8"
    assert not app.view.find_withtag("mistake-limit")


def test_cancel_new_game_preserves_progress(app, monkeypatch):
    cell_click(app, 0, 0)
    button_click(app, "digit:8")
    monkeypatch.setattr("sudoku_gui.messagebox.askyesno", lambda *args, **kwargs: False)
    app.restart()
    assert app.game.value((0, 0)) == 8


def test_confirm_new_game_resets_state_preserving_cleanup_preference(app, monkeypatch):
    cell_click(app, 0, 0)
    button_click(app, "digit:8")
    app.game.auto_clean = False
    monkeypatch.setattr("sudoku_gui.messagebox.askyesno", lambda *args, **kwargs: True)
    app.restart()
    assert app.game.value((0, 0)) == 0
    assert not app.game.auto_clean
    assert not app.game.history


def test_all_fours_expand_peer_background_without_overriding_digit_colors(app):
    cell_click(app, 5, 4)
    assert color(app, "cell-5-4") == INK
    assert color(app, "cell-3-0") == SAME
    assert color(app, "value-3-0") == WHITE
    assert color(app, "cell-3-8") == PEER
    assert color(app, "cell-8-0") == PEER
    assert color(app, "cell-4-2") == PEER
    assert color(app, "cell-0-8") == BG


def test_empty_selection_and_note_input_do_not_keep_global_peer_background(app):
    cell_click(app, 5, 4)
    assert color(app, "cell-4-2") == PEER
    cell_click(app, 8, 8)
    button_click(app, "notes-switch")
    button_click(app, "digit:4")
    assert color(app, "cell-8-8") == SELECTED
    assert color(app, "cell-4-2") == BG
    assert color(app, "cell-5-4") == SAME
    assert color(app, "note-8-8-4") == SAME


def test_clicking_given_includes_peer_regions_of_player_entered_number(app):
    cell_click(app, 0, 0)
    button_click(app, "digit:8")
    cell_click(app, 4, 5)
    assert color(app, "cell-0-0") == SAME
    assert color(app, "cell-0-8") == PEER
    assert color(app, "cell-2-1") == PEER
    assert color(app, "cell-3-0") == PEER


def test_global_peer_background_keeps_wrong_cell_and_conflict_colors(app):
    cell_click(app, 4, 7)
    button_click(app, "digit:8")
    cell_click(app, 4, 5)
    assert color(app, "cell-4-7") == ERROR_LIGHT
    assert color(app, "value-4-7") == ERROR_INK
    assert color(app, "value-4-5") == ERROR_INK
    assert color(app, "cell-6-2") == SAME
    assert color(app, "cell-0-2") == PEER


def test_highlight_region_is_computed_once_per_board_redraw(app, monkeypatch):
    calls = []
    original = app.game.highlighted_cells
    def tracked():
        calls.append(app.game.selected)
        result = original()
        return result
    monkeypatch.setattr(app.game, "highlighted_cells", tracked)
    app.view.draw()
    assert calls == [app.game.selected]


def test_hint_mouse_opens_read_only_explanation_and_returns_without_filling(app):
    cell_click(app, 8, 8)
    before = [row[:] for row in app.game.board]
    button_click(app, "hint")
    assert app.game.status == "hint" and app.game.board == before
    assert app.view.find_withtag("hint-outline")
    assert app.view.hint_panel is not None
    assert not app.view.find_withtag("hint-value-0-2")
    button_click(app, "close-hint")
    assert app.game.status == "playing" and app.game.board == before
    assert app.view.hint_panel is None and not app.game.history


def test_hint_click_any_canvas_position_closes_it(app):
    button_click(app, "hint")
    assert app.game.status == "hint"
    click(app, 12, 12)
    assert app.game.status == "playing" and app.view.hint_panel is None


def test_hint_click_inside_description_closes_it(app):
    button_click(app, "hint")
    text = next(child for child in app.view.hint_panel.winfo_children() if isinstance(child, tk.Text))
    text.event_generate("<Button-1>", x=5, y=5)
    app.root.update()
    assert app.game.status == "playing" and app.view.hint_panel is None


def test_hint_shows_source_digits_and_correct_focus_box(app):
    button_click(app, "hint")
    assert color(app, "hint-cell-1-7") == SAME
    assert color(app, "hint-value-1-7") == WHITE
    assert app.game.hint_preview.targets == {(0, 2)}
    assert set(app.game.hint_preview.units[0]) == {(r, c) for r in range(3) for c in range(3)}
    assert set(app.view.targets) == {"close-hint"}


def test_hint_keyboard_blocks_input_and_arrow_moves_until_escape(app):
    cell_click(app, 0, 0)
    press(app, "h")
    for key in ("8", "n", "a", "Right", "Delete"):
        press(app, key)
    assert app.game.selected == (0, 0) and app.game.value((0, 0)) == 0
    assert not app.game.notes and not app.game.history
    press(app, "Escape")
    press(app, "8")
    assert app.game.value((0, 0)) == 8


@pytest.mark.parametrize("key", ["space", "Return", "h"])
def test_hint_other_close_shortcuts_do_not_apply_step(app, key):
    press(app, "h")
    press(app, key)
    assert app.game.status == "playing"
    assert app.game.value((0, 2)) == 0 and not app.game.history


def test_auto_notes_button_operates_while_given_is_selected(app):
    cell_click(app, 0, 4)
    button_click(app, "auto-notes")
    assert len(app.game.notes) == 57 and app.game.notes_mode
    assert not app.view.find_withtag("note-0-4-9")
    assert app.view.find_withtag("note-0-0-8")
    button_click(app, "undo")
    assert not app.game.notes


def test_auto_notes_keyboard_and_pen_switch_have_separate_actions(app):
    press(app, "a")
    assert len(app.game.notes) == 57 and app.game.notes_mode
    button_click(app, "notes-switch")
    assert not app.game.notes_mode and len(app.game.notes) == 57
    assert app.view.action_at(436, 745) == "auto-notes"


def test_auto_notes_button_disables_on_error_without_suppressing_warning_hint(app):
    cell_click(app, 4, 7)
    button_click(app, "digit:8")
    assert not app.view.targets["auto-notes"][1]
    button_click(app, "hint")
    assert app.game.hint_preview.step is None
    assert color(app, "hint-cell-4-7") == ERROR
    button_click(app, "close-hint")
    assert app.game.value((4, 7)) == 8 and app.game.mistakes == 1


def test_hint_resize_recreates_panel_without_leaking_old_widgets(app):
    button_click(app, "hint")
    old = app.view.hint_panel
    app.root.geometry("430x613")
    app.root.update()
    assert not old.winfo_exists()
    assert len(app.view.winfo_children()) == 1
    button_click(app, "close-hint")
    assert not app.view.winfo_children()
    button_click(app, "auto-notes")
    assert len(app.game.notes) == 57


def test_long_hint_text_remains_read_only_and_scrollable(app):
    from dataclasses import replace
    button_click(app, "hint")
    app.game.hint_preview = replace(app.game.hint_preview, message="完整的推理说明。" * 300)
    app.view.draw()
    app.root.update()
    text = next(child for child in app.view.hint_panel.winfo_children() if isinstance(child, tk.Text))
    text.count("1.0", "end", "update", "ypixels")
    assert text.cget("state") == "disabled" and text.yview()[1] < 1
    text.yview_moveto(1)
    assert text.yview()[1] == 1 and app.game.value((0, 2)) == 0


def test_elimination_hint_draws_red_candidates_without_removing_notes(app):
    from test_sudoku_hints import elimination_game, play_state
    app.game = elimination_game()
    app.view.game = app.game
    app._bind_commands()
    app.view.draw()
    before = play_state(app.game)
    button_click(app, "hint")
    assert app.view.find_withtag("hint-removal")
    assert play_state(app.game) == before
