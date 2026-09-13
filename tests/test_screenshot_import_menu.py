"""验证 GUI 可反复选择截图文件并安装对应游戏。
文件选择和识别模块通过公开接口替换，避免测试依赖真实磁盘截图。
测试覆盖菜单入口、偏好继承、重复导入和失败提示。
Linux 无显示环境时跳过本文件中的 Tk 交互测试。
"""

import os
import sys
import tkinter as tk

import pytest

from sudoku_game import Game
from sudoku_gui import SudokuWindow

pytestmark = pytest.mark.skipif(
    sys.platform.startswith("linux") and not os.environ.get("DISPLAY"),
    reason="GUI 测试需要显示环境或 xvfb-run",
)


@pytest.fixture
def app():
    root = tk.Tk()
    result = SudokuWindow(root)
    root.update()
    yield result
    result.close()


def test_levels_menu_contains_screenshot_import(app, monkeypatch):
    captured = {}
    monkeypatch.setattr(app, "_popup", lambda menu: captured.setdefault("menu", menu))
    app.show_levels()
    menu = captured["menu"]
    labels = [menu.entrycget(index, "label") for index in range(menu.index("end") + 1)]
    assert "从截图导入…" in labels


def test_screenshot_import_preserves_preferences_and_rebinds_view(app, monkeypatch):
    app.game.auto_simple = True
    app.game.auto_clean = False
    seen = []
    monkeypatch.setattr("sudoku_gui.filedialog.askopenfilename", lambda **kwargs: "first.png")
    monkeypatch.setattr("sudoku_gui.game_from_screenshot", _fake_loader(seen))
    app.import_screenshot()
    assert seen == [("first.png", True)]
    assert app.game.auto_simple
    assert not app.game.auto_clean
    assert app.game.notes == {(0, 0): {1}}
    assert app.view.game is app.game


def test_screenshot_import_can_run_repeatedly(app, monkeypatch):
    paths = iter(("first.png", "second.png"))
    seen = []
    monkeypatch.setattr("sudoku_gui.filedialog.askopenfilename", lambda **kwargs: next(paths))
    monkeypatch.setattr("sudoku_gui.game_from_screenshot", _fake_loader(seen))
    app.import_screenshot()
    first_game = app.game
    app.import_screenshot()
    assert seen == [("first.png", False), ("second.png", False)]
    assert app.game is not first_game
    assert app.game.message == "second.png"


def test_screenshot_import_failure_keeps_current_game(app, monkeypatch):
    original = app.game
    errors = []
    monkeypatch.setattr("sudoku_gui.filedialog.askopenfilename", lambda **kwargs: "bad.png")
    monkeypatch.setattr("sudoku_gui.game_from_screenshot", _failing_loader)
    monkeypatch.setattr("sudoku_gui.messagebox.showerror", lambda title, text, **kwargs: errors.append((title, text)))
    app.import_screenshot()
    assert app.game is original
    assert errors == [("截图导入失败", "识别失败")]


def _fake_loader(seen):
    def load(path, auto_simple=True):
        seen.append((path, auto_simple))
        game = Game(auto_simple=auto_simple)
        game.notes = {(0, 0): {1}}
        game.notes_mode = True
        game.message = path
        return game
    return load


def _failing_loader(path, auto_simple=True):
    raise ValueError("识别失败")
