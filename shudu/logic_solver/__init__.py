"""逻辑求解 deep Module 的唯一公开入口。"""

from ._auto import solve_auto
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
