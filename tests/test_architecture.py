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
    assert "shudu.logic_solver" in modules
    assert "shudu_solver" not in modules
    assert "logical_solver" not in modules


def test_hint_adapter_does_not_call_private_solver_step_interface():
    source = (PACKAGE / "sudoku_hints.py").read_text(encoding="utf-8")
    assert "._apply_next_step(" not in source


def test_hint_recommendation_uses_all_algorithms_with_existing_note_projection():
    source = (PACKAGE / "sudoku_hints.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    pending_args = [arg.arg for arg in functions["pending_step"].args.args]
    hint_args = [arg.arg for arg in functions["make_hint"].args.args]
    game_source = (PACKAGE / "sudoku_game.py").read_text(encoding="utf-8")
    assert pending_args == ["board", "notes"]
    assert hint_args == ["board", "notes", "wrong"]
    assert "_complete_candidate_notes" not in source
    assert "_apply_candidate_notes" not in source
    assert "next_hint_step" in source
    assert "auto_techniques" not in source
    assert "solver.next_step()" not in source
    assert "make_hint(self.board, self.notes, self.wrong_cells())" in game_source


def test_hint_view_reads_cells_from_rules_and_pending_actions_from_hint():
    modules = imported_modules(PACKAGE / "sudoku_hint_view.py")
    source = (PACKAGE / "sudoku_hint_view.py").read_text(encoding="utf-8")
    assert "shudu.sudoku_rules" in modules
    assert "hint.pending_eliminations" in source
    assert "view.game.notes.get(cell)" in source
    assert "hint.step.eliminations" not in source
    assert "use_visible_candidates" not in source


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
    source = (PACKAGE / "logic_solver" / "_project.py").read_text(encoding="utf-8")
    assert "self._last_sources" in source
    assert "self._last_units" in source
    assert "LogicStep(" in source


def test_logic_solver_root_adapter_keeps_legacy_class_identity():
    source = (ROOT / "logical_solver.py").read_text(encoding="utf-8")
    assert "class LogicSolver(NumbaLogicSolver):" in source
    assert "    pass" in source
    assert "from shudu.logic_solver import NumbaLogicSolver" in source


def test_legacy_solver_runtime_identity_stays_at_root_adapter():
    from logical_solver import LogicSolver
    from shudu.logic_solver import NumbaLogicSolver

    assert LogicSolver.__module__ == "logical_solver"
    assert issubclass(LogicSolver, NumbaLogicSolver)
    assert LogicSolver([[0] * 9 for _ in range(9)]).__class__ is LogicSolver


def test_logic_solver_module_owns_moved_implementation_files():
    assert (PACKAGE / "logic_solver" / "__init__.py").is_file()
    assert (PACKAGE / "logic_solver" / "_engine.py").is_file()
    assert (PACKAGE / "logic_solver" / "_project.py").is_file()
    assert (PACKAGE / "logic_solver" / "_results.py").is_file()
    assert not (PACKAGE / "sudoku_logic.py").exists()
    assert not (PACKAGE / "sudoku_step.py").exists()


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


def test_auto_technique_catalog_is_internal_single_source():
    game_source = (PACKAGE / "sudoku_game.py").read_text(encoding="utf-8")
    solver_source = (ROOT / "shudu_solver.py").read_text(encoding="utf-8")
    assert "AUTO_TECHNIQUE_SPECS = (" not in game_source
    assert "AUTO_TECHNIQUE_SPECS = (" not in solver_source
    assert "shudu.auto_techniques" in imported_modules(PACKAGE / "sudoku_game.py")
    assert "shudu.auto_techniques" in imported_modules(ROOT / "shudu_solver.py")


def test_user_settings_io_stays_out_of_game_and_view():
    settings_modules = imported_modules(PACKAGE / "user_settings.py")
    forbidden = {
        "sudoku_gui",
        "shudu.sudoku_game",
        "shudu.sudoku_view",
        "tkinter",
        "shudu_solver",
    }
    assert settings_modules.isdisjoint(forbidden)
    assert "shudu.auto_techniques" in settings_modules
    assert "shudu.user_settings" not in imported_modules(PACKAGE / "sudoku_game.py")
    assert "shudu.user_settings" not in imported_modules(PACKAGE / "sudoku_view.py")


def test_gui_owns_settings_lifecycle_through_store_interface():
    modules = imported_modules(ROOT / "sudoku_gui.py")
    source = (ROOT / "sudoku_gui.py").read_text(encoding="utf-8")
    assert "shudu.user_settings" in modules
    assert "UserSettingsStore" in source
    assert ".settings_store.save(" in source


def test_settings_menu_has_one_public_entry_and_keeps_game_io_outside():
    source = (PACKAGE / "settings_menu" / "__init__.py").read_text(encoding="utf-8")
    modules = imported_modules(PACKAGE / "settings_menu" / "__init__.py")
    assert "shudu.sudoku_game" not in modules
    assert "shudu.user_settings" not in modules
    assert "open_settings" in source
    assert "SettingsMenuState" in source


def test_completion_animation_is_view_only():
    game_source = (PACKAGE / "sudoku_game.py").read_text(encoding="utf-8")
    view_source = (PACKAGE / "sudoku_view.py").read_text(encoding="utf-8")
    assert "after(" not in game_source
    assert "animate_completed_units" in view_source
    assert "completed_units" in game_source
