"""把既有逻辑求解器的一步结果转换为只读提示。
手工笔记不是推理约束，只用于识别已手动完成的合法排除。
所有试演都在求解器副本中进行，不填写或删除玩家的内容。
没有逻辑步骤时明确说明，不用答案或回溯伪装推理。
"""

from __future__ import annotations

from dataclasses import dataclass

from logical_solver import LogicSolver, box_cells, col_cells, row_cells, unit_name
from sudoku_step import Cell, LogicStep, capture_candidates, step_changes

CELLS = tuple((r, c) for r in range(9) for c in range(9))
NAMES = {
    "Naked Single": "唯一候选数", "Hidden Single": "排除法 · 隐性唯一数",
    "Naked Pair": "显性数对", "Hidden Pair": "隐性数对",
    "Naked Triple": "显性三数组", "Pointing Pair": "宫指向行列",
    "Box-Line": "行列指向宫", "X-Wing": "X-Wing", "XY-Wing": "XY-Wing",
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
        result = frozenset((r, c) for r, c, _ in changes)
        return result


def shares_unit(a: Cell, b: Cell) -> bool:
    result = a[0] == b[0] or a[1] == b[1] or (a[0] // 3, a[1] // 3) == (b[0] // 3, b[1] // 3)
    return result


def already_noted(step: LogicStep, notes: dict[Cell, set[int]]) -> bool:
    result = bool(step.eliminations) and all(
        bool(notes.get((r, c))) and digit not in notes[(r, c)]
        for r, c, digit in step.eliminations
    )
    return result


def _message(solver: LogicSolver) -> str:
    result = solver.steps[-1].split("] ", 1)[-1] if solver.steps else ""
    return result


def _placement_units(placements) -> tuple[tuple[Cell, ...], ...]:
    result = ()
    if placements:
        r, c, _ = placements[0]
        result = (tuple(row_cells(r)), tuple(col_cells(c)), tuple(box_cells(r, c)))
    return result


def _solver_step(solver: LogicSolver) -> LogicStep | None:
    before = [row[:] for row in solver.board]
    candidates = capture_candidates(solver.cands)
    result = None
    if solver._apply_next_step():
        placements, eliminations = step_changes(before, solver.board, candidates, solver.cands)
        result = LogicStep(_message(solver), placements, eliminations, (),
                           _placement_units(placements), candidates)
    return result


def pending_step(board, notes: dict[Cell, set[int]]) -> LogicStep | None:
    solver = LogicSolver(board)
    result = None
    for _ in range(729):
        result = _solver_step(solver)
        if result is None or not already_noted(result, notes):
            break
    return result


def make_hint(board, notes: dict[Cell, set[int]], wrong: set[Cell]) -> Hint:
    if wrong:
        result = Hint("请先修正错误", "红色格中的正式数字有误。先擦除或修正，再查看逻辑提示。", attention=frozenset(wrong))
    else:
        step = pending_step(board, notes)
        result = Hint("暂无逻辑提示", "现有逻辑技巧暂时找不到下一步。没有自动填数，也没有使用回溯答案。")
        if step is not None:
            result = describe_step(board, step)
    return result


def focus_units(step: LogicStep) -> tuple[tuple[Cell, ...], ...]:
    result = step.units
    if step.placements and step.name == "Hidden Single":
        r, c, digit = step.placements[0]
        preferred = (tuple(box_cells(r, c)), tuple(row_cells(r)), tuple(col_cells(c)))
        matching = tuple(unit for unit in preferred
                         if sum(digit in step.candidates[i][j] for i, j in unit) == 1)
        result = matching[:1] or result
    return result


def single_sources(board, step: LogicStep, units) -> frozenset[Cell]:
    r, c, digit = step.placements[0]
    sources = {cell for cell in CELLS if board[cell[0]][cell[1]] and shares_unit((r, c), cell)}
    if step.name == "Hidden Single" and units:
        others = {cell for cell in units[0] if cell != (r, c) and not board[cell[0]][cell[1]]}
        sources = {cell for cell in CELLS if board[cell[0]][cell[1]] == digit
                   and any(shares_unit(cell, other) for other in others)}
    result = frozenset(sources)
    return result


def evidence_regions(board, sources, units) -> frozenset[Cell]:
    result = {cell for unit in units for cell in unit} | set(sources)
    empty = [cell for unit in units for cell in unit if not board[cell[0]][cell[1]]]
    for source in sources:
        result.update(source_regions(source, empty))
    frozen = frozenset(result)
    return frozen


def source_regions(source, empty) -> set[Cell]:
    result = set()
    for unit in (row_cells(source[0]), col_cells(source[1]), box_cells(*source)):
        if any(cell in unit for cell in empty):
            result.update(unit)
    return result


def step_message(step: LogicStep, units) -> str:
    result = step.message.partition(": ")[2] or step.message
    if step.placements:
        r, c, digit = step.placements[0]
        position = f"第 {r + 1} 行第 {c + 1} 列"
        if step.name == "Hidden Single" and units:
            result = f"观察蓝框标出的{unit_name(list(units[0]))}。数字 {digit} 只在{position}保留为候选，因此该格可填 {digit}。"
        else:
            result = f"{position}结合同行、同列、同宫的限制后，只剩候选数 {digit}，因此可填 {digit}。"
    return result


def describe_step(board, step: LogicStep) -> Hint:
    units = focus_units(step)
    sources = frozenset(step.sources)
    if step.placements:
        sources = single_sources(board, step, units)
    result = Hint(NAMES.get(step.name, step.name), step_message(step, units), step,
                  sources, units, evidence_regions(board, sources, units))
    return result
