"""逻辑求解 deep Module 的唯一公开入口。"""

from ._engine import NumbaLogicSolver
from ._project import ShuduSolver
from ._results import (
    CandidatesSnapshot,
    Change,
    LogicStep,
    SimpleSolveResult,
    capture_candidates,
    step_changes,
)
from ._single import next_hint_step

__all__ = (
    "CandidatesSnapshot",
    "Change",
    "LogicStep",
    "NumbaLogicSolver",
    "ShuduSolver",
    "SimpleSolveResult",
    "capture_candidates",
    "next_hint_step",
    "step_changes",
)
