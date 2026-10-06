"""直接创建设置 ttk 条目并管理弹层生命周期。"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from ._model import (
    CommandAction,
    CommandItem,
    SettingAction,
    SettingsMenuState,
    TechniqueItem,
    action_widget_name,
)
from ._position import monitor_bounds


class SettingsPopup(tk.Toplevel):
    def __init__(
        self,
        root: tk.Misc,
        state: SettingsMenuState,
        on_setting: Callable[[SettingAction], None],
        on_command: Callable[[CommandAction], None],
        on_close: Callable[[], None],
        font: tuple[str, int] = ("TkDefaultFont", 11),
    ) -> None:
        state.validate()
        super().__init__(root, borderwidth=1, relief=tk.SOLID)
        self.withdraw()
        self.overrideredirect(True)
        self.transient(root)
        self._on_setting = on_setting
        self._on_command = on_command
        self._on_close = on_close
        self._closed = False
        self._checked = {
            "auto_solve": state.auto_solve,
            "auto_clean": state.auto_clean,
            **{item.action_key: item.checked for item in state.techniques},
        }
        self._submenu: ttk.Frame | None = None
        self._submenu_row: ttk.Button | None = None
        self._opens_left = False
        self._check_icons = [tk.PhotoImage(master=self, width=16, height=16) for _ in range(2)]
        foreground = "#" + "".join(f"{channel // 257:02x}" for channel in self.winfo_rgb("#000000"))
        for offset in range(4):
            self._check_icons[1].put(foreground, to=(2 + offset, 7 + offset, 4 + offset, 9 + offset))
        for offset in range(8):
            self._check_icons[1].put(foreground, to=(5 + offset, 10 - offset, 7 + offset, 12 - offset))
        ttk.Style(self).configure("Settings.Toolbutton", font=font, padding=(6, 3), anchor=tk.W)
        self._menu = ttk.Frame(self, name="menu")
        self._menu.grid(row=0, column=0, sticky=tk.NW)
        self._build_settings(self._menu, state)
        self.bind("<Escape>", lambda event: self.close())
        self.bind("<ButtonPress-1>", self._outside_click)
        self.bind("<FocusOut>", self._focus_out)

    def _button(self, frame: ttk.Frame, name: str, text: str, command: Callable[[], None]) -> ttk.Button:
        entry = ttk.Button(
            frame,
            name=name,
            text=text,
            style="Settings.Toolbutton",
            compound=tk.LEFT,
            image=self._check_icons[0],
            command=command,
        )
        entry.bind("<Return>", self._keyboard_invoke)
        entry.bind("<ButtonRelease-1>", self._button_release)
        entry.pack(fill=tk.X)
        return entry

    def _build_settings(self, frame: ttk.Frame, state: SettingsMenuState) -> None:
        solve = self._button(frame, "auto_solve", "自动求解", lambda: self._toggle("auto_solve"))
        solve.configure(image=self._check_icons[int(state.auto_solve)])
        solve.bind("<Enter>", lambda event: self._hide_submenu())

        self._submenu = ttk.Frame(self, name="submenu")
        self._submenu_row = self._button(frame, "auto_technique", "自动解决算法  ▶", self._show_submenu)
        self._submenu_row.bind("<Enter>", lambda event: self._show_submenu())
        self._submenu_row.bind("<Right>", lambda event: self._show_submenu())
        for item in state.techniques:
            self._add_technique(self._submenu, item)

        clean = self._button(
            frame,
            "auto_clean",
            "正确填数后，清理关联笔记",
            lambda: self._toggle("auto_clean"),
        )
        clean.configure(image=self._check_icons[int(state.auto_clean)])
        clean.bind("<Enter>", lambda event: self._hide_submenu())
        ttk.Separator(frame).pack(fill=tk.X, pady=3)

        for item in state.commands:
            if item.kind == "help":
                ttk.Separator(frame).pack(fill=tk.X, pady=3)
            button = self._button(
                frame,
                action_widget_name(item.action_key),
                item.label,
                lambda item=item: self._invoke_command(item),
            )
            button.bind("<Enter>", lambda event: self._hide_submenu())

    def _add_technique(self, frame: ttk.Frame, item: TechniqueItem) -> None:
        row = self._button(
            frame,
            action_widget_name(item.action_key),
            item.label,
            lambda item=item: self._toggle_technique(item),
        )
        row.configure(image=self._check_icons[int(item.checked)])

    def _toggle(self, kind: str) -> None:
        checked = not self._checked[kind]
        self._checked[kind] = checked
        row = self.nametowidget(f"menu.{action_widget_name(kind)}")
        row.configure(image=self._check_icons[int(checked)])
        self._on_setting(SettingAction(kind, checked))

    def _toggle_technique(self, item: TechniqueItem) -> None:
        current = bool(self._checked[item.action_key])
        checked = not current
        self._checked[item.action_key] = checked
        row = self.nametowidget(f"submenu.{action_widget_name(item.action_key)}")
        row.configure(image=self._check_icons[int(checked)])
        self._on_setting(SettingAction("auto_technique", checked, item.name))

    def _invoke_command(self, item: CommandItem) -> None:
        self.close()
        self._on_command(CommandAction(item))

    def post(self, x: int, y: int) -> None:
        if self._closed:
            return
        self.update_idletasks()
        left, top, right, bottom = monitor_bounds(self.master, x, y)
        height = self.winfo_reqheight()
        if self._submenu is not None and self._submenu_row is not None:
            height = max(height, self._submenu_row.winfo_y() + self._submenu.winfo_reqheight() + 2 * int(self.cget("borderwidth")))
        self._x = max(left, min(x, right - self.winfo_reqwidth()))
        self._y = max(top, min(y, bottom - height))
        self._opens_left = (
            self._submenu is not None
            and self._x + self.winfo_reqwidth() + self._submenu.winfo_reqwidth() > right
        )
        self._menu.grid_configure(column=1 if self._opens_left else 0)
        self._place()
        self.deiconify()
        self.update_idletasks()
        self.grab_set()
        self.focus_force()

    def _place(self) -> None:
        self.update_idletasks()
        x = self._x
        if self._opens_left and self._submenu is not None and self._submenu.winfo_manager():
            x -= self._submenu.winfo_reqwidth()
        self.geometry(f"+{x}+{self._y}")

    def _show_submenu(self) -> None:
        if self._closed or self._submenu is None or self._submenu_row is None:
            return
        self._submenu.grid(
            row=0,
            column=0 if self._opens_left else 1,
            sticky=tk.NW,
            pady=(self._submenu_row.winfo_y(), 0),
        )
        self._place()

    def _hide_submenu(self) -> None:
        if self._submenu is not None:
            focused = self.focus_displayof()
            self._submenu.grid_remove()
            if focused in self._submenu.winfo_children():
                self.focus_set()
            self._place()

    def _keyboard_invoke(self, event: tk.Event) -> str:
        event.widget.invoke()
        return "break"

    def _button_release(self, event: tk.Event) -> str | None:
        if not (0 <= event.x < event.widget.winfo_width() and 0 <= event.y < event.widget.winfo_height()):
            event.widget.state(["!pressed"])
            return "break"
        return None

    def _outside_click(self, event: tk.Event) -> str | None:
        x, y = event.x_root - self.winfo_rootx(), event.y_root - self.winfo_rooty()
        if not (0 <= x < self.winfo_width() and 0 <= y < self.winfo_height()):
            self.close()
            return "break"
        return None

    def _focus_out(self, event: tk.Event) -> None:
        focused = self.focus_displayof()
        if focused is None or focused.winfo_toplevel() != self:
            self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._on_close()
        if self.grab_current() == self:
            self.grab_release()
        self.destroy()
        self._check_icons.clear()
        self._menu = None
        self._submenu = None
        self._submenu_row = None
