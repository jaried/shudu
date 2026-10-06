"""自动完整结果 capability 的内部编排。"""

from ._project import ShuduSolver
from ._results import AutoSolveResult


def solve_auto(board, names, proven_eliminations) -> AutoSolveResult:
    """按显式勾选集合推进固定点并转移一次完整结果。"""
    solver = ShuduSolver(board)
    solver.apply_candidate_eliminations(proven_eliminations)
    result = solver.solve_techniques_result(names)
    candidates = solver.algorithm_candidates()
    notes = {
        (row, col): set(candidates[row][col])
        for row in range(9)
        for col in range(9)
        if not solver.board[row][col] and candidates[row][col]
    }
    return AutoSolveResult(solver.board, notes, result.placements, result.eliminations)
