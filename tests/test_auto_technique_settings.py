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

    monkeypatch.setattr("shudu.sudoku_game.solve_auto", forbidden_solver)
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
    try:
        window.show_settings()
        root.update()
        popup = window._settings_popup
        checked = {name for name in EXPECTED_NAMES if popup.nametowidget(f"submenu.auto_technique_{name}").cget("image") == (str(popup._check_icons[True]),)}
        assert set(popup._checked) >= {"auto_solve", "auto_clean"}
        assert checked == EXPECTED_DEFAULTS
    finally:
        window.close()


@pytest.mark.skipif(
    sys.platform.startswith("linux") and not os.environ.get("DISPLAY"),
    reason="GUI 测试需要显示环境或 xvfb-run",
)
def test_setting_change_is_saved_immediately(tmp_path, monkeypatch):
    store = UserSettingsStore(tmp_path / "settings.json")
    root = tk.Tk()
    window = SudokuWindow(root, Game(auto_techniques=set()), settings_store=store)
    try:
        window.show_settings()
        window._settings_popup.nametowidget("submenu.auto_technique_x_wing").invoke()
        assert store.load().auto_techniques == frozenset({"x_wing"})
    finally:
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
    try:
        window.show_settings()
        popup = window._settings_popup
        assert popup.nametowidget("menu.auto_solve").cget("text") == "自动求解"
        before = deepcopy((game.board, game.notes, game.history))
        popup.nametowidget("menu.auto_solve").invoke()
        assert not game.auto_solve
        assert game.auto_techniques == set(AUTO_TECHNIQUE_NAMES)
        assert (game.board, game.notes, game.history) == before
        assert not store.load().auto_solve
        assert store.load().auto_techniques == set(AUTO_TECHNIQUE_NAMES)
        window.show_settings()
        popup = window._settings_popup
        assert popup._checked["auto_solve"] is False
        assert all(popup._checked[f"auto_technique:{name}"] for name in AUTO_TECHNIQUE_NAMES)
        popup.nametowidget("submenu.auto_technique_hidden_pair").invoke()
        assert not store.load().auto_solve
        assert store.load().auto_techniques == set(AUTO_TECHNIQUE_NAMES) - {"hidden_pair"}
        window.restart()
        assert not window.game.auto_solve
        assert window.game.auto_techniques == game.auto_techniques
        assert window.game.board == AUTO_NOTES_PUZZLE.grid()
    finally:
        window.close()


@pytest.mark.skipif(
    sys.platform.startswith("linux") and not os.environ.get("DISPLAY"),
    reason="GUI 测试需要显示环境或 xvfb-run",
)
def test_auto_clean_changes_only_memory_and_row(tmp_path, monkeypatch):
    store = UserSettingsStore(tmp_path / "settings.json")
    root = tk.Tk()
    window = SudokuWindow(root, Game(auto_techniques=set()), settings_store=store)
    try:
        window.show_settings()
        game = window.game
        before = deepcopy((game.board, game.notes, game.history, game.message))
        monkeypatch.setattr(game, "completed_units", lambda: pytest.fail("auto_clean must not scan completed units"))
        monkeypatch.setattr(window.view, "draw", lambda: pytest.fail("auto_clean must not redraw"))
        monkeypatch.setattr(window.view, "animate_completed_units", lambda units: pytest.fail("auto_clean must not animate"))
        monkeypatch.setattr(store, "save", lambda settings: pytest.fail("auto_clean must not save"))
        monkeypatch.setattr(store, "load", lambda: pytest.fail("auto_clean must not access store"))
        window._settings_popup.nametowidget("menu.auto_clean").invoke()
        assert game.auto_clean is False
        assert (game.board, game.notes, game.history, game.message) == before
    finally:
        window.close()


