"""定义逻辑求解器的一步结构化结果。
动作来自既有技巧实际产生的棋盘与候选差异。
依据格和观察单位由技巧直接提供，不解析日志猜测。
结果使用不可变对象，供只读提示界面安全引用。
"""

from dataclasses import dataclass

Cell = tuple[int, int]
Change = tuple[int, int, int]
Candidates = tuple[tuple[frozenset[int], ...], ...]


@dataclass(frozen=True)
class LogicStep:
    message: str
    placements: tuple[Change, ...]
    eliminations: tuple[Change, ...]
    sources: tuple[Cell, ...]
    units: tuple[tuple[Cell, ...], ...]
    candidates: Candidates

    @property
    def name(self) -> str:
        result = self.message.partition(":")[0]
        return result


def capture_candidates(candidates) -> Candidates:
    result = tuple(tuple(frozenset(values) for values in row) for row in candidates)
    return result


def step_changes(before, after, candidates, remaining) -> tuple:
    """填数步骤不把其附带的约束传播重复展示成删除笔记步骤。"""
    placements = tuple((r, c, after[r][c]) for r in range(9) for c in range(9)
                       if before[r][c] != after[r][c])
    eliminations = ()
    if not placements:
        eliminations = tuple((r, c, n) for r in range(9) for c in range(9)
                             for n in sorted(candidates[r][c] - remaining[r][c]))
    result = (placements, eliminations)
    return result
