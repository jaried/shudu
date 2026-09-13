"""把 codebase-design 的 seam、Locality 与目录约束固化为可执行回归。"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "shudu"
ENTRY_FILES = {
    "logical_solver.py",
    "shudu_solver.py",
    "solver.py",
    "sudoku_gui.py",
    "techniques.py",
}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_root_only_keeps_executable_python_entries():
    root_python = {path.name for path in ROOT.glob("*.py")}
    assert root_python == ENTRY_FILES


def test_rules_module_has_no_upper_layer_dependencies():
    modules = imported_modules(PACKAGE / "sudoku_rules.py")
    forbidden = {
        "logical_solver",
        "shudu_solver",
        "shudu.sudoku_hints",
        "shudu.sudoku_game",
        "shudu.sudoku_view",
    }
    assert modules.isdisjoint(forbidden)


def test_game_does_not_depend_on_legacy_logic_implementation():
    modules = imported_modules(PACKAGE / "sudoku_game.py")
    assert "logical_solver" not in modules


def test_hint_adapter_depends_on_project_solver_not_legacy_solver():
    modules = imported_modules(PACKAGE / "sudoku_hints.py")
    assert "shudu_solver" in modules
    assert "logical_solver" not in modules


def test_hint_adapter_does_not_call_private_solver_step_interface():
    source = (PACKAGE / "sudoku_hints.py").read_text(encoding="utf-8")
    assert "._apply_next_step(" not in source


def test_hint_adapter_does_not_reimplement_algorithm_recognition():
    source = (PACKAGE / "sudoku_hints.py").read_text(encoding="utf-8")
    forbidden = (
        "_naked_subset_context",
        "_hidden_pair_context",
        "_pointing_context",
        "_box_line_context",
        "_x_wing_context",
        "_xy_wing_context",
        "from itertools import combinations",
    )
    assert all(name not in source for name in forbidden)


def test_project_solver_exports_step_evidence_directly():
    source = (ROOT / "shudu_solver.py").read_text(encoding="utf-8")
    assert "self._last_sources" in source
    assert "self._last_units" in source
    assert "LogicStep(" in source


def test_hint_view_uses_public_view_drawing_interface():
    source = (PACKAGE / "sudoku_hint_view.py").read_text(encoding="utf-8")
    assert "view.draw_header()" in source
    assert "view.draw_grid_lines()" in source
    assert "view._draw_header()" not in source
    assert "view._draw_grid_lines()" not in source


def test_screenshot_import_is_below_gui_and_game():
    modules = imported_modules(PACKAGE / "sudoku_screenshot.py")
    forbidden = {
        "sudoku_gui",
        "shudu.sudoku_view",
        "shudu.sudoku_game",
        "shudu.sudoku_hints",
        "shudu_solver",
        "logical_solver",
    }
    assert modules.isdisjoint(forbidden)
    assert "shudu.sudoku_puzzles" in modules
    assert "shudu.sudoku_rules" in modules


def test_gui_uses_screenshot_module_through_public_loader():
    modules = imported_modules(ROOT / "sudoku_gui.py")
    source = (ROOT / "sudoku_gui.py").read_text(encoding="utf-8")
    assert "shudu.sudoku_screenshot" in modules
    assert "load_screenshot_game(" in source
