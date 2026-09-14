"""绘制接近截图配色的数独桌面界面。
所有控件与棋盘使用同一套缩放和命中坐标。
本模块只呈现状态并发送操作，不执行数独求解。
行列宫完成动画是 View 内部瞬态，不写入 Game 或撤回状态。
"""

from __future__ import annotations

import tkinter as tk
from math import cos, pi, sin
from tkinter import font
from typing import Callable

from shudu.sudoku_game import CELLS, Cell, Game
from shudu.sudoku_hint_view import draw_hint
from shudu.sudoku_theme import (
    WIDTH, HEIGHT, LEFT, TOP, SIDE, CELL, BG, INK, ACCENT, PEER,
    SELECTED, SAME, LINE, BORDER, BLUE, MUTED, ERROR, ERROR_LIGHT, ERROR_INK, WHITE,
    COMPLETE_LIGHT, COMPLETE_MID, COMPLETE_STRONG,
)

COMPLETION_FRAME_MS = 70
COMPLETION_PALETTE = (
    COMPLETE_LIGHT,
    COMPLETE_MID,
    COMPLETE_STRONG,
    COMPLETE_MID,
    COMPLETE_LIGHT,
)

Rect = tuple[float, float, float, float]


def cell_background(game: Game, cell: Cell, wrong: set[Cell], conflicts: set[Cell], highlighted: set[Cell]) -> str:
    color = PEER if cell in highlighted else BG
    if game.active_digit and game.value(cell) == game.active_digit and cell not in conflicts:
        color = SAME
    if cell == game.selected:
        color = INK if game.value(cell) else SELECTED
    if cell in wrong:
        color = ERROR if cell == game.selected else ERROR_LIGHT
    return color


def cell_foreground(game: Game, cell: Cell, wrong: set[Cell], conflicts: set[Cell]) -> str:
    color = INK
    if game.value(cell) and (cell == game.selected or game.value(cell) == game.active_digit):
        color = WHITE
    if cell in conflicts or cell in wrong:
        color = ERROR_INK
    if cell in wrong and cell == game.selected:
        color = WHITE
    return color


def choose_font(master: tk.Misc, choices: tuple[str, ...]) -> str:
    available = set(font.families(master))
    result = next((name for name in choices if name in available), "TkDefaultFont")
    return result


