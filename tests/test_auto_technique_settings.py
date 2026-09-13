"""验证所有逻辑算法都可独立配置自动执行。
默认仅启用此前的简单算法集合，高级算法保持未勾选。
设置只选择算法，不复制算法实现或依赖 GUI 私有细节。
每个已启用算法都通过同一求解器入口执行到固定点。
"""

import os
import sys
import tkinter as tk

import pytest

from shudu_solver import AUTO_TECHNIQUE_NAMES, DEFAULT_AUTO_TECHNIQUES, ShuduSolver
from sudoku_game import Game
from sudoku_gui import SudokuWindow

EXPECTED_NAMES = (
    "hidden_single",
    "naked_single",
    "naked_pair",
    "hidden_pair",
    "naked_triple",
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
