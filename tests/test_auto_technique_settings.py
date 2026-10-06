"""验证所有逻辑算法都可独立配置自动执行。
默认仅启用此前的简单算法集合，高级算法保持未勾选。
GUI 修改后通过 UserSettingsStore 保存，下次产品启动恢复完整集合。
每个已启用算法都通过同一求解器入口执行到固定点。
"""

import os
import sys
import tkinter as tk
from copy import deepcopy

import pytest
from sudoku_game import Game
from test_auto_simple import AUTO_NOTES_PUZZLE

from shudu.user_settings import UserSettings, UserSettingsStore
from shudu_solver import AUTO_TECHNIQUE_NAMES, DEFAULT_AUTO_TECHNIQUES, ShuduSolver
from sudoku_gui import SudokuWindow, main

EXPECTED_NAMES = (
    "hidden_single",
    "naked_single",
    "naked_pair",
    "hidden_pair",
    "naked_triple",
    "hidden_triple",
    "pointing_pair",
    "box_line_reduction",
    "x_wing",
    "xy_wing",
)
EXPECTED_DEFAULTS = {
    "hidden_single",
    "naked_single",
    "naked_pair",
    "naked_triple",
    "pointing_pair",
}


def test_all_logic_techniques_are_configurable():
    assert AUTO_TECHNIQUE_NAMES == EXPECTED_NAMES
    assert DEFAULT_AUTO_TECHNIQUES == EXPECTED_DEFAULTS


def test_default_game_enables_only_previous_simple_techniques():
    game = Game(auto_simple=True)
    enabled = {name for name, _, checked in game.auto_technique_settings() if checked}
    assert enabled == EXPECTED_DEFAULTS


def test_custom_auto_techniques_can_enable_only_one_advanced_algorithm():
    game = Game(auto_techniques={"x_wing"})
    assert game.auto_techniques == {"x_wing"}
    assert game.auto_simple


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_solver_selection_reaches_each_algorithm(name):
    solver = ShuduSolver([[0] * 9 for _ in range(9)])
    calls = []

    def selected_technique():
        calls.append(name)
        return False

    setattr(solver, name, selected_technique)
    solver.solve_techniques_result({name})
    assert calls == [name]


def test_game_toggles_algorithms_independently():
    game = Game(auto_simple=True)
    game.set_auto_technique("naked_pair", False)
    assert "naked_pair" not in game.auto_techniques
    assert EXPECTED_DEFAULTS - {"naked_pair"} == game.auto_techniques
    game.status = "paused"
    game.set_auto_technique("hidden_pair", True)
    assert "hidden_pair" in game.auto_techniques
    assert "box_line_reduction" not in game.auto_techniques


def test_enabling_one_auto_technique_only_changes_configuration():
    game = Game(auto_techniques=set())
    before_board = [row[:] for row in game.board]
    before_notes = {cell: set(values) for cell, values in game.notes.items()}
    before_history = list(game.history)
    game.set_auto_technique("hidden_pair", True)
    assert game.auto_techniques == {"hidden_pair"}
    assert game.board == before_board
    assert game.notes == before_notes
    assert game.history == before_history


def test_master_switch_off_blocks_all_selected_algorithms_without_state_changes():
    game = Game(AUTO_NOTES_PUZZLE, auto_techniques=AUTO_TECHNIQUE_NAMES)
    game.auto_solve = False
    game.notes = {(0, 8): {9}}
    before = deepcopy((game.board, game.notes, game.history, game.simple_eliminations))
    assert game.auto_solve_enabled(remember=True) == 0
    assert (game.board, game.notes, game.history, game.simple_eliminations) == before
    assert game.auto_techniques == set(AUTO_TECHNIQUE_NAMES)


def test_auto_notes_with_master_off_only_generates_basic_candidates():
    game = Game(AUTO_NOTES_PUZZLE, auto_techniques=AUTO_TECHNIQUE_NAMES)
    game.auto_solve = False
    before = deepcopy(game.board)
    game.auto_notes()
    assert game.board == before
    assert game.notes[(0, 8)] == {9}
    assert len(game.history) == 1