@pytest.mark.skipif(
    sys.platform.startswith("linux") and not os.environ.get("DISPLAY"),
    reason="GUI 测试需要显示环境或 xvfb-run",
)
def test_preference_save_failure_keeps_memory_and_reports_error(tmp_path, monkeypatch):
    store = UserSettingsStore(tmp_path / "settings.json")
    root = tk.Tk()
    window = SudokuWindow(root, Game(auto_techniques=set()), settings_store=store)
    errors = []
    monkeypatch.setattr(store, "save", lambda settings: (_ for _ in ()).throw(OSError("disk full")))
    monkeypatch.setattr("sudoku_gui.messagebox.showerror", lambda *args, **kwargs: errors.append(args))
    try:
        window.show_settings()
        window._settings_popup.nametowidget("submenu.auto_technique_x_wing").invoke()
        assert window.game.auto_techniques == {"x_wing"}
        assert errors and "disk full" in errors[0][1]
    finally:
        window.close()


@pytest.mark.skipif(
    sys.platform.startswith("linux") and not os.environ.get("DISPLAY"),
    reason="GUI 测试需要显示环境或 xvfb-run",
)
def test_algorithm_entry_is_a_cascade(monkeypatch):
    root = tk.Tk()
    window = SudokuWindow(root)
    try:
        window.show_settings()
        assert window._settings_popup.nametowidget("menu.auto_technique").cget("text").startswith("自动解决算法")
    finally:
        window.close()


@pytest.mark.skipif(
    sys.platform.startswith("linux") and not os.environ.get("DISPLAY"),
    reason="GUI 测试需要显示环境或 xvfb-run",
)
def test_algorithm_popup_stays_open_for_successive_mouse_selections(tmp_path):
    store = UserSettingsStore(tmp_path / "settings.json")
    root = tk.Tk()
    game = Game(auto_techniques=set(), auto_solve=False)
    window = SudokuWindow(root, game, settings_store=store)
    try:
        root.update()
        root.focus_force()
        window.show_settings()
        root.update()
        popup = window._settings_popup
        assert popup is not None and popup.winfo_ismapped()
        pointer_x, pointer_y = root.winfo_pointerxy()
        # 让真实系统指针避开弹层，防止它与生成的悬停事件同时操作菜单。
        popup.post(
            0 if pointer_x > root.winfo_screenwidth() // 2 else root.winfo_screenwidth() - 500,
            0 if pointer_y > root.winfo_screenheight() // 2 else root.winfo_screenheight() - 500,
        )
        root.update()
        submenu = popup.nametowidget("submenu")
        assert not submenu.winfo_ismapped()
        popup.nametowidget("menu.auto_technique").event_generate("<Enter>")
        root.update()
        assert submenu.winfo_ismapped()
        before = deepcopy((game.board, game.notes, game.history))
        for name, enabled in (("hidden_pair", True), ("hidden_triple", True), ("hidden_pair", False)):
            button = submenu.nametowidget(f"auto_technique_{name}")
            assert button.winfo_class() == "TButton"
            button.event_generate("<Enter>", x=10, y=10)
            button.event_generate("<ButtonPress-1>", x=10, y=10)
            button.event_generate("<ButtonRelease-1>", x=10, y=10, state=0x100)
            root.update()
            assert (name in game.auto_techniques) is enabled
            assert button.cget("image") == (str(popup._check_icons[enabled]),)
            assert popup.winfo_ismapped() and submenu.winfo_ismapped() and popup.grab_current() == popup
            assert store.load().auto_techniques == game.auto_techniques
        button = submenu.nametowidget("auto_technique_hidden_triple")
        button.focus_force()
        root.update()
        button.event_generate("<KeyPress-space>")
        root.update()
        assert not game.auto_techniques and not store.load().auto_techniques
        assert submenu.winfo_ismapped()
        popup.nametowidget("menu.auto_solve").event_generate("<Enter>")
        root.update()
        assert not submenu.winfo_ismapped()
        assert root.focus_displayof() == popup
        root.focus_displayof().event_generate("<KeyPress-space>")
        root.update()
        assert not game.auto_techniques and not store.load().auto_techniques
        popup.nametowidget("menu.auto_technique").event_generate("<Enter>")
        root.update()
        assert submenu.winfo_ismapped()
        assert not store.load().auto_solve
        assert (game.board, game.notes, game.history) == before
        popup.event_generate("<Escape>")
        root.update()
        assert window._settings_popup is None
        assert root.grab_current() is None
    finally:
        window.close()


