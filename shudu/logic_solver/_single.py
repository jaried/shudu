"""单步逻辑提示 capability。"""

from ._project import ShuduSolver
from ._results import LogicStep


def next_hint_step(board, notes) -> LogicStep | None:
    """在当前 board 和已有 notes 上返回项目优先级的第一步。"""
    solver = ShuduSolver(board)
    candidates = solver.algorithm_candidates()
    if notes:
        eliminations = tuple(
            (row, col, digit)
            for (row, col), visible in notes.items()
            if not solver.board[row][col] and visible
            for digit in candidates[row][col]
            if digit not in visible
        )
        solver.apply_candidate_eliminations(eliminations)
    return solver.next_step()
