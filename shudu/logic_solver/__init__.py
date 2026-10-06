"""逻辑求解 deep Module 的唯一公开入口。"""

from ._engine import NumbaLogicSolver
from ._project import ShuduSolver
from ._results import (
    AutoSolveResult,
    CandidatesSnapshot,
    Change,
    LogicStep,
    SimpleSolveResult,
    capture_candidates,
    step_changes,
)

__all__ = (
    "AutoSolveResult",
    "CandidatesSnapshot",
    "Change",
    "LogicStep",
    "NumbaLogicSolver",
    "ShuduSolver",
    "SimpleSolveResult",
    "capture_candidates",
    "solve_auto",
    "step_changes",
)


def solve_auto(board, names, proven_eliminations) -> AutoSolveResult:
    """按需加载自动 capability，保持公开结果合同。"""
    from ._auto import solve_auto as _solve_auto

    return _solve_auto(board, names, proven_eliminations)
