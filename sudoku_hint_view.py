"""绘制只读的一步推理界面。
绿色标识依据，蓝色标识相关区域，红色标识建议排除。
候选示意只存在于绘制层，关闭面板不修改任何数字或笔记。
长说明使用可滚动文本区，缩放后仍可阅读全部推理。
"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from sudoku_hints import CELLS, Hint
from sudoku_theme import BG, BLUE, BORDER, CELL, ERROR, ERROR_INK, INK, LEFT, SAME, TOP, WHITE, WIDTH

if TYPE_CHECKING:
    from sudoku_view import SudokuView

DIM = "#858573"
DIM_INK = "#604B34"
REGION = "#C3DBF8"
SOURCE_NOTE = "#E5EFCF"


def hint_background(hint: Hint, cell, value: int) -> str:
    result = REGION if cell in hint.regions else DIM
    if cell in hint.sources:
        result = SAME if value else SOURCE_NOTE
    if cell in hint.targets:
        result = BG
    if cell in hint.attention:
        result = ERROR
    return result


def draw_hint(view: SudokuView) -> None:
    hint = view.game.hint_preview
    view.targets.clear()
    view.rectangle((0, 0, WIDTH, 940), DIM)
    view.text(WIDTH / 2, 49, "单步提示", 30, WHITE)
    view.text(WIDTH / 2, 106, "绿色：依据    蓝框：观察区域    红色小字：建议删除", 14, WHITE)
    for cell in CELLS:
        draw_hint_cell(view, hint, cell)
    view._draw_grid_lines()
    draw_outlines(view, hint)
    draw_panel(view, hint)


def draw_hint_cell(view: SudokuView, hint: Hint, cell) -> None:
    r, c = cell
    x, y = LEFT + c * CELL, TOP + r * CELL
    value = view.game.value(cell)
    view.rectangle((x, y, x + CELL, y + CELL), hint_background(hint, cell, value), tags=f"hint-cell-{r}-{c}")
    if value:
        foreground = WHITE if cell in hint.sources or cell in hint.attention else INK if cell in hint.regions else DIM_INK
        view.text(x + CELL / 2, y + CELL / 2, str(value), 43, foreground, numeric=True, tags=f"hint-value-{r}-{c}")
    else:
        draw_hint_notes(view, hint, cell, x, y)


def draw_hint_notes(view: SudokuView, hint: Hint, cell, x: float, y: float) -> None:
    values = view.game.notes.get(cell, ())
    if hint.step is not None and cell in hint.sources | hint.targets:
        values = hint.step.candidates[cell[0]][cell[1]]
    removed = set(() if hint.step is None else hint.step.eliminations)
    for digit in sorted(values):
        draw_note(view, cell, digit, x, y, (*cell, digit) in removed)


def draw_note(view: SudokuView, cell, digit: int, x: float, y: float, removed: bool) -> None:
    r, c = divmod(digit - 1, 3)
    cx, cy = x + (c + 0.5) * CELL / 3, y + (r + 0.5) * CELL / 3
    color = ERROR_INK if removed else INK
    view.text(cx, cy, str(digit), 18, color, numeric=True, tags=f"hint-note-{cell[0]}-{cell[1]}-{digit}")
    if removed:
        view.line((cx - 7, cy + 6, cx + 7, cy - 6), ERROR_INK, 2, tags="hint-removal")


def outline(view: SudokuView, cells, width: int, color: str) -> None:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    x1, y1 = LEFT + min(cols) * CELL + 2, TOP + min(rows) * CELL + 2
    x2, y2 = LEFT + (max(cols) + 1) * CELL - 2, TOP + (max(rows) + 1) * CELL - 2
    view.line((x1, y1, x2, y1, x2, y2, x1, y2, x1, y1), color, width, tags="hint-outline")


def draw_outlines(view: SudokuView, hint: Hint) -> None:
    for unit in hint.units:
        outline(view, unit, 3, BLUE)
    for cell in hint.sources:
        outline(view, (cell,), 2, SAME)
    for cell in hint.targets:
        outline(view, (cell,), 2, BLUE)
    for cell in hint.attention:
        outline(view, (cell,), 2, ERROR_INK)


def draw_panel(view: SudokuView, hint: Hint) -> None:
    view.round_box((LEFT, 699, LEFT + 540, 866), WHITE, 12)
    view.text(LEFT + 16, 718, hint.title, 19, INK, anchor="w", tags="hint-title")
    create_description(view, hint.message)
    view.text(WIDTH / 2, 851, "仅展示这一步；棋盘、笔记均未自动修改。", 13, INK)
    view.round_box((214, 879, 446, 918), BLUE, 10)
    view.text(WIDTH / 2, 898, "知道了，返回棋盘", 18, WHITE)
    view.targets["close-hint"] = ((214, 879, 446, 918), True)
    view.text(WIDTH / 2, 933, "Esc / 空格 / Enter 返回  ·  说明区域可滚动", 10, WHITE)


def create_description(view: SudokuView, message: str) -> None:
    panel = tk.Frame(view, background=WHITE)
    view.hint_panel = panel
    text = description_text(view, panel, message)
    scroll = tk.Scrollbar(panel, command=text.yview)
    _bind_click_to_close(view, panel, text, scroll)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    text.configure(yscrollcommand=scroll.set)
    text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    view.create_window(*view.screen(LEFT + 16, 739), window=panel, anchor="nw",
                       width=508 * view.scale_factor, height=98 * view.scale_factor, tags="hint-description")


def _bind_click_to_close(view: SudokuView, *widgets) -> None:
    for widget in widgets:
        widget.bind("<Button-1>", lambda event: view.dispatch("close-hint"))


def description_text(view: SudokuView, panel, message: str) -> tk.Text:
    text = tk.Text(panel, wrap=tk.CHAR, background=WHITE, foreground=INK, relief=tk.FLAT,
                   highlightthickness=0, borderwidth=0, padx=0, pady=0, cursor="arrow",
                   font=(view.chinese_font, -max(11, round(17 * view.scale_factor))))
    text.insert("1.0", message)
    text.configure(state=tk.DISABLED)
    return text
