"""S1-02 fresh-process lazy capability import probe."""

import subprocess
import sys

ROOT = r"D:\Tony\Documents\invest2026\projects\shudu\.worktrees\S1-02"
PROBE = r"""
import json
import sys

import shudu.logic_solver as public


def loaded():
    return {
        "single": "shudu.logic_solver._single" in sys.modules,
        "evidence": "shudu.logic_solver._evidence" in sys.modules,
    }


before = loaded()
from shudu.logic_solver import ShuduSolver

legacy_solver = ShuduSolver([[0] * 9 for _ in range(9)])
legacy_solver.solve_techniques_result(("hidden_triple",))
after_legacy = loaded()
from shudu.sudoku_game import Game

step = public.next_hint_step(Game().board, {})
after_single = loaded()
print(
    json.dumps(
        {
            "before_public_call": before,
            "after_legacy_auto": after_legacy,
            "step": step.technique_name if step is not None else None,
            "after_single_capability": after_single,
        },
        ensure_ascii=False,
    )
)
"""

completed = subprocess.run(
    [sys.executable, "-c", PROBE],
    cwd=ROOT,
    capture_output=True,
    text=True,
    check=False,
)
if completed.returncode:
    raise SystemExit(completed.stderr)
print(completed.stdout, end="")
