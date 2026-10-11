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
        self._submenu_visible = False
        self._bounds: tuple[int, int, int, int] | None = None
        self._opens_left = False
        self._check_icons = [
            tk.PhotoImage(master=self, width=16, height=16) for _ in range(2)
        ]
        foreground = "#" + "".join(
            f"{channel // 257:02x}" for channel in self.winfo_rgb("#000000")
        )
        for offset in range(4):
            self._check_icons[1].put(
                foreground, to=(2 + offset, 7 + offset, 4 + offset, 9 + offset)
            )
        for offset in range(8):
            self._check_icons[1].put(
                foreground, to=(5 + offset, 10 - offset, 7 + offset, 12 - offset)
            )
        ttk.Style(self).configure(
            "Settings.Toolbutton", font=font, padding=(6, 3), anchor=tk.W
        )
        self._viewport = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self._viewport.grid(row=0, column=0, sticky=tk.NSEW)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self._menu = ttk.Frame(self, name="menu")
        self._menu_window = self._viewport.create_window(
            0, 0, window=self._menu, anchor=tk.NW
        )
        self._build_settings(self._menu, state)
        self._horizontal = ttk.Scrollbar(
            self, orient=tk.HORIZONTAL, command=self._viewport.xview
        )
        self._vertical = ttk.Scrollbar(
            self, orient=tk.VERTICAL, command=self._viewport.yview
        )
        self._viewport.configure(
            xscrollcommand=self._horizontal.set, yscrollcommand=self._vertical.set
        )
        self.bind("<Escape>", lambda event: self.close())
        self.bind("<ButtonPress-1>", self._outside_click)
        self.bind("<FocusOut>", self._focus_out)
        self.bind("<Button-4>", lambda event: self._scroll(event, -3))
        self.bind("<Button-5>", lambda event: self._scroll(event, 3))

    def _button(
        self, frame: ttk.Frame, name: str, text: str, command: Callable[[], None]
    ) -> ttk.Button:
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
        entry.bind("<FocusIn>", self._reveal_entry)
        entry.pack(fill=tk.X)
        return entry

    def _build_settings(self, frame: ttk.Frame, state: SettingsMenuState) -> None:
        solve = self._button(
            frame, "auto_solve", "自动求解", lambda: self._toggle("auto_solve")
        )
        solve.configure(image=self._check_icons[int(state.auto_solve)])
        solve.bind("<Enter>", lambda event: self._hide_submenu())

        self._submenu = ttk.Frame(self, name="submenu")
        self._submenu_window = self._viewport.create_window(
            0,
            0,
            window=self._submenu,
            anchor=tk.NW,
            state=tk.HIDDEN,
        )
        self._submenu_row = self._button(
            frame, "auto_technique", "自动解决算法  ▶", self._show_submenu
        )
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
        self._bounds = monitor_bounds(self.master, x, y)
        left, top, right, bottom = self._bounds
        self._x = max(left, min(x, right - self._menu.winfo_reqwidth()))
        width = self._menu.winfo_reqwidth()
        height = self._menu.winfo_reqheight()
        if self._submenu is not None and self._submenu_row is not None:
            width += self._submenu.winfo_reqwidth()
            height = max(
                height, self._submenu_row.winfo_y() + self._submenu.winfo_reqheight()
            )
        border = 2 * int(self.cget("borderwidth"))
        height += border
        available_width = right - left - border
        if height > bottom - top:
            available_width -= self._vertical.winfo_reqwidth()
        if width > available_width:
            height += self._horizontal.winfo_reqheight()
        self._y = max(top, min(y, bottom - height))
        self._opens_left = (
            self._submenu is not None
            and self._x + self._menu.winfo_reqwidth() + self._submenu.winfo_reqwidth()
            > right
        )
        self._place()
        self.deiconify()
        self.update_idletasks()
        self.grab_set()
        self.focus_force()

    def _place(self) -> None:
        if self._bounds is None:
            return
        self.update_idletasks()
        left, top, right, bottom = self._bounds
        width = self._menu.winfo_reqwidth()
        height = self._menu.winfo_reqheight()
        submenu_width = 0
        if (
            self._submenu_visible
            and self._submenu is not None
            and self._submenu_row is not None
        ):
            submenu_width = self._submenu.winfo_reqwidth()
            height = max(
                height, self._submenu_row.winfo_y() + self._submenu.winfo_reqheight()
            )
            self._viewport.coords(
                self._submenu_window,
                0 if self._opens_left else width,
                self._submenu_row.winfo_y(),
            )
        self._viewport.coords(
            self._menu_window, submenu_width if self._opens_left else 0, 0
        )
        width += submenu_width
        border = 2 * int(self.cget("borderwidth"))
        available_width, available_height = right - left - border, bottom - top - border
        vertical_width = self._vertical.winfo_reqwidth()
        horizontal_height = self._horizontal.winfo_reqheight()
        scroll_x, scroll_y = width > available_width, height > available_height
        for _ in range(2):
            scroll_x = width > available_width - (vertical_width if scroll_y else 0)
            scroll_y = height > available_height - (
                horizontal_height if scroll_x else 0
            )
        popup_width = min(
            right - left, width + border + (vertical_width if scroll_y else 0)
        )
        popup_height = min(
            bottom - top, height + border + (horizontal_height if scroll_x else 0)
        )
        self._viewport.configure(
            width=max(1, popup_width - border - (vertical_width if scroll_y else 0)),
            height=max(
                1, popup_height - border - (horizontal_height if scroll_x else 0)
            ),
            scrollregion=(0, 0, width, height),
        )
        if scroll_x:
            self._horizontal.grid(row=1, column=0, sticky=tk.EW)
            self._horizontal.lift()
        else:
            self._horizontal.grid_remove()
        if scroll_y:
            self._vertical.grid(row=0, column=1, sticky=tk.NS)
            self._vertical.lift()
        else:
            self._vertical.grid_remove()
        x = max(
            left,
            min(
                self._x - (submenu_width if self._opens_left else 0),
                right - popup_width,
            ),
        )
        y = max(top, min(self._y, bottom - popup_height))
        self.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

    def _show_submenu(self) -> None:
        if self._closed or self._submenu is None or self._submenu_row is None:
            return
        self._submenu_visible = True
        self._viewport.itemconfigure(self._submenu_window, state=tk.NORMAL)
        self._place()
        self._viewport.xview_moveto(0 if self._opens_left else 1)

    def _hide_submenu(self) -> None:
        if self._submenu_visible and self._submenu is not None:
            focused = self.focus_displayof()
            self._submenu_visible = False
            self._viewport.itemconfigure(self._submenu_window, state=tk.HIDDEN)
            self._viewport.xview_moveto(0)
            if focused in self._submenu.winfo_children():
                self.focus_set()
            self._place()

    def _keyboard_invoke(self, event: tk.Event) -> str:
        event.widget.invoke()
        return "break"

    def _reveal_entry(self, event: tk.Event) -> None:
        self.update_idletasks()
        viewport = self._viewport
        left, top, right, bottom = map(
            float, self.tk.splitlist(viewport.cget("scrollregion"))
        )
        for origin, extent, entry_origin, entry_extent, start, end, move in (
            (
                viewport.canvasx(0),
                viewport.winfo_width(),
                event.widget.winfo_rootx() - viewport.winfo_rootx(),
                event.widget.winfo_width(),
                left,
                right,
                viewport.xview_moveto,
            ),
            (
                viewport.canvasy(0),
                viewport.winfo_height(),
                event.widget.winfo_rooty() - viewport.winfo_rooty(),
                event.widget.winfo_height(),
                top,
                bottom,
                viewport.yview_moveto,
            ),
        ):
            if entry_origin < 0:
                move((origin + entry_origin - start) / (end - start))
            elif entry_origin + entry_extent > extent:
                move(
                    (origin + entry_origin + entry_extent - extent - start)
                    / (end - start)
                )

    def _scroll(self, event: tk.Event, units: int) -> str:
        scroll = (
            self._viewport.xview_scroll
            if event.state & 0x1
            else self._viewport.yview_scroll
        )
        scroll(units, "units")
        return "break"

    def _button_release(self, event: tk.Event) -> str | None:
        if not (
            0 <= event.x < event.widget.winfo_width()
            and 0 <= event.y < event.widget.winfo_height()
        ):
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