def test_enabling_master_preserves_selection_and_defers_solver_execution():
    game = Game(AUTO_NOTES_PUZZLE, auto_techniques={"hidden_single"})
    game.auto_solve = False
    before = deepcopy((game.board, game.notes, game.history))
    game.set_auto_solve(True)
    assert game.auto_solve
    assert game.auto_techniques == {"hidden_single"}
    assert (game.board, game.notes, game.history) == before
    assert game.auto_solve_enabled() == 1 and game.board[0][8] == 9


def test_master_off_keeps_hint_available_and_independent():
    game = Game(AUTO_NOTES_PUZZLE, auto_techniques=AUTO_TECHNIQUE_NAMES)
    game.hint()
    expected = game.hint_preview
    game.close_hint()
    game.auto_solve = False
    game.hint()
    assert game.hint_preview == expected and game.hint_preview.step is not None


def test_master_off_stops_correct_entries_and_legacy_auto_calls(monkeypatch):
    game = Game(AUTO_NOTES_PUZZLE, auto_techniques=AUTO_TECHNIQUE_NAMES, auto_solve=False)

    def forbidden_solver(*args, **kwargs):
        pytest.fail("总开关关闭时自动入口仍创建 solver")

    monkeypatch.setattr("shudu.sudoku_game.ShuduSolver", forbidden_solver)
    assert game.auto_solve_simple() == 0
    game.set_auto_simple(True)
    assert not game.auto_solve and not game.history
    game.selected = (0, 8)
    game.enter(9)
    assert game.board[0][8] == 9
    assert not game.notes


def test_master_on_with_no_checked_algorithms_does_not_solve():
    game = Game(AUTO_NOTES_PUZZLE, auto_techniques=set(), auto_solve=True)
    before = deepcopy((game.board, game.notes, game.history))
    assert game.auto_solve_enabled() == 0
    assert (game.board, game.notes, game.history) == before


def test_master_on_only_executes_checked_algorithms():
    game = Game(AUTO_NOTES_PUZZLE, auto_techniques={"hidden_pair"}, auto_solve=True)
    assert game.auto_solve_enabled() == 0
    assert game.board[0][8] == 0
    game.set_auto_technique("hidden_single", True)
    assert game.board[0][8] == 0
    assert game.auto_solve_enabled() == 1
    assert game.board[0][8] == 9


@pytest.mark.skipif(
    sys.platform.startswith("linux") and not os.environ.get("DISPLAY"),
    reason="GUI 测试需要显示环境或 xvfb-run",
)
def test_settings_menu_defaults_match_previous_simple_algorithms(monkeypatch):
    root = tk.Tk()
    window = SudokuWindow(root, Game(auto_simple=True))
    monkeypatch.setattr(window, "_popup", lambda menu: None)
    window.show_settings()
    checked = {name for name, variable in window._auto_technique_vars.items() if variable.get()}
    assert set(window._auto_technique_vars) == set(EXPECTED_NAMES)
    assert checked == EXPECTED_DEFAULTS
    window.close()


@pytest.mark.skipif(
    sys.platform.startswith("linux") and not os.environ.get("DISPLAY"),
    reason="GUI 测试需要显示环境或 xvfb-run",
)
def test_setting_change_is_saved_immediately(tmp_path, monkeypatch):
    store = UserSettingsStore(tmp_path / "settings.json")
    root = tk.Tk()
    window = SudokuWindow(root, Game(auto_techniques=set()), settings_store=store)
    monkeypatch.setattr(window, "_popup", lambda menu: None)
    window.show_settings()
    window._auto_technique_vars["x_wing"].set(True)
    window._set_auto_technique("x_wing")
    assert store.load().auto_techniques == frozenset({"x_wing"})
    window.close()


