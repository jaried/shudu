"""启动数独图形化游戏。
使用 Tkinter 接收鼠标和键盘输入。
默认加载截图中的关卡 108，并复用现有公共求解器。
窗口关闭时取消计时回调，不创建后台线程或写入用户文件。
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from sudoku_game import Game
from sudoku_puzzles import PUZZLES, Puzzle, SCREENSHOT_PUZZLE, puzzle_from_text
from sudoku_view import BG, HEIGHT, WIDTH, SudokuView


HELP_TEXT = (
    "单击格子后，点击下方数字或用键盘输入。\n\n"
    "笔记开启：数字在小九宫格中标记，再按一次取消。\n"
    "笔记关闭：正式填数，错误填数标红并累计错误。\n"
    "错误次数不设上限；同一错误值重复点击不重复计数；擦除和撤回不退错误。\n\n"
    "方向键移动；N 切换笔记；Delete / 0 擦除；\n"
    "Ctrl+Z 撤回；A 自动笔记；H 展示一步提示。\n"
    "空格暂停 / 继续；提示中用 Esc / 空格返回。\n\n"
    "设置中的“自动解决简单算法”默认开启：自动连续执行 X-Wing 之前的技巧，"
    "不自动执行 X-Wing 和 XY-Wing。\n"
    "提示只展示推理，不自动填数或删笔记。\n"
    "自动笔记重算全部空格的行、列、宫合法候选，可一次撤回。\n"
    "关闭窗口不保存进度；左上角可选择其他关卡。"
)


class SudokuWindow:
    def __init__(self, root: tk.Tk, game: Game | None = None):
        self.root = root
        self.game = game if game is not None else Game()
        self._configure_window()
        self.view = SudokuView(root, self.game, self.dispatch)
        self.view.pack(fill=tk.BOTH, expand=True)
        self._bind_commands()
        self._bind_window_events()
        self._timer_id: str | None = None
        self._tick()
        return

    def _configure_window(self) -> None:
        self.root.title("数独 · shudu")
        self.root.configure(background=BG)
        scale = min(1.0, (self.root.winfo_screenheight()-100)/HEIGHT)
        self.root.geometry(f"{int(WIDTH*scale)}x{int(HEIGHT*scale)}")
        self.root.minsize(430, 613)

    def _bind_commands(self) -> None:
        self.commands = {
            "erase": self.game.erase, "undo": self.game.undo,
            "notes": self.game.toggle_notes, "notes-switch": self.game.toggle_notes,
            "hint": self.game.hint, "close-hint": self.game.close_hint,
            "auto-notes": self.game.auto_notes, "pause": self.game.toggle_pause,
            "restart": self.restart, "levels": self.show_levels,
            "settings": self.show_settings,
        }

    def _bind_window_events(self) -> None:
        self.root.bind("<KeyPress>", self._key)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.view.focus_set()

    def dispatch(self, action: str) -> None:
        if self.game.status == "hint" and action != "close-hint":
            return
        parts = action.split(":")
        if parts[0] == "cell":
            self.game.select(int(parts[1]), int(parts[2]))
        elif parts[0] == "digit":
            self.game.enter(int(parts[1]))
        else:
            self.commands[action]()
        self.view.draw()

    def _key(self, event: tk.Event) -> str | None:
        action = self._key_action(event)
        result = None
        if action is not None:
            self.dispatch(action)
            result = "break"
        elif self._move_key(event.keysym):
            self.view.draw()
            result = "break"
        return result

    def _key_action(self, event: tk.Event) -> str | None:
        if self.game.status == "hint":
            action = "close-hint" if event.keysym in ("Escape", "space", "Return", "KP_Enter", "h", "H") else None
        else:
            action = self._play_key_action(event)
        return action

    def _play_key_action(self, event: tk.Event) -> str | None:
        keys = {"n": "notes", "a": "auto-notes", "h": "hint", "space": "pause", "Escape": "pause", "BackSpace": "erase", "Delete": "erase", "0": "erase"}
        symbol = event.keysym
        action = keys.get(symbol.lower(), keys.get(symbol))
        if event.char in "123456789" and event.char:
            action = f"digit:{event.char}"
        if symbol.lower() == "z" and event.state & 0x4:
            action = "undo"
        return action

    def _move_key(self, symbol: str) -> bool:
        offsets = {"Left": (0,-1), "Right": (0,1), "Up": (-1,0), "Down": (1,0)}
        moved = self.game.status == "playing" and symbol in offsets
        if moved:
            self.game.move(*offsets[symbol])
        return moved

    def _tick(self) -> None:
        self.view.update_timer()
        self._timer_id = self.root.after(250, self._tick)

    def close(self) -> None:
        if self._timer_id is not None:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None
        self.root.destroy()

    def restart(self) -> None:
        self._change_puzzle(self.game.puzzle)

    def _change_puzzle(self, puzzle: Puzzle) -> None:
        dirty = bool(self.game.history or self.game.mistakes)
        if dirty and self.game.status in ("playing", "paused"):
            if not messagebox.askyesno("开始新游戏", "放弃当前进度并重新开始？", parent=self.root):
                return
        auto_clean = self.game.auto_clean
        auto_simple = self.game.auto_simple
        self.game = Game(puzzle, auto_simple=auto_simple)
        self.game.auto_clean = auto_clean
        self.game.auto_solve_simple()
        self.view.game = self.game
        self._bind_commands()
        self.view.draw()

    def _menu(self) -> tk.Menu:
        result = tk.Menu(self.root, tearoff=False, font=(self.view.chinese_font, 11))
        return result

    def _add_levels(self, menu: tk.Menu) -> None:
        for puzzle in PUZZLES:
            menu.add_command(label=f"{puzzle.title} · {puzzle.difficulty}", command=lambda selected=puzzle: self._change_puzzle(selected))

    def _popup(self, menu: tk.Menu) -> None:
        self._active_menu = menu
        menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())

    def show_levels(self) -> None:
        menu = self._menu()
        menu.add_command(label="选择关卡", state=tk.DISABLED)
        self._add_levels(menu)
        self._popup(menu)

    def show_settings(self) -> None:
        menu = self._menu()
        self._auto_simple = tk.BooleanVar(value=self.game.auto_simple)
        menu.add_checkbutton(
            label="自动解决简单算法（不含 X-Wing）",
            variable=self._auto_simple,
            command=self._set_auto_simple,
        )
        self._auto_clean = tk.BooleanVar(value=self.game.auto_clean)
        menu.add_checkbutton(label="正确填数后，清理关联笔记", variable=self._auto_clean, command=self._set_auto_clean)
        menu.add_separator()
        menu.add_command(label="重新开始当前关卡", command=self.restart)
        self._add_levels(menu)
        menu.add_separator()
        menu.add_command(label="操作说明", command=self.show_help)
        self._popup(menu)

    def _set_auto_simple(self) -> None:
        self.game.set_auto_simple(self._auto_simple.get())
        self.view.draw()

    def _set_auto_clean(self) -> None:
        self.game.auto_clean = self._auto_clean.get()

    def show_help(self) -> None:
        messagebox.showinfo("操作说明", HELP_TEXT, parent=self.root)


def main(puzzle: Puzzle = SCREENSHOT_PUZZLE) -> None:
    game = Game(puzzle, auto_simple=True)
    game.auto_solve_simple()
    root = tk.Tk()
    SudokuWindow(root, game)
    root.mainloop()


if __name__ == "__main__":
    # 直接修改这里即可自定义开局；`.` 或 `0` 表示空格，也可在数字间加空格。
    CUSTOM_BOARD = """
...7...3.
8......5.
..2..8.74
.37...6.9
..4......
1..93.7..
.9...2..7
.6.....1.
...51....
    """
    main(puzzle_from_text(CUSTOM_BOARD))
