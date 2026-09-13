"""定义逻辑求解器的一步结构化结果。
动作来自求解器实际产生的棋盘与候选差异。
结果使用不可变对象，供只读提示界面安全引用。
共享坐标类型来自 sudoku_rules，避免重复定义领域概念。
"""

from dataclasses import dataclass

from sudoku_rules import Cell

Change = tuple[int, int, int]
CandidatesSnapshot = tuple[tuple[frozenset[int], ...], ...]


@dataclass(frozen=True)
class LogicStep:
    message: str
    placements: tuple[Change, ...]
    eliminations: tuple[Change, ...]
    sources: tuple[Cell, ...]
    units: tuple[tuple[Cell, ...], ...]
    candidates: CandidatesSnapshot

    @property
    def name(self) -> str:
        result = self.message.partition(":")[0]
        return result


def capture_candidates(candidates) -> CandidatesSnapshot:
    result = tuple(tuple(frozenset(values) for values in row) for row in candidates)
    return result


def step_changes(before, after, candidates, remaining) -> tuple:
    """填数步骤不把附带的约束传播重复展示成删除笔记步骤。"""
    placements = tuple(
        (row, col, after[row][col])
        for row in range(9)
        for col in range(9)
        if before[row][col] != after[row][col]
    )
    eliminations = ()
    if not placements:
        eliminations = tuple(
            (row, col, digit)
            for row in range(9)
            for col in range(9)
            for digit in sorted(candidates[row][col] - remaining[row][col])
        )
    result = (placements, eliminations)
    return result
