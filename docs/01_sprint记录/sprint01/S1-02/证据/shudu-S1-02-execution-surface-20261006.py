"""S1-02 implementation execution-surface probe on fixed board/notes fixtures."""

import copy
import json
import sys
from collections import Counter
from contextlib import ExitStack
from unittest.mock import patch

ROOT = r"D:\Tony\Documents\invest2026\projects\shudu\.worktrees\S1-02"
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + r"\tests")

import conftest  # noqa: F401  # test-only historical import aliases
from test_auto_simple import AUTO_NOTES_PUZZLE
from test_sudoku_hints import LEVEL119_PUZZLE, SCREENSHOT_NOTES

import shudu.logic_solver._engine as engine
import shudu.logic_solver._evidence as evidence
import shudu.logic_solver._project as project
from shudu.auto_techniques import AUTO_TECHNIQUE_NAMES
from shudu.logic_solver import ShuduSolver, next_hint_step
from shudu.sudoku_hints import make_hint

FIELDS = (
    "candidate_sets",
    "masks_from_board",
    "apply_placement",
    "find_hidden_single",
    "find_naked_single",
    "find_naked_pair",
    "find_hidden_pair",
    "find_naked_triple",
    "find_hidden_triple",
    "find_pointing_pair",
    "find_box_line",
    "find_x_wing",
    "find_xy_wing",
)


def tracked(label, counts, shapes, original):
    def call(*args, **kwargs):
        counts[label] += 1
        for value in args:
            if hasattr(value, "shape"):
                shapes.add(tuple(value.shape))
        return original(*args, **kwargs)

    return call


def record(name, action):
    counts = Counter()
    shapes = set()
    with ExitStack() as stack:
        for attr in FIELDS:
            stack.enter_context(
                patch.object(
                    engine, attr, tracked(attr, counts, shapes, getattr(engine, attr))
                )
            )
        stack.enter_context(
            patch.object(
                project,
                "capture_candidates",
                tracked(
                    "capture_candidates", counts, shapes, project.capture_candidates
                ),
            )
        )
        stack.enter_context(
            patch.object(
                project.ShuduSolver,
                "next_step",
                tracked("next_step", counts, shapes, project.ShuduSolver.next_step),
            )
        )
        stack.enter_context(
            patch.object(
                evidence,
                "hidden_single_evidence",
                tracked(
                    "project_hidden_single_evidence",
                    counts,
                    shapes,
                    evidence.hidden_single_evidence,
                ),
            )
        )
        outcome = action(counts)
    return {
        "scenario": name,
        "calls": dict(sorted(counts.items())),
        "array_shapes": sorted(shapes),
        "outcome": outcome,
    }


def hint_stalled(counts):
    return str(next_hint_step([[0] * 9 for _ in range(9)], {}))


def auto_stalled_all_ten(counts):
    result = ShuduSolver([[0] * 9 for _ in range(9)]).solve_techniques_result(
        AUTO_TECHNIQUE_NAMES
    )
    return {"placements": result.placements, "eliminations": len(result.eliminations)}


def auto_stalled_hidden_triple_only(counts):
    result = ShuduSolver([[0] * 9 for _ in range(9)]).solve_techniques_result(
        ("hidden_triple",)
    )
    return {"placements": result.placements, "eliminations": len(result.eliminations)}


def hint_hidden_triple(counts):
    return next_hint_step(LEVEL119_PUZZLE.grid(), copy.deepcopy(SCREENSHOT_NOTES)).name


def hint_hidden_single(counts):
    return next_hint_step(AUTO_NOTES_PUZZLE.grid(), {}).name


def wrong_board(counts):
    return make_hint(AUTO_NOTES_PUZZLE.grid(), {}, {(0, 0)}).title


def exception_probe(counts):
    def fail(*args, **kwargs):
        counts["find_hidden_single"] += 1
        raise RuntimeError("implementation_probe_exception")

    with patch.object(engine, "find_hidden_single", fail):
        try:
            next_hint_step([[0] * 9 for _ in range(9)], {})
        except RuntimeError as error:
            return {"exception_type": type(error).__name__, "message": str(error)}
    raise AssertionError("injected exception did not propagate")


results = [
    record("auto_stalled_all_ten", auto_stalled_all_ten),
    record("auto_stalled_hidden_triple_only", auto_stalled_hidden_triple_only),
    record("hint_stalled_without_notes", hint_stalled),
    record("hint_hidden_triple_existing_notes", hint_hidden_triple),
    record("hint_hidden_single_without_notes", hint_hidden_single),
    record("wrong_board_warning", wrong_board),
    record("hint_exception_fixed_empty_board", exception_probe),
]
print(
    json.dumps(
        {"observations": results, "measurement": "call_counts_and_input_shapes"},
        ensure_ascii=False,
        indent=2,
    )
)