@pytest.mark.skipif(
    sys.platform.startswith("linux") and not os.environ.get("DISPLAY"),
    reason="GUI 测试需要显示环境或 xvfb-run",
)
def test_algorithm_popup_closes_on_outside_click_and_can_reopen():
    root = tk.Tk()
    window = SudokuWindow(root)
    try:
        root.update()
        root.focus_force()
        window.show_settings()
        root.update()
        popup = window._settings_popup
        popup.nametowidget("menu.auto_technique").event_generate("<Enter>")
        root.update()
        popup.event_generate(
            "<ButtonPress-1>",
            x=popup.winfo_width() + 10,
            y=10,
            rootx=popup.winfo_rootx() + popup.winfo_width() + 10,
            rooty=popup.winfo_rooty() + 10,
        )
        root.update()
        assert window._settings_popup is None and root.grab_current() is None
        window.show_settings()
        root.update()
        assert window._settings_popup.winfo_ismapped()
        root.focus_force()
        root.update()
        assert window._settings_popup is None and root.grab_current() is None
    finally:
        window.close()


@pytest.mark.skipif(
    sys.platform.startswith("linux") and not os.environ.get("DISPLAY"),
    reason="GUI 测试需要显示环境或 xvfb-run",
)
def test_settings_popup_preserves_master_toggle_and_restart_command(tmp_path):
    store = UserSettingsStore(tmp_path / "settings.json")
    root = tk.Tk()
    window = SudokuWindow(root, settings_store=store)
    try:
        root.update()
        root.focus_force()
        root.update()
        window.show_settings()
        root.update()
        popup = window._settings_popup
        before = deepcopy((window.game.board, window.game.notes, window.game.history))
        popup.nametowidget("menu.auto_solve").invoke()
        root.update()
        assert not window.game.auto_solve and not store.load().auto_solve
        assert (window.game.board, window.game.notes, window.game.history) == before
        assert popup.winfo_ismapped()
        restart = popup.nametowidget("menu.restart")
        restart.event_generate("<Enter>", x=10, y=10)
        restart.event_generate("<ButtonPress-1>", x=10, y=10)
        restart.event_generate("<Leave>", x=restart.winfo_width() + 10, y=10, state=0x100)
        restart.event_generate("<ButtonRelease-1>", x=restart.winfo_width() + 10, y=10, state=0x100)
        root.update()
        assert window._settings_popup == popup and popup.winfo_ismapped()
        restart.event_generate("<Enter>", x=10, y=10)
        restart.event_generate("<ButtonPress-1>", x=10, y=10)
        restart.event_generate("<ButtonRelease-1>", x=10, y=10, state=0x100)
        root.update()
        assert window._settings_popup is None and root.grab_current() is None
        assert not window.game.auto_solve
    finally:
        window.close()


@pytest.mark.skipif(
    sys.platform.startswith("linux") and not os.environ.get("DISPLAY"),
    reason="GUI 测试需要显示环境或 xvfb-run",
)
@pytest.mark.parametrize("bounds", ((0, 0, 600, 400), (-600, -400, 0, 0)))
def test_algorithm_submenu_stays_inside_monitor_at_bottom_right(monkeypatch, bounds):
    root = tk.Tk()
    window = SudokuWindow(root)
    monkeypatch.setattr("shudu.settings_menu._popup.monitor_bounds", lambda root, x, y: bounds)
    try:
        root.update()
        window.show_settings()
        popup = window._settings_popup
        popup.post(bounds[2] - 10, bounds[3] - 10)
        popup.nametowidget("menu.auto_technique").event_generate("<Enter>")
        root.update()
        assert popup.winfo_rootx() >= bounds[0]
        assert popup.winfo_rooty() >= bounds[1]
        assert popup.winfo_rootx() + popup.winfo_width() <= bounds[2]
        assert popup.winfo_rooty() + popup.winfo_height() <= bounds[3]
        assert popup.nametowidget("submenu.auto_technique_xy_wing").winfo_viewable()
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
