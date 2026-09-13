"""把 solver 的结构化一步结果转换为只读提示。
手工笔记只用于跳过玩家已经完成的合法排除，不作为算法推理约束。
算法依据格和观察区域由 LogicStep 直接携带，本层不重新识别任何数独模式。
本层只负责标题、自然语言说明和统一视觉语义。
"""

from __future__ import annotations

from dataclasses import dataclass

from shudu_solver import ShuduSolver
from shudu.sudoku_rules import CELLS, Cell, unit_name
from shudu.sudoku_step import LogicStep

NAMES = {
    "Naked Single": "唯一候选数",
    "Hidden Single": "排除法 · 隐性唯一数",
    "Naked Pair": "显性数对",
    "Hidden Pair": "隐性数对",
    "Naked Triple": "显性三数组",
    "Pointing Pair": "宫指向行列",
    "Box-Line": "行列指向宫",
    "X-Wing": "X-Wing",
    "XY-Wing": "XY-Wing",
}
MAX_LOGIC_TRANSITIONS = len(CELLS) * 9


@dataclass(frozen=True)
class Hint:
    title: str
    message: str
    step: LogicStep | None = None
    sources: frozenset[Cell] = frozenset()
    units: tuple[tuple[Cell, ...], ...] = ()
    regions: frozenset[Cell] = frozenset()
    attention: frozenset[Cell] = frozenset()

    @property
    def targets(self) -> frozenset[Cell]:
        changes = () if self.step is None else self.step.placements + self.step.eliminations
        result = frozenset((row, col) for row, col, _ in changes)
        return result


def already_noted(step: LogicStep, notes: dict[Cell, set[int]]) -> bool:
    result = bool(step.eliminations) and all(
        bool(notes.get((row, col))) and digit not in notes[(row, col)]
        for row, col, digit in step.eliminations
    )
    return result


def pending_step(board, notes: dict[Cell, set[int]]) -> LogicStep | None:
    solver = ShuduSolver(board)
    result = None
    for _ in range(MAX_LOGIC_TRANSITIONS):
        result = solver.next_step()
        if result is None or not already_noted(result, notes):
            break
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
    regions = _focus_regions(sources, units, step)
    result = Hint(
        NAMES.get(step.name, step.name),
        step_message(step, units, sources),
        step,
        sources,
        units,
        regions,
    )
    return result


def hint_context(board, step: LogicStep) -> tuple[frozenset[Cell], tuple[tuple[Cell, ...], ...]]:
    """直接使用 solver 产出的证据；board 参数仅为兼容既有调用。"""
    result = (frozenset(step.sources), step.units)
    return result


def _focus_regions(sources, units, step: LogicStep) -> frozenset[Cell]:
    cells = set(sources) | set(_target_cells(step))
    for unit in units:
        cells.update(unit)
    result = frozenset(cells)
    return result


def _target_cells(step: LogicStep) -> frozenset[Cell]:
    changes = step.placements + step.eliminations
    result = frozenset((row, col) for row, col, _ in changes)
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
    elif step.name == "Hidden Pair":
        result = _hidden_pair_message(step, units, sources)
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


def _hidden_pair_message(step: LogicStep, units, sources) -> str:
    digits = _remaining_source_digits(step, sources)
    area = unit_name(units[0]) if units else "区域"
    result = f"观察蓝框标出的{area}。数字 {digits} 只可能出现在绿色两格，因此这两格只能保留这两个数字，红色的其他候选可删除。"
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
