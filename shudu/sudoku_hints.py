"""把 solver 的结构化一步结果转换为只读提示。
提示固定使用全部逻辑算法，不读取自动算法配置。
每个已有笔记格都作为该格当前候选状态投影到 solver；没有笔记的格继续使用 solver 基础候选。
算法依据格和观察区域由 LogicStep 直接携带，本层不重新识别任何数独模式。
"""

from __future__ import annotations

from dataclasses import dataclass

from shudu.sudoku_rules import Cell, unit_name
from shudu.logic_solver import Change, LogicStep, ShuduSolver

NAMES = {
    "Naked Single": "唯一候选数",
    "Hidden Single": "排除法 · 隐性唯一数",
    "Naked Pair": "显性数对",
    "Hidden Pair": "隐性数对",
    "Naked Triple": "显性三数组",
    "Hidden Triple": "隐性三数组",
    "Pointing Pair": "宫指向行列",
    "Box-Line": "行列指向宫",
    "X-Wing": "X-Wing",
    "XY-Wing": "XY-Wing",
}


@dataclass(frozen=True)
class Hint:
    title: str
    message: str
    step: LogicStep | None = None
    sources: frozenset[Cell] = frozenset()
    units: tuple[tuple[Cell, ...], ...] = ()
    regions: frozenset[Cell] = frozenset()
    attention: frozenset[Cell] = frozenset()
    pending_eliminations: tuple[Change, ...] = ()

    @property
    def targets(self) -> frozenset[Cell]:
        changes = ()
        if self.step is not None:
            changes = self.step.placements or self.pending_eliminations
        result = frozenset((row, col) for row, col, _ in changes)
        return result


def _apply_candidate_notes(solver: ShuduSolver, notes: dict[Cell, set[int]]) -> None:
    """已有笔记格以可见候选为准；没有笔记的空格保留 solver 基础候选。"""
    candidates = solver.algorithm_candidates()
    eliminations = tuple(
        (row, col, digit)
        for (row, col), visible in notes.items()
        if not solver.board[row][col] and visible
        for digit in candidates[row][col]
        if digit not in visible
    )
    solver.apply_candidate_eliminations(eliminations)


def pending_step(board, notes: dict[Cell, set[int]]) -> LogicStep | None:
    """把现有笔记逐格投影后，按全部算法返回第一条逻辑步骤。"""
    solver = ShuduSolver(board)
    _apply_candidate_notes(solver, notes)
    result = solver.next_step()
    return result


def make_hint(board, notes: dict[Cell, set[int]], wrong: set[Cell]) -> Hint:
    if wrong:
        result = Hint(
            "请先修正错误",
            "红色格中的正式数字有误。先擦除或修正，再查看逻辑提示。",
            attention=frozenset(wrong),
        )
    else:
        result = _logic_hint(board, notes)
    return result


def _logic_hint(board, notes: dict[Cell, set[int]]) -> Hint:
    step = pending_step(board, notes)
    result = Hint(
        "暂无逻辑提示",
        "现有逻辑技巧暂时找不到下一步。没有自动填数，也没有使用回溯答案。",
    )
    if step is not None:
        result = describe_step(board, step)
    return result


def describe_step(board, step: LogicStep) -> Hint:
    sources, units = hint_context(board, step)
    visible_eliminations = step.eliminations
    regions = _focus_regions(sources, units, step, visible_eliminations)
    result = Hint(
        NAMES.get(step.name, step.name),
        step_message(step, units, sources),
        step,
        sources,
        units,
        regions,
        pending_eliminations=visible_eliminations,
    )
    return result


def hint_context(board, step: LogicStep) -> tuple[frozenset[Cell], tuple[tuple[Cell, ...], ...]]:
    """直接使用 solver 产出的证据；board 参数仅为兼容既有调用。"""
    result = (frozenset(step.sources), step.units)
    return result


def _focus_regions(
    sources,
    units,
    step: LogicStep,
    pending_eliminations: tuple[Change, ...],
) -> frozenset[Cell]:
    changes = step.placements or pending_eliminations
    cells = set(sources)
    cells.update((row, col) for row, col, _ in changes)
    for unit in units:
        cells.update(unit)
    result = frozenset(cells)
    return result


