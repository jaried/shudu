"""绘制统一的只读一步推理效果。
保留游戏页头并压暗无关区域，亮起观察行列宫和绿色依据格。
红色候选表示本步建议删除，蓝框表示需要观察的逻辑区域。
本模块只消费 Hint 和 SudokuView 的公开绘制 Interface，不调用其私有方法。
"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from shudu.sudoku_hints import CELLS, Hint
from shudu.sudoku_theme import BG, BLUE, CELL, ERROR, ERROR_INK, INK, LEFT, SAME, TOP, WHITE, WIDTH

if TYPE_CHECKING:
    from shudu.sudoku_view import SudokuView

DIM = "#858573"
DIM_INK = "#604B34"
FOCUS = "#FFFCE5"


def hint_background(hint: Hint, cell, value: int) -> str:
    result = FOCUS if cell in hint.regions else DIM
    if cell in hint.sources:
        result = SAME
    if cell in hint.targets and hint.step is not None and hint.step.placements:
        result = SAME
    if cell in hint.targets and hint.step is not None and hint.step.eliminations:
        result = FOCUS
    if cell in hint.attention:
        result = ERROR
    return result


def draw_hint(view: SudokuView) -> None:
    hint = view.game.hint_preview
    view.targets.clear()
    view.rectangle((0, 0, WIDTH, 940), DIM)
    view.draw_header()
    for cell in CELLS:
        draw_hint_cell(view, hint, cell)
    view.draw_grid_lines()
    draw_outlines(view, hint)
    draw_panel(view, hint)
    view.targets.clear()
    view.targets["close-hint"] = ((0, 0, WIDTH, 940), True)


def draw_hint_cell(view: SudokuView, hint: Hint, cell) -> None:
    row, col = cell
    x, y = LEFT + col * CELL, TOP + row * CELL
    value = view.game.value(cell)
    background = hint_background(hint, cell, value)
    view.rectangle((x, y, x + CELL, y + CELL), background, tags=f"hint-cell-{row}-{col}")
    if value:
        foreground = hint_foreground(hint, cell)
        view.text(x + CELL / 2, y + CELL / 2, str(value), 43, foreground, numeric=True, tags=f"hint-value-{row}-{col}")
    else:
        draw_hint_notes(view, hint, cell, x, y)


def hint_foreground(hint: Hint, cell) -> str:
    result = INK if cell in hint.regions else DIM_INK
    if cell in hint.sources or cell in hint.attention:
        result = WHITE
    if cell in hint.targets and hint.step is not None and hint.step.placements:
        result = WHITE
    return result


def draw_hint_notes(view: SudokuView, hint: Hint, cell, x: float, y: float) -> None:
    values = view.game.notes.get(cell, ())
    if hint.step is not None and cell in hint.regions | hint.sources | hint.targets:
        values = hint.step.candidates[cell[0]][cell[1]]
    removed = set(() if hint.step is None else hint.step.eliminations)
    for digit in sorted(values):
        draw_note(view, hint, cell, digit, x, y, (*cell, digit) in removed)


def draw_note(view: SudokuView, hint: Hint, cell, digit: int, x: float, y: float, removed: bool) -> None:
    note_row, note_col = divmod(digit - 1, 3)
    cx = x + (note_col + 0.5) * CELL / 3
    cy = y + (note_row + 0.5) * CELL / 3
    color = note_color(hint, cell, removed)
    view.text(cx, cy, str(digit), 18, color, numeric=True, tags=f"hint-note-{cell[0]}-{cell[1]}-{digit}")
    if removed:
        view.line((cx - 7, cy + 6, cx + 7, cy - 6), ERROR_INK, 2, tags="hint-removal")


def note_color(hint: Hint, cell, removed: bool) -> str:
    result = INK if cell in hint.regions else DIM_INK
    if cell in hint.sources:
        result = WHITE
    if removed:
        result = ERROR_INK
    return result


def outline(view: SudokuView, cells, width: int, color: str) -> None:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    x1 = LEFT + min(cols) * CELL + 2
    y1 = TOP + min(rows) * CELL + 2
    x2 = LEFT + (max(cols) + 1) * CELL - 2
    y2 = TOP + (max(rows) + 1) * CELL - 2
    view.line((x1, y1, x2, y1, x2, y2, x1, y2, x1, y1), color, width, tags="hint-outline")


def draw_outlines(view: SudokuView, hint: Hint) -> None:
    for unit in hint.units:
        outline(view, unit, 3, BLUE)
    if hint.step is not None and hint.step.placements:
        for cell in hint.targets:
            outline(view, (cell,), 3, BLUE)
    for cell in hint.attention:
        outline(view, (cell,), 3, ERROR_INK)


def draw_panel(view: SudokuView, hint: Hint) -> None:
    view.round_box((LEFT, 699, LEFT + 540, 846), WHITE, 10)
    create_description(view, f"{hint.title}：{hint.message}")
    view.round_box((LEFT, 860, LEFT + 540, 904), WHITE, 8)
    view.text(WIDTH / 2, 882, "点击任意位置返回棋盘  ·  提示只展示推理，不自动修改棋盘", 12, DIM_INK)
    view.text(WIDTH / 2, 924, "Esc / 空格 / Enter 返回  ·  长说明可滚动", 10, DIM_INK)


def create_description(view: SudokuView, message: str) -> None:
    panel = tk.Frame(view, background=WHITE)
    view.hint_panel = panel
    text = description_text(view, panel, message)
    scroll = tk.Scrollbar(panel, command=text.yview)
    _bind_click_to_close(view, panel, text, scroll)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    text.configure(yscrollcommand=scroll.set)
    text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    view.create_window(
        *view.screen(LEFT + 10, 709),
        window=panel,
        anchor="nw",
        width=520 * view.scale_factor,
        height=127 * view.scale_factor,
        tags="hint-description",
    )


def _bind_click_to_close(view: SudokuView, *widgets) -> None:
    for widget in widgets:
        widget.bind("<Button-1>", lambda event: view.dispatch("close-hint"))


def description_text(view: SudokuView, panel, message: str) -> tk.Text:
    text = tk.Text(
        panel,
        wrap=tk.CHAR,
        background=WHITE,
        foreground=INK,
        relief=tk.FLAT,
        highlightthickness=0,
        borderwidth=0,
        padx=0,
        pady=0,
        cursor="arrow",
        font=(view.chinese_font, -max(11, round(17 * view.scale_factor))),
    )
    text.insert("1.0", message)
    text.configure(state=tk.DISABLED)
    return text