@pytest.mark.skipif(
    sys.platform.startswith("linux") and not os.environ.get("DISPLAY"),
    reason="GUI 测试需要显示环境或 xvfb-run",
)
def test_master_menu_toggle_preserves_checks_and_saves_both_preferences(tmp_path, monkeypatch):
    store = UserSettingsStore(tmp_path / "settings.json")
    root = tk.Tk()
    game = Game(AUTO_NOTES_PUZZLE, auto_techniques=AUTO_TECHNIQUE_NAMES)
    window = SudokuWindow(root, game, settings_store=store)
    menus = []
    monkeypatch.setattr(window, "_popup", menus.append)
    try:
        window.show_settings()
        assert menus[-1].entrycget(0, "label") == "自动求解"
        assert window._auto_solve.get()
        before = deepcopy((game.board, game.notes, game.history))
        window._auto_solve.set(False)
        window._set_auto_solve()
        assert not game.auto_solve
        assert game.auto_techniques == set(AUTO_TECHNIQUE_NAMES)
        assert (game.board, game.notes, game.history) == before
        assert not store.load().auto_solve
        assert store.load().auto_techniques == set(AUTO_TECHNIQUE_NAMES)
        window.show_settings()
        assert not window._auto_solve.get()
        assert all(variable.get() for variable in window._auto_technique_vars.values())
        window._auto_technique_vars["hidden_pair"].set(False)
        window._set_auto_technique("hidden_pair")
        assert not store.load().auto_solve
        assert store.load().auto_techniques == set(AUTO_TECHNIQUE_NAMES) - {"hidden_pair"}
        window.restart()
        assert not window.game.auto_solve
        assert window.game.auto_techniques == game.auto_techniques
        assert window.game.board == AUTO_NOTES_PUZZLE.grid()
    finally:
        window.close()


@pytest.mark.parametrize("screenshot_path", (None, "screenshot.png"))
def test_product_startup_preserves_saved_master_off(tmp_path, monkeypatch, screenshot_path):
    store = UserSettingsStore(tmp_path / "settings.json")
    store.save(UserSettings.from_auto_techniques(AUTO_TECHNIQUE_NAMES, auto_solve=False))
    captured = {}

    class FakeRoot:
        def mainloop(self):
            pass

    def fake_window(root, game, settings_store=None):
        captured["game"] = game

    def fake_screenshot(path, auto_techniques=None, auto_solve=True):
        return Game(AUTO_NOTES_PUZZLE, auto_techniques=auto_techniques, auto_solve=auto_solve)

    monkeypatch.setattr("sudoku_gui.tk.Tk", FakeRoot)
    monkeypatch.setattr("sudoku_gui.SudokuWindow", fake_window)
    monkeypatch.setattr("sudoku_gui.game_from_screenshot", fake_screenshot)
    main(puzzle=AUTO_NOTES_PUZZLE, screenshot_path=screenshot_path, settings_store=store)
    assert not captured["game"].auto_solve
    assert captured["game"].auto_techniques == set(AUTO_TECHNIQUE_NAMES)
    assert captured["game"].board == AUTO_NOTES_PUZZLE.grid()


def test_product_startup_restores_saved_auto_techniques(tmp_path, monkeypatch):
    store = UserSettingsStore(tmp_path / "settings.json")
    store.save(UserSettings.from_auto_techniques({"x_wing", "hidden_pair"}))
    captured = {}

    class FakeRoot:
        def mainloop(self):
            captured["mainloop"] = True

    def fake_window(root, game, settings_store=None):
        captured["game"] = game
        captured["store"] = settings_store
        return object()

    monkeypatch.setattr("sudoku_gui.tk.Tk", FakeRoot)
    monkeypatch.setattr("sudoku_gui.SudokuWindow", fake_window)
    main(settings_store=store)
    assert captured["game"].auto_techniques == {"x_wing", "hidden_pair"}
    assert captured["store"] is store
    assert captured["mainloop"]
