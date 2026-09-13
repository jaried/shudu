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
from sudoku_view import BG, CELL, ERROR, ERROR_INK, HEIGHT, INK, LEFT, PEER, SAME, SELECTED, TOP, WHITE, WIDTH

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


def test_lost_overlay_restart_resets_errors_and_board(app):
    cell_click(app, 4, 7)
    for digit in (8, 9, 1):
        button_click(app, f"digit:{digit}")
    assert app.game.status == "lost"
    assert not app.view.targets["hint"][1]
    button_click(app, "overlay:restart")
    assert app.game.status == "playing" and app.game.mistakes == 0
    assert app.game.value((4, 7)) == 0


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