def _single_elimination_digit(step: LogicStep) -> int:
    digits = {digit for _, _, digit in step.eliminations}
    result = next(iter(digits)) if len(digits) == 1 else 0
    return result


def _candidates(step: LogicStep, cell: Cell) -> set[int]:
    result = set(step.candidates[cell[0]][cell[1]])
    return result


def _remaining_source_digits(step: LogicStep, sources) -> list[int]:
    removed: dict[Cell, set[int]] = {}
    for row, col, digit in step.eliminations:
        removed.setdefault((row, col), set()).add(digit)
    digits: set[int] = set()
    for cell in sources:
        digits.update(_candidates(step, cell).difference(removed.get(cell, set())))
    result = sorted(digits)
    return result


def step_message(step: LogicStep, units, sources) -> str:
    result = step.message.partition(": ")[2] or step.message
    if step.placements:
        result = _placement_message(step, units)
    elif step.name in ("Naked Pair", "Naked Triple"):
        result = _naked_subset_message(step, units, sources)
    elif step.name in ("Hidden Pair", "Hidden Triple"):
        result = _hidden_subset_message(step, units, sources)
    elif step.name == "Pointing Pair":
        result = _pointing_message(step, units)
    elif step.name == "Box-Line":
        result = _box_line_message(step, units)
    elif step.name == "X-Wing":
        result = _x_wing_message(step)
    elif step.name == "XY-Wing":
        result = _xy_wing_message(step)
    return result


def _placement_message(step: LogicStep, units) -> str:
    row, col, digit = step.placements[0]
    position = f"第 {row + 1} 行第 {col + 1} 列"
    result = f"观察亮起的行、列和宫。{position}只剩候选数 {digit}，因此可填 {digit}。"
    if step.name == "Hidden Single" and units:
        result = f"观察蓝框标出的{unit_name(units[0])}。数字 {digit} 只在{position}保留为候选，因此该格可填 {digit}。"
    return result


def _naked_subset_message(step: LogicStep, units, sources) -> str:
    digits = sorted(set().union(*(_candidates(step, cell) for cell in sources))) if sources else []
    count = "两" if len(sources) == 2 else "三"
    area = unit_name(units[0]) if units else "区域"
    result = f"观察蓝框标出的{area}。绿色{count}格只由候选 {digits} 组成，这些数字必须占据这些格，因此同一区域其他格中的红色候选可删除。"
    return result


def _hidden_subset_message(step: LogicStep, units, sources) -> str:
    digits = _remaining_source_digits(step, sources)
    area = unit_name(units[0]) if units else "区域"
    count = "两" if len(sources) == 2 else "三"
    result = f"观察蓝框标出的{area}。数字 {digits} 只可能出现在绿色{count}格，因此这{count}格只能保留这{count}个数字，红色的其他候选可删除。"
    return result


def _pointing_message(step: LogicStep, units) -> str:
    digit = _single_elimination_digit(step)
    box_name = unit_name(units[0]) if units else "宫"
    line_name = unit_name(units[1]) if len(units) > 1 else "行或列"
    result = f"观察蓝框标出的{box_name}和{line_name}。数字 {digit} 在该宫中只出现在绿色格并全部落在同一行或列，因此宫外的红色 {digit} 可删除。"
    return result


def _box_line_message(step: LogicStep, units) -> str:
    digit = _single_elimination_digit(step)
    line_name = unit_name(units[0]) if units else "行或列"
    box_name = unit_name(units[1]) if len(units) > 1 else "宫"
    result = f"观察蓝框标出的{line_name}和{box_name}。数字 {digit} 在这条行或列中只可能落在该宫，因此宫内其他位置的红色 {digit} 可删除。"
    return result


def _x_wing_message(step: LogicStep) -> str:
    digit = _single_elimination_digit(step)
    result = f"观察亮起的两行和两列。绿色四格构成数字 {digit} 的 X-Wing；两个 {digit} 必须分布在不同的行和列，因此交叉线其他位置的红色 {digit} 可删除。"
    return result


def _xy_wing_message(step: LogicStep) -> str:
    digit = _single_elimination_digit(step)
    result = f"观察绿色的枢纽和两个翼。枢纽的两个候选分别连接两个翼，而两个翼共享候选 {digit}，因此同时看见两个翼的红色 {digit} 可删除。"
    return result
