"""验证 GUI 可反复选择截图文件并安装对应游戏。
文件选择和识别模块通过公开接口替换，避免测试依赖真实磁盘截图。
测试覆盖菜单入口、偏好继承、重复导入和失败提示。
Linux 无显示环境时跳过本文件中的 Tk 交互测试。
"""

import os
import sys
import tkinter as tk
from copy import deepcopy

import pytest
from sudoku_game import Game
from test_screenshot_foreground import FIXTURES, expected_image, unreadable_image

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
    labels = [menu.entrycget(index, "label") for index in range(menu.index("end") + 1) if menu.type(index) != "separator"]
    assert "从截图导入…" in labels


def test_screenshot_import_preserves_preferences_and_rebinds_view(app, monkeypatch):
    app.game.auto_simple = True
    app.game.auto_clean = False
    seen = []
    monkeypatch.setattr("sudoku_gui.filedialog.askopenfilename", lambda **kwargs: "first.png")
    monkeypatch.setattr("sudoku_gui.game_from_screenshot", _fake_loader(seen))
    app.import_screenshot()
    assert seen == [("first.png", frozenset(app.game.auto_techniques))]
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
    assert seen == [("first.png", frozenset()), ("second.png", frozenset())]
    assert app.game is not first_game
    assert app.game.message == "second.png"


def test_screenshot_import_preserves_master_off_and_algorithm_selection(app, monkeypatch):
    app.game.set_auto_technique("hidden_triple", True)
    app.game.set_auto_solve(False)
    selected = set(app.game.auto_techniques)
    seen = []
    monkeypatch.setattr("sudoku_gui.game_from_screenshot", _fake_loader(seen))
    app._load_screenshot("first.png")
    assert not app.game.auto_solve
    assert app.game.auto_techniques == selected
    assert app.game.notes == {(0, 0): {1}}


def test_screenshot_import_failure_keeps_current_game(app, monkeypatch):
    original = app.game
    errors = []
    monkeypatch.setattr("sudoku_gui.filedialog.askopenfilename", lambda **kwargs: "bad.png")
    monkeypatch.setattr("sudoku_gui.game_from_screenshot", _failing_loader)
    monkeypatch.setattr("sudoku_gui.messagebox.showerror", lambda title, text, **kwargs: errors.append((title, text)))
    app.import_screenshot()
    assert app.game is original
    assert errors == [("截图导入失败", "识别失败")]


def test_real_wechat_import_installs_complete_game_and_preserves_preferences(app):
    app.game.set_auto_technique("hidden_triple", True)
    app.game.set_auto_solve(False)
    app.game.auto_clean = False
    selected = set(app.game.auto_techniques)
    original = app.game
    for _ in range(2):
        app._load_screenshot(str(FIXTURES / "level120-wechat.jpg"))
        app.root.update()
        assert app.game is not original and app.view.game is app.game
        assert app.game.puzzle.rows == tuple(expected_image()["rows"])
        assert app.game.notes == {} and not app.game.notes_mode
        assert not app.game.auto_solve and not app.game.auto_clean
        assert app.game.auto_techniques == selected
        original = app.game


def test_real_unreadable_cell_keeps_entire_current_game(app, tmp_path, monkeypatch):
    original, original_view = app.game, app.view
    cell = next((r, c) for r in range(9) for c in range(9) if not original.given((r, c)))
    original.notes = {cell: {1, 2}}
    original.set_auto_solve(False)
    original.auto_clean = False
    before = deepcopy(original.__dict__)
    errors, installs = [], []
    monkeypatch.setattr("sudoku_gui.messagebox.showerror", lambda title, text, **kwargs: errors.append((title, text)))
    monkeypatch.setattr(app, "_install_game", lambda game: installs.append(game))
    app._load_screenshot(str(unreadable_image(tmp_path / "错误格.png")))
    app.root.update()
    assert app.game is original and app.view is original_view and app.view.game is original
    assert original.__dict__ == before
    assert installs == []
    assert len(errors) == 1 and errors[0][0] == "截图导入失败"
    assert errors[0][1].startswith("第3行第5列：正式大数字识别置信度不足：")
    assert errors[0][1].endswith("。请使用清晰截图重试。")


def _fake_loader(seen):
    def load(path, auto_techniques=None, auto_solve=True):
        techniques = frozenset(auto_techniques or ())
        seen.append((path, techniques))
        game = Game(auto_techniques=techniques, auto_solve=auto_solve)
        game.notes = {(0, 0): {1}}
        game.notes_mode = True
        game.message = path
        return game

    return load


def _failing_loader(path, auto_techniques=None, auto_solve=True):
    raise ValueError("识别失败")
