"""把项目级求解器的一步结果转换为只读提示。
手工笔记不是推理约束，只用于识别已手动完成的合法排除。
所有试演都在求解器副本中进行，不填写或删除玩家的内容。
提示层只依赖 ShuduSolver 公共一步 API 与共享数独规则。
"""

from __future__ import annotations

from dataclasses import dataclass

from shudu_solver import ShuduSolver
from sudoku_rules import CELLS, UNITS, Cell, box_cells, col_cells, row_cells, unit_name
from sudoku_step import LogicStep

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
    for _ in range(729):
        result = solver.next_step()
        if result is None or not already_noted(result, notes):
            break
    return _with_sources(result)


def _with_sources(step: LogicStep | None) -> LogicStep | None:
    result = step
    if step is not None and step.name == "Naked Pair" and not step.sources:
        sources = _naked_pair_sources(step.candidates, step.eliminations)
        result = LogicStep(
            step.message,
            step.placements,
            step.eliminations,
            sources,
            step.units,
            step.candidates,
        )
    return result


def _naked_pair_sources(candidates, eliminations) -> tuple[Cell, ...]:
    digits = {digit for _, _, digit in eliminations}
    targets = {(row, col) for row, col, _ in eliminations}
    result = ()
    for unit in UNITS:
        if targets and targets <= set(unit):
            sources = tuple(cell for cell in unit if set(candidates[cell[0]][cell[1]]) == digits)
            if len(sources) == 2:
                result = sources
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


def focus_units(step: LogicStep) -> tuple[tuple[Cell, ...], ...]:
    result = step.units
    if step.placements and step.name == "Hidden Single":
        result = _hidden_single_unit(step)
    return result


def _hidden_single_unit(step: LogicStep) -> tuple[tuple[Cell, ...], ...]:
    row, col, digit = step.placements[0]
    preferred = (box_cells(row, col), row_cells(row), col_cells(col))
    matching = tuple(
        unit
        for unit in preferred
        if sum(digit in step.candidates[item_row][item_col] for item_row, item_col in unit) == 1
    )
    result = matching[:1] or step.units
    return result


def single_sources(board, step: LogicStep, units) -> frozenset[Cell]:
    row, col, digit = step.placements[0]
    sources = {cell for cell in CELLS if board[cell[0]][cell[1]] and _shares_unit((row, col), cell)}
    if step.name == "Hidden Single" and units:
        sources = _hidden_single_sources(board, units[0], (row, col), digit)
    result = frozenset(sources)
    return result


def _hidden_single_sources(board, unit, target: Cell, digit: int) -> set[Cell]:
    empty_others = {cell for cell in unit if cell != target and not board[cell[0]][cell[1]]}
    result = {
        cell
        for cell in CELLS
        if board[cell[0]][cell[1]] == digit
        and any(_shares_unit(cell, other) for other in empty_others)
    }
    return result


def _shares_unit(first: Cell, second: Cell) -> bool:
    row, col = first
    other_row, other_col = second
    result = row == other_row or col == other_col or (row // 3, col // 3) == (other_row // 3, other_col // 3)
    return result


def evidence_regions(board, sources, units) -> frozenset[Cell]:
    result = {cell for unit in units for cell in unit} | set(sources)
    empty = [cell for unit in units for cell in unit if not board[cell[0]][cell[1]]]
    for source in sources:
        result.update(_source_regions(source, empty))
    frozen = frozenset(result)
    return frozen


def _source_regions(source: Cell, empty) -> set[Cell]:
    result = set()
    for unit in (row_cells(source[0]), col_cells(source[1]), box_cells(*source)):
        if any(cell in unit for cell in empty):
            result.update(unit)
    return result


def step_message(step: LogicStep, units) -> str:
    result = step.message.partition(": ")[2] or step.message
    if step.placements:
        result = _placement_message(step, units)
    return result


def _placement_message(step: LogicStep, units) -> str:
    row, col, digit = step.placements[0]
    position = f"第 {row + 1} 行第 {col + 1} 列"
    result = f"{position}结合同行、同列、同宫的限制后，只剩候选数 {digit}，因此可填 {digit}。"
    if step.name == "Hidden Single" and units:
        result = (
            f"观察蓝框标出的{unit_name(units[0])}。数字 {digit} 只在{position}保留为候选，"
            f"因此该格可填 {digit}。"
        )
    return result


def describe_step(board, step: LogicStep) -> Hint:
    units = focus_units(step)
    sources = frozenset(step.sources)
    if step.placements:
        sources = single_sources(board, step, units)
    result = Hint(
        NAMES.get(step.name, step.name),
        step_message(step, units),
        step,
        sources,
        units,
        evidence_regions(board, sources, units),
    )
    return result
