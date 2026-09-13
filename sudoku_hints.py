"""把项目级求解器的一步结果转换为只读提示。
手工笔记不是推理约束，只用于识别已手动完成的合法排除。
所有技巧都转换成统一的观察区域、依据格和目标格语义。
提示层只依赖 ShuduSolver 公共一步 API 与共享数独规则。
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from shudu_solver import ShuduSolver
from sudoku_rules import (
    BOXES,
    COLS,
    ROWS,
    CELLS,
    UNITS,
    Cell,
    box_cells,
    col_cells,
    related,
    row_cells,
    unit_name,
)
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
    if step.placements:
        units = focus_units(step)
        sources = single_sources(board, step, units)
        return sources, units
    result = _elimination_context(step)
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
    sources = {cell for cell in CELLS if board[cell[0]][cell[1]] and related((row, col), cell)}
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
        and any(related(cell, other) for other in empty_others)
    }
    return result


def _elimination_context(step: LogicStep):
    name = step.name
    result = (frozenset(step.sources), step.units)
    if name == "Naked Pair":
        result = _naked_subset_context(step, 2)
    elif name == "Hidden Pair":
        result = _hidden_pair_context(step)
    elif name == "Naked Triple":
        result = _naked_subset_context(step, 3)
    elif name == "Pointing Pair":
        result = _pointing_context(step)
    elif name == "Box-Line":
        result = _box_line_context(step)
    elif name == "X-Wing":
        result = _x_wing_context(step)
    elif name == "XY-Wing":
        result = _xy_wing_context(step)
    return result


def _naked_subset_context(step: LogicStep, size: int):
    targets = _target_cells(step)
    fallback = (frozenset(step.sources), step.units)
    for unit in UNITS:
        if not targets.intersection(unit):
            continue
        cells = [cell for cell in unit if 1 <= len(_candidates(step, cell)) <= size]
        for group in combinations(cells, size):
            digits = set().union(*(_candidates(step, cell) for cell in group))
            if len(digits) == size and _eliminations_fit(step, unit, group, digits):
                return frozenset(group), (unit,)
    return fallback


def _hidden_pair_context(step: LogicStep):
    targets = _target_cells(step)
    fallback = (frozenset(step.sources), step.units)
    if len(targets) != 2:
        return fallback
    for unit in UNITS:
        if targets <= set(unit) and len(_hidden_pair_digits(step, unit, targets)) >= 2:
            return targets, (unit,)
    return fallback


def _pointing_context(step: LogicStep):
    digit = _single_elimination_digit(step)
    targets = _target_cells(step)
    fallback = (frozenset(step.sources), step.units)
    if digit == 0 or not targets:
        return fallback
    for box in BOXES:
        sources = _digit_cells(step, box, digit)
        line = _single_line(sources)
        if len(sources) >= 2 and line and targets <= set(line).difference(box):
            return frozenset(sources), (box, line)
    return fallback


def _box_line_context(step: LogicStep):
    digit = _single_elimination_digit(step)
    targets = _target_cells(step)
    fallback = (frozenset(step.sources), step.units)
    if digit == 0 or not targets:
        return fallback
    for line in ROWS + COLS:
        sources = _digit_cells(step, line, digit)
        box = _single_box(sources)
        if len(sources) >= 2 and box and targets <= set(box).difference(line):
            return frozenset(sources), (line, box)
    return fallback


def _x_wing_context(step: LogicStep):
    digit = _single_elimination_digit(step)
    fallback = (frozenset(step.sources), step.units)
    if digit == 0:
        return fallback
    result = _x_wing_rows(step, digit)
    if result == fallback:
        result = _x_wing_cols(step, digit)
    return result


def _x_wing_rows(step: LogicStep, digit: int):
    targets = _target_cells(step)
    fallback = (frozenset(step.sources), step.units)
    rows = [(row, tuple(col for col in range(9) if digit in step.candidates[row][col])) for row in range(9)]
    for first, second in combinations(rows, 2):
        if len(first[1]) != 2 or first[1] != second[1]:
            continue
        row_a, row_b = first[0], second[0]
        col_a, col_b = first[1]
        affected = {(row, col) for row in range(9) if row not in (row_a, row_b) for col in (col_a, col_b)}
        if targets and targets <= affected:
            sources = {(row, col) for row in (row_a, row_b) for col in (col_a, col_b)}
            units = (row_cells(row_a), row_cells(row_b), col_cells(col_a), col_cells(col_b))
            return frozenset(sources), units
    return fallback


def _x_wing_cols(step: LogicStep, digit: int):
    targets = _target_cells(step)
    fallback = (frozenset(step.sources), step.units)
    cols = [(col, tuple(row for row in range(9) if digit in step.candidates[row][col])) for col in range(9)]
    for first, second in combinations(cols, 2):
        if len(first[1]) != 2 or first[1] != second[1]:
            continue
        col_a, col_b = first[0], second[0]
        row_a, row_b = first[1]
        affected = {(row, col) for col in range(9) if col not in (col_a, col_b) for row in (row_a, row_b)}
        if targets and targets <= affected:
            sources = {(row, col) for row in (row_a, row_b) for col in (col_a, col_b)}
            units = (col_cells(col_a), col_cells(col_b), row_cells(row_a), row_cells(row_b))
            return frozenset(sources), units
    return fallback


def _xy_wing_context(step: LogicStep):
    digit = _single_elimination_digit(step)
    targets = _target_cells(step)
    fallback = (frozenset(step.sources), step.units)
    pairs = [cell for cell in CELLS if len(_candidates(step, cell)) == 2]
    if digit == 0 or not targets:
        return fallback
    for pivot in pairs:
        result = _xy_wing_for_pivot(step, pivot, digit, targets, pairs)
        if result is not None:
            return result
    return fallback


def _xy_wing_for_pivot(step: LogicStep, pivot: Cell, digit: int, targets, pairs):
    pivot_digits = _candidates(step, pivot)
    if digit in pivot_digits:
        return None
    wings = [cell for cell in pairs if cell != pivot and related(pivot, cell)]
    for wing_a, wing_b in combinations(wings, 2):
        if _valid_xy_wing(step, pivot_digits, wing_a, wing_b, digit, targets):
            units = _dedupe_units((_shared_unit(pivot, wing_a), _shared_unit(pivot, wing_b)))
            return frozenset((pivot, wing_a, wing_b)), units
    return None


def _valid_xy_wing(step: LogicStep, pivot_digits, wing_a: Cell, wing_b: Cell, digit: int, targets) -> bool:
    first = _candidates(step, wing_a)
    second = _candidates(step, wing_b)
    first_link = first.difference({digit})
    second_link = second.difference({digit})
    links_match = first.intersection(second) == {digit} and first_link | second_link == pivot_digits
    distinct = len(first_link) == 1 and len(second_link) == 1 and first_link != second_link
    seen = all(related(target, wing_a) and related(target, wing_b) for target in targets)
    result = digit in first and digit in second and links_match and distinct and seen
    return result


def _shared_unit(first: Cell, second: Cell):
    result = ()
    if first[0] == second[0]:
        result = row_cells(first[0])
    elif first[1] == second[1]:
        result = col_cells(first[1])
    elif first[0] // 3 == second[0] // 3 and first[1] // 3 == second[1] // 3:
        result = box_cells(*first)
    return result


def _dedupe_units(units) -> tuple[tuple[Cell, ...], ...]:
    result = tuple(dict.fromkeys(unit for unit in units if unit))
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


def _digit_cells(step: LogicStep, unit, digit: int) -> set[Cell]:
    result = {cell for cell in unit if digit in step.candidates[cell[0]][cell[1]]}
    return result


def _single_line(cells):
    rows = {row for row, _ in cells}
    cols = {col for _, col in cells}
    result = row_cells(next(iter(rows))) if len(rows) == 1 and rows else ()
    if len(cols) == 1 and cols:
        result = col_cells(next(iter(cols)))
    return result


def _single_box(cells):
    boxes = {(row // 3, col // 3) for row, col in cells}
    result = ()
    if len(boxes) == 1 and boxes:
        box_row, box_col = next(iter(boxes))
        result = box_cells(box_row * 3, box_col * 3)
    return result


def _eliminations_fit(step: LogicStep, unit, sources, digits) -> bool:
    unit_cells = set(unit)
    source_cells = set(sources)
    result = bool(step.eliminations) and all(
        (row, col) in unit_cells and (row, col) not in source_cells and digit in digits
        for row, col, digit in step.eliminations
    )
    return result


def _hidden_pair_digits(step: LogicStep, unit, targets) -> list[int]:
    result = []
    for digit in range(1, 10):
        positions = _digit_cells(step, unit, digit)
        if positions == set(targets):
            result.append(digit)
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
        result = _x_wing_message(step, units)
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
    digits = _hidden_pair_digits(step, units[0], sources) if units and sources else []
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


def _x_wing_message(step: LogicStep, units) -> str:
    digit = _single_elimination_digit(step)
    result = f"观察亮起的两行和两列。绿色四格构成数字 {digit} 的 X-Wing；两个 {digit} 必须分布在不同的行和列，因此交叉线其他位置的红色 {digit} 可删除。"
    return result


def _xy_wing_message(step: LogicStep) -> str:
    digit = _single_elimination_digit(step)
    result = f"观察绿色的枢纽和两个翼。枢纽的两个候选分别连接两个翼，而两个翼共享候选 {digit}，因此同时看见两个翼的红色 {digit} 可删除。"
    return result
