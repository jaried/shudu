"""把 codebase design 的依赖方向固化为可执行回归。"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def imported_modules(name: str) -> set[str]:
    tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_rules_layer_has_no_upper_layer_dependencies():
    forbidden = {"logical_solver", "shudu_solver", "sudoku_hints", "sudoku_game", "sudoku_view", "sudoku_gui"}
    assert imported_modules("sudoku_rules.py").isdisjoint(forbidden)


def test_game_does_not_depend_on_legacy_logic_implementation():
    assert "logical_solver" not in imported_modules("sudoku_game.py")


def test_hint_adapter_depends_on_project_solver_not_legacy_solver():
    modules = imported_modules("sudoku_hints.py")
    assert "shudu_solver" in modules
    assert "logical_solver" not in modules


def test_hint_adapter_does_not_call_private_solver_step_api():
    source = (ROOT / "sudoku_hints.py").read_text(encoding="utf-8")
    assert "._apply_next_step(" not in source
