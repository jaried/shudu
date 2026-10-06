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


def next_hint_step(board, notes) -> LogicStep | None:
    """按需加载单步 capability，返回当前 board/notes 的第一条步骤。"""
    from ._single import next_hint_step as _next_hint_step

    result = _next_hint_step(board, notes)
    return result


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
