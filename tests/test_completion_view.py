"""验证挑战完成后保留棋盘界面。
完成态停止游戏输入，但不再用遮罩替换棋盘。
暂停态仍保留原遮罩行为。
测试只验证渲染状态，不修改求解规则。
"""

import os
import sys
import tkinter as tk

import pytest

from sudoku_gui import SudokuWindow
from sudoku_theme import HEIGHT, WIDTH

pytestmark = pytest.mark.skipif(
    sys.platform.startswith("linux") and not os.environ.get("DISPLAY"),
    reason="GUI 测试需要显示环境或 xvfb-run",
)


def make_app():
    root = tk.Tk()
    app = SudokuWindow(root)
    root.geometry(f"{WIDTH}x{HEIGHT}+20+20")
    root.update()
    return app


def test_completed_game_keeps_full_board_visible():
    app = make_app()
    app.game.board = [list(row) for row in app.game.solution]
    app.game._check_finished()
    app.view.draw()
    app.root.update()
    assert app.game.status == "won"
    assert app.view.find_withtag("cell-0-0")
    assert app.view.find_withtag("cell-8-8")
    assert app.view.find_withtag("value-0-0")
    assert app.view.find_withtag("value-8-8")
    assert app.view.find_withtag("completion-status")
    assert app.view.itemcget("completion-status", "text") == "挑战完成"
    assert "overlay:restart" not in app.view.targets
    app.close()


def test_completed_game_controls_are_read_only():
    app = make_app()
    app.game.board = [list(row) for row in app.game.solution]
    app.game._check_finished()
    app.view.draw()
    assert not app.view.targets["erase"][1]
    assert not app.view.targets["undo"][1]
    assert not app.view.targets["notes"][1]
    assert not app.view.targets["auto-notes"][1]
    assert not app.view.targets["hint"][1]
    assert not app.view.targets["pause"][1]
    app.close()


def test_pause_still_hides_board_behind_overlay():
    app = make_app()
    app.game.toggle_pause()
    app.view.draw()
    assert app.game.status == "paused"
    assert not app.view.find_withtag("cell-0-0")
    assert app.view.targets["overlay:pause"][1]
    app.close()
