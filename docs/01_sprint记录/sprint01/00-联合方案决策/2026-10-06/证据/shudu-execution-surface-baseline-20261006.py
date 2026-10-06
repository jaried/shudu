"""记录当前仓库 capability 的实际调用计数，仅生成草案证据。"""
import json
import sys
from collections import Counter
from contextlib import ExitStack
from unittest.mock import patch

ROOT = r"D:\Tony\Documents\invest2026\projects\shudu"
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + r"\tests")
import conftest  # 复用当前测试别名。
import shudu.logic_solver._engine as logic
import shudu.sudoku_hints as hints
import shudu_solver as project
from shudu.auto_techniques import AUTO_TECHNIQUE_NAMES
from shudu.sudoku_game import Game
from test_auto_simple import AUTO_NOTES_PUZZLE
from test_sudoku_hints import LEVEL119_PUZZLE, SCREENSHOT_NOTES

results = []


def record(name, action):
    counts = Counter()
    shapes = set()
    def tracked(label, original):
        def call(*args, **kwargs):
            counts[label] += 1
            for value in args:
                if hasattr(value, "shape"):
                    shapes.add(tuple(value.shape))
            return original(*args, **kwargs)
        return call
    with ExitStack() as stack:
        for attr in ("candidate_sets", "masks_from_board", "apply_placement", "find_hidden_single",
                     "find_naked_single", "find_naked_pair", "find_hidden_pair", "find_naked_triple",
                     "find_hidden_triple", "find_pointing_pair", "find_box_line", "find_x_wing", "find_xy_wing"):
            stack.enter_context(patch.object(logic, attr, tracked(attr, getattr(logic, attr))))
        stack.enter_context(patch.object(project, "capture_candidates", tracked("capture_candidates", project.capture_candidates)))
        stack.enter_context(patch.object(logic.NumbaLogicSolver, "_hidden_single_sources", tracked("base_hidden_single_evidence", logic.NumbaLogicSolver._hidden_single_sources)))
        stack.enter_context(patch.object(project.ShuduSolver, "_hidden_single_evidence", tracked("project_hidden_single_evidence", project.ShuduSolver._hidden_single_evidence)))
        stack.enter_context(patch.object(project.ShuduSolver, "next_step", tracked("next_step", project.ShuduSolver.next_step)))
        outcome = action()
    results.append({"scenario": name, "calls": dict(sorted(counts.items())), "array_shapes": sorted(shapes), "outcome": outcome})


def auto_stalled(names):
    solver = project.ShuduSolver([[0] * 9 for _ in range(9)])
    result = solver.solve_techniques_result(names)
    return {"placements": result.placements, "eliminations": len(result.eliminations)}


record("auto_stalled_all_ten", lambda: auto_stalled(AUTO_TECHNIQUE_NAMES))
record("auto_stalled_hidden_triple_only", lambda: auto_stalled({"hidden_triple"}))
record("hint_stalled_without_notes", lambda: str(hints.pending_step([[0] * 9 for _ in range(9)], {})))
record("hint_hidden_triple_existing_notes", lambda: hints.pending_step(LEVEL119_PUZZLE.grid(), SCREENSHOT_NOTES).name)
record("hint_hidden_single_without_notes", lambda: hints.pending_step(AUTO_NOTES_PUZZLE.grid(), {}).name)
record("wrong_board_warning", lambda: hints.make_hint(AUTO_NOTES_PUZZLE.grid(), {}, {(0, 0)}).title)
disabled = Game(AUTO_NOTES_PUZZLE, auto_techniques=AUTO_TECHNIQUE_NAMES, auto_solve=False)
record("auto_master_disabled_after_game_creation", lambda: disabled.auto_solve_enabled())

import tkinter as tk
from sudoku_gui import SudokuWindow


class CountingStore:
    def __init__(self):
        self.calls = 0
    def save(self, settings):
        self.calls += 1


root = tk.Tk()
root.withdraw()
store = CountingStore()
window = SudokuWindow(root, Game(auto_solve=False), settings_store=store)
window._popup = lambda menu: None
window.show_settings()
menu_counts = Counter()
try:
    with ExitStack() as stack:
        for target, attr, label in ((window.game, "completed_units", "completed_units"),
                                    (window.view, "draw", "full_view_draw"),
                                    (window.view, "animate_completed_units", "animate_completed_units")):
            original = getattr(target, attr)
            def tracked_menu(*args, original=original, label=label, **kwargs):
                menu_counts[label] += 1
                return original(*args, **kwargs)
            stack.enter_context(patch.object(target, attr, tracked_menu))
        window._auto_technique_vars["hidden_triple"].set(True)
        window._set_auto_technique("hidden_triple")
    results.append({"scenario": "one_technique_setting_toggle", "calls": {**dict(menu_counts), "settings_save": store.calls}, "outcome": "configuration_only"})
finally:
    window.close()

print(json.dumps({"observations": results, "measurement": "call_counts_and_input_shapes", "timing": "not_measured"}, ensure_ascii=False, indent=2))