class SudokuView(tk.Canvas):
    def __init__(self, master: tk.Misc, game: Game, dispatch: Callable[[str], None]):
        super().__init__(master, background=BG, highlightthickness=0, takefocus=True)
        self.game = game
        self.dispatch = dispatch
        self.targets: dict[str, tuple[Rect, bool]] = {}
        self.scale_factor = 1.0
        self.offset = (0.0, 0.0)
        self.hint_panel: tk.Frame | None = None
        self._completion_after_id: str | None = None
        self._completion_units: tuple[tuple[Cell, ...], ...] = ()
        self._completion_frame = 0
        self._completion_colors: dict[Cell, str] = {}
        self._init_fonts()
        self._bind_events()
        return

    def _init_fonts(self) -> None:
        self.chinese_font = choose_font(self, ("Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC"))
        self.number_font = choose_font(self, ("Segoe UI Light", "Helvetica Neue", "DejaVu Sans"))

    def _bind_events(self) -> None:
        self.bind("<Configure>", self._resize)
        self.bind("<Button-1>", self._click)
        self.bind("<Motion>", self._hover)
        self.bind("<Leave>", lambda event: self.configure(cursor="arrow"))

    def _resize(self, event: tk.Event) -> None:
        self.scale_factor = min(event.width / WIDTH, event.height / HEIGHT)
        self.offset = ((event.width - WIDTH * self.scale_factor) / 2, (event.height - HEIGHT * self.scale_factor) / 2)
        self.draw()

    def screen(self, x: float, y: float) -> tuple[float, float]:
        result = (self.offset[0] + x * self.scale_factor, self.offset[1] + y * self.scale_factor)
        return result

    def coordinates(self, points: tuple[float, ...]) -> list[float]:
        result = [point * self.scale_factor + self.offset[index % 2] for index, point in enumerate(points)]
        return result

    def text(self, x: float, y: float, value: str, size: float, color: str = INK, **options) -> int:
        numeric = options.pop("numeric", False)
        family = self.number_font if numeric else self.chinese_font
        text_font = (family, -max(8, round(size * self.scale_factor)))
        result = self.create_text(*self.screen(x, y), text=value, fill=color, font=text_font, **options)
        return result

    def rectangle(self, bounds: Rect, fill: str, **options) -> int:
        result = self.create_rectangle(*self.coordinates(bounds), fill=fill, outline="", **options)
        return result

    def line(self, points: tuple[float, ...], color: str, width: float = 2, **options) -> int:
        result = self.create_line(*self.coordinates(points), fill=color, width=width * self.scale_factor, **options)
        return result

    def oval(self, bounds: Rect, fill: str, **options) -> int:
        result = self.create_oval(*self.coordinates(bounds), fill=fill, outline="", **options)
        return result

    def round_box(self, bounds: Rect, fill: str, radius: float = 12) -> int:
        x1, y1, x2, y2 = bounds
        r = radius
        points = (x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2, x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1)
        result = self.create_polygon(*self.coordinates(points), smooth=True, splinesteps=20, fill=fill, outline="")
        return result

    def draw(self) -> None:
        self._clear_hint_panel()
        self.delete("all")
        self.targets.clear()
        self.draw_header()
        if self.game.status == "hint":
            draw_hint(self)
        else:
            self._draw_play_surface()

    def _clear_hint_panel(self) -> None:
        if self.hint_panel is not None:
            self.hint_panel.destroy()
            self.hint_panel = None

    def animate_completed_units(self, units) -> None:
        """播放行、列、宫完成后的青色扫光；不修改 Game 状态。"""
        normalized = tuple(dict.fromkeys(tuple(unit) for unit in units if unit))
        if not normalized:
            return
        self.stop_completion_animation()
        self._completion_units = normalized
        self._completion_frame = 0
        self._draw_completion_frame()
        return

    def stop_completion_animation(self) -> None:
        """取消当前完成动画并清理临时绘制状态。"""
        if self._completion_after_id is not None:
            self.after_cancel(self._completion_after_id)
            self._completion_after_id = None
        self._completion_units = ()
        self._completion_colors = {}
        self._completion_frame = 0
        return

    def _draw_completion_frame(self) -> None:
        max_rank = max(
            self._completion_rank(unit, cell)
            for unit in self._completion_units
            for cell in unit
        )
        final_frame = max_rank + len(COMPLETION_PALETTE)
        if self._completion_frame >= final_frame:
            self._completion_after_id = None
            self._completion_units = ()
            self._completion_colors = {}
            self._completion_frame = 0
            self.draw()
            return
        self._completion_colors = self._completion_frame_colors()
        self.draw()
        self._completion_frame += 1
        self._completion_after_id = self.after(
            COMPLETION_FRAME_MS,
            self._draw_completion_frame,
        )
        return

    def _completion_frame_colors(self) -> dict[Cell, str]:
        result: dict[Cell, str] = {}
        for unit in self._completion_units:
            for cell in unit:
                phase = self._completion_frame - self._completion_rank(unit, cell)
                if 0 <= phase < len(COMPLETION_PALETTE):
                    result[cell] = COMPLETION_PALETTE[phase]
        return result

    def _completion_rank(self, unit, cell: Cell) -> int:
        rows = {row for row, _ in unit}
        cols = {col for _, col in unit}
        if len(rows) == 1:
            result = cell[1] - min(cols)
        elif len(cols) == 1:
            result = cell[0] - min(rows)
        else:
            result = cell[0] - min(rows) + cell[1] - min(cols)
        return result

    def _draw_play_surface(self) -> None:
        if self.game.status == "paused":
            self._draw_overlay()
        else:
            self._draw_board()
        self._draw_controls()
        self._draw_footer()

    def draw_header(self) -> None:
        """绘制普通页头；提示视图通过这一公开绘制 Interface 复用。"""
        self.text(WIDTH / 2, 49, self.game.puzzle.title, 30, ACCENT)
        self.line((81,34, 67,49, 81,64), ACCENT, 5, capstyle=tk.ROUND, joinstyle=tk.ROUND)
        self.targets["levels"] = ((50, 24, 102, 77), True)
        self._draw_gear(576, 49)
        self.targets["settings"] = ((551, 24, 601, 77), True)
        self.text(LEFT + 5, 107, self.game.puzzle.difficulty, 23, ACCENT, anchor="w")
        self._draw_mistakes()
        self.text(545, 107, self.game.time_text, 26, ACCENT, anchor="e", numeric=True, tags="timer")
        self._draw_pause()

    def _draw_mistakes(self) -> None:
        color = SAME if self.game.mistakes == 0 else ERROR_INK
        self.text(296, 107, "错误：", 23, ACCENT, anchor="e")
        self.text(318, 107, str(self.game.mistakes), 26, color, numeric=True, tags="mistake-count")

    def _draw_pause(self) -> None:
        enabled = self.game.status in ("playing", "paused")
        color = ACCENT if enabled else MUTED
        if self.game.status == "paused":
            self.text(576, 107, "▶", 22, color)
        else:
            self.line((569,97,569,117), color, 5, capstyle=tk.ROUND)
            self.line((582,97,582,117), color, 5, capstyle=tk.ROUND)
        self.targets["pause"] = ((553, 86, 600, 129), enabled)

    def _draw_gear(self, x: float, y: float) -> None:
        for index in range(8):
            angle = index * pi / 4
            self.line((x+12*cos(angle), y+12*sin(angle), x+19*cos(angle), y+19*sin(angle)), ACCENT, 8, capstyle=tk.ROUND)
        self.oval((x-17,y-17,x+17,y+17), ACCENT)
        self.oval((x-10,y-10,x+10,y+10), BG)
        self.oval((x-6,y-6,x+6,y+6), ACCENT)

    def _draw_board(self) -> None:
        wrong = self.game.wrong_cells()
        conflicts = self.game.conflict_cells()
        highlighted = self.game.highlighted_cells()
        for cell in CELLS:
            self._draw_cell(cell, wrong, conflicts, highlighted)
        self.draw_grid_lines()

    def _draw_cell(self, cell: Cell, wrong: set[Cell], conflicts: set[Cell], highlighted: set[Cell]) -> None:
        row, col = cell
        x, y = LEFT + col * CELL, TOP + row * CELL
        background = cell_background(self.game, cell, wrong, conflicts, highlighted)
        foreground = cell_foreground(self.game, cell, wrong, conflicts)
        flashing = cell in self._completion_colors
        animated = flashing and cell != self.game.selected and cell not in wrong
        tags = (f"cell-{row}-{col}",)
        if flashing:
            tags += ("completion-flash",)
        if animated:
            background = self._completion_colors[cell]
            foreground = INK
        self.rectangle((x,y,x+CELL,y+CELL), background, tags=tags)
        if self.game.value(cell):
            self.text(x+CELL/2, y+CELL/2, str(self.game.value(cell)), 43, foreground, numeric=True, tags=f"value-{row}-{col}")
        else:
            self._draw_notes(cell, x, y)

    def _draw_notes(self, cell: Cell, x: float, y: float) -> None:
        for digit in sorted(self.game.notes.get(cell, ())):
            note_row, note_col = divmod(digit - 1, 3)
            color = SAME if digit == self.game.active_digit and self.game.active_digit else INK
            tag = f"note-{cell[0]}-{cell[1]}-{digit}"
            self.text(x+(note_col+0.5)*CELL/3, y+(note_row+0.5)*CELL/3, str(digit), 18, color, numeric=True, tags=tag)

    def draw_grid_lines(self) -> None:
        """绘制共用棋盘网格；普通棋盘与提示效果共享。"""
        for index in range(10):
            width = 3 if index % 3 == 0 else 1
            color = BORDER if index % 3 == 0 else LINE
            distance = index * CELL
            self.line((LEFT+distance,TOP,LEFT+distance,TOP+SIDE), color, width)
            self.line((LEFT,TOP+distance,LEFT+SIDE,TOP+distance), color, width)

    def _control_state(self) -> dict[str, bool]:
        game = self.game
        playing = game.status == "playing"
        erasable = game.editable and bool(game.value(game.selected) or game.notes.get(game.selected))
        result = {"erase": erasable, "undo": playing and bool(game.history), "notes": playing, "auto-notes": playing and not game.wrong_cells(), "hint": playing}
        return result

    def _draw_controls(self) -> None:
        controls = (("erase", "擦除", 100), ("undo", "撤回", 212), ("notes", "笔记", 324),
                    ("auto-notes", "自动笔记", 436), ("hint", "提示", 548))
        enabled = self._control_state()
        for action, label, x in controls:
            self._draw_tool(action, label, x, enabled[action])
        self._draw_note_switch()
        for digit in range(1, 10):
            self._draw_digit(digit)

    def _draw_tool(self, action: str, label: str, x: float, enabled: bool) -> None:
        color = INK if enabled else MUTED
        if action == "notes" and self.game.notes_mode:
            color = BLUE if enabled else MUTED
        self.round_box((x-28,717,x+28,773), color)
        self._draw_icon(action, x, 745)
        self.text(x, 793, label, 18, ACCENT if enabled else MUTED)
        self.targets[action] = ((x-44, 708, x+44, 810), enabled)

    def _draw_icon(self, action: str, x: float, y: float) -> None:
        if action == "erase":
            self._eraser_icon(x, y)
        elif action == "undo":
            self._undo_icon(x, y)
        elif action == "notes":
            self._pen_icon(x, y)
        elif action == "auto-notes":
            self._auto_notes_icon(x, y)
        else:
            self._hint_icon(x, y)

    def _eraser_icon(self, x: float, y: float) -> None:
        points = (x-17,y+3, x+3,y-17, x+17,y-3, x-3,y+17, x-17,y+3)
        self.line(points, WHITE, 3, joinstyle=tk.ROUND)
        self.line((x-9,y-5,x+5,y+9), WHITE, 3)
        self.line((x-3,y+17,x+18,y+17), WHITE, 2)

    def _undo_icon(self, x: float, y: float) -> None:
        points = (x-13,y-8, x+10,y-8, x+17,y+5, x+10,y+15, x-8,y+15)
        self.line(points, WHITE, 4, smooth=True, capstyle=tk.ROUND)
        self.line((x-5,y-17,x-15,y-8,x-5,y+1), WHITE, 4, joinstyle=tk.ROUND, capstyle=tk.ROUND)

    def _pen_icon(self, x: float, y: float) -> None:
        self.line((x-13,y+18,x-9,y-6,x+5,y-17,x+17,y-5,x+6,y+10,x-13,y+18), WHITE, 2, joinstyle=tk.ROUND)
        self.line((x-13,y+18,x+1,y+2), WHITE, 2)
        self.oval((x-2,y-2,x+4,y+4), WHITE)
        self.line((x+1,y-14,x+14,y-1), WHITE, 5)

    def _auto_notes_icon(self, x: float, y: float) -> None:
        for digit in range(1, 10):
            row, col = divmod(digit - 1, 3)
            self.text(x + (col - 1) * 14, y + (row - 1) * 15, str(digit), 13, WHITE, numeric=True)

    def _hint_icon(self, x: float, y: float) -> None:
        self.line((x-15,y-17,x+15,y-17,x+15,y+17,x-15,y+17,x-15,y-17), WHITE, 3, joinstyle=tk.ROUND)
        self.text(x, y, "?", 30, WHITE, numeric=True)

    def _draw_note_switch(self) -> None:
        enabled = self.game.status == "playing"
        color = BLUE if self.game.notes_mode and enabled else MUTED
        self.round_box((348,717,382,737), color, 10)
        x = 372 if self.game.notes_mode else 358
        self.oval((x-8,719,x+8,735), WHITE)
        self.targets["notes-switch"] = ((346, 707, 386, 745), enabled)

    def _digit_enabled(self, digit: int) -> bool:
        game = self.game
        result = game.editable and (game.notes_mode or not game.completed_digit(digit))
        if game.notes_mode and game.value(game.selected):
            result = False
        return result

    def _draw_digit(self, digit: int) -> None:
        x = LEFT + (digit - 0.5) * CELL
        enabled = self._digit_enabled(digit)
        color = INK if enabled else MUTED
        if self.game.active_digit == digit and enabled:
            self.round_box((x-24,821,x+24,881), PEER)
            color = BLUE if self.game.notes_mode else ACCENT
        self.text(x, 851, str(digit), 48, color, numeric=True, tags=f"digit-{digit}")
        self.targets[f"digit:{digit}"] = ((x-29, 818, x+29, 884), enabled)

    def _draw_footer(self) -> None:
        if self.game.status == "won":
            self.text(WIDTH/2, 905, "挑战完成", 15, SAME, tags="completion-status")
            detail = f"用时 {self.game.time_text}  ·  提示 {self.game.hints_used} 次"
            self.text(WIDTH/2, 928, detail, 11, INK, tags="completion-detail")
        else:
            self.text(WIDTH/2, 905, self.game.message, 12, INK, width=590*self.scale_factor)
            self.text(WIDTH/2, 928, "N 笔记  ·  A 自动笔记  ·  H 提示  ·  Ctrl+Z 撤回  ·  空格 暂停", 10, MUTED)

    def _draw_overlay(self) -> None:
        self.round_box((LEFT,TOP,LEFT+SIDE,TOP+SIDE), PEER, 18)
        self.text(WIDTH/2, 344, "已暂停", 36, ACCENT)
        self.text(WIDTH/2, 402, "休息一下，回来继续。", 18)
        self._overlay_buttons()

    def _overlay_buttons(self) -> None:
        self.round_box((230,491,430,545), INK)
        self.text(WIDTH/2, 518, "继续游戏", 20, WHITE)
        self.targets["overlay:pause"] = ((230, 491, 430, 545), True)

    def _logical_pointer(self, event: tk.Event) -> tuple[float, float]:
        result = ((event.x-self.offset[0])/self.scale_factor, (event.y-self.offset[1])/self.scale_factor)
        return result

    def action_at(self, x: float, y: float) -> str | None:
        result = None
        for action, (bounds, enabled) in reversed(tuple(self.targets.items())):
            x1, y1, x2, y2 = bounds
            if enabled and x1 <= x <= x2 and y1 <= y <= y2:
                result = action
                break
        if result is None and self.game.status == "playing" and LEFT <= x < LEFT+SIDE and TOP <= y < TOP+SIDE:
            result = f"cell:{int((y-TOP)//CELL)}:{int((x-LEFT)//CELL)}"
        return result

    def _click(self, event: tk.Event) -> None:
        self.focus_set()
        if self.game.status == "hint":
            self.dispatch("close-hint")
            return
        action = self.action_at(*self._logical_pointer(event))
        if action is not None:
            self.dispatch(action.removeprefix("overlay:"))

    def _hover(self, event: tk.Event) -> None:
        action = self.action_at(*self._logical_pointer(event))
        self.configure(cursor="hand2" if action is not None else "arrow")

    def update_timer(self) -> None:
        self.itemconfigure("timer", text=self.game.time_text)
