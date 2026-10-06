"""展示支持悬停展开、连续勾选的设置菜单，管理焦点和鼠标抓取。"""

import sys
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk


def _monitor_bounds(root: tk.Tk, x: int, y: int) -> tuple[int, int, int, int]:
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class MonitorInfo(ctypes.Structure):
            _fields_ = [
                ("size", wintypes.DWORD), ("monitor", wintypes.RECT),
                ("work", wintypes.RECT), ("flags", wintypes.DWORD),
            ]

        user32 = ctypes.WinDLL("user32")
        user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
        user32.MonitorFromPoint.restype = wintypes.HANDLE
        user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MonitorInfo)]
        info = MonitorInfo(size=ctypes.sizeof(MonitorInfo))
        monitor = user32.MonitorFromPoint(wintypes.POINT(x, y), 2)
        if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            raise ctypes.WinError()
        return info.work.left, info.work.top, info.work.right, info.work.bottom
    return (
        root.winfo_vrootx(), root.winfo_vrooty(),
        root.winfo_vrootx() + root.winfo_vrootwidth(),
        root.winfo_vrooty() + root.winfo_vrootheight(),
    )


class SettingsPopup(tk.Toplevel):
    def __init__(self, root: tk.Tk, menu: tk.Menu, on_close: Callable[[], None]):
        super().__init__(root, borderwidth=1, relief=tk.SOLID)
        self.withdraw()
        self.overrideredirect(True)
        self.transient(root)
        self._on_close = on_close
        self._submenu: ttk.Frame | None = None
        self._submenu_row: tk.Widget | None = None
        self._opens_left = False
        self._check_icons = [tk.PhotoImage(master=self, width=16, height=16) for _ in range(2)]
        foreground = "#" + "".join(f"{channel // 257:02x}" for channel in self.winfo_rgb(menu.cget("foreground")))
        for offset in range(4):
            self._check_icons[1].put(foreground, to=(2 + offset, 7 + offset, 4 + offset, 9 + offset))
        for offset in range(8):
            self._check_icons[1].put(foreground, to=(5 + offset, 10 - offset, 7 + offset, 12 - offset))
        ttk.Style(self).configure("Settings.Toolbutton", font=menu.cget("font"), padding=(6, 3), anchor=tk.W)
        self._menu = ttk.Frame(self, name="menu")
        self._menu.grid(row=0, column=0, sticky=tk.NW)
        self._build_entries(self._menu, menu)
        self.bind("<Escape>", lambda event: self.close())
        self.bind("<ButtonPress-1>", self._outside_click)
        self.bind("<FocusOut>", self._focus_out)

    def _build_entries(self, frame: ttk.Frame, menu: tk.Menu) -> None:
        for index in range(menu.index(tk.END) + 1):
            kind = menu.type(index)
            if kind == "separator":
                ttk.Separator(frame).pack(fill=tk.X, pady=3)
                continue
            label = menu.entrycget(index, "label")
            entry = ttk.Button(
                frame, name=f"entry{index}", text=f"{label}  ▶" if kind == "cascade" else label,
                style="Settings.Toolbutton", compound=tk.LEFT, image=self._check_icons[0],
                command=lambda selected=index: self._invoke(menu, selected),
            )
            entry.bind("<Return>", self._keyboard_invoke)
            entry.bind("<ButtonRelease-1>", self._button_release)
            if kind == "checkbutton":
                checked = menu.tk.getboolean(menu.tk.globalgetvar(menu.entrycget(index, "variable")))
                entry.configure(
                    image=self._check_icons[checked],
                    command=lambda selected=index, row=entry: self._toggle_check(menu, selected, row),
                )
            elif kind == "cascade":
                self._submenu = ttk.Frame(self, name="submenu")
                self._submenu_row = entry
                self._build_entries(self._submenu, menu.nametowidget(menu.entrycget(index, "menu")))
                entry.configure(command=self._show_submenu)
                entry.bind("<Enter>", lambda event: self._show_submenu())
                entry.bind("<Right>", lambda event: self._show_submenu())
            entry.pack(fill=tk.X)
            if frame == self._menu and kind != "cascade":
                entry.bind("<Enter>", lambda event: self._hide_submenu())
            if menu.entrycget(index, "state") == tk.DISABLED:
                entry.configure(state=tk.DISABLED)

    def post(self, x: int, y: int) -> None:
        self.update_idletasks()
        left, top, right, bottom = _monitor_bounds(self.master, x, y)
        height = self.winfo_reqheight()
        if self._submenu is not None:
            height = max(height, self._submenu_row.winfo_y() + self._submenu.winfo_reqheight() + 2 * int(self.cget("borderwidth")))
        self._x = max(left, min(x, right - self.winfo_reqwidth()))
        self._y = max(top, min(y, bottom - height))
        self._opens_left = self._submenu is not None and self._x + self.winfo_reqwidth() + self._submenu.winfo_reqwidth() > right
        self._menu.grid_configure(column=1 if self._opens_left else 0)
        self._place()
        self.deiconify()
        self.update_idletasks()
        self.grab_set()
        self.focus_force()

    def _place(self) -> None:
        self.update_idletasks()
        x = self._x - self._submenu.winfo_reqwidth() if self._opens_left and self._submenu.winfo_manager() else self._x
        self.geometry(f"+{x}+{self._y}")

    def _show_submenu(self) -> None:
        self._submenu.grid(
            row=0, column=0 if self._opens_left else 1, sticky=tk.NW,
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

    def _toggle_check(self, menu: tk.Menu, index: int, row: ttk.Button) -> None:
        variable = menu.entrycget(index, "variable")
        checked = not menu.tk.getboolean(menu.tk.globalgetvar(variable))
        menu.tk.globalsetvar(variable, checked)
        row.configure(image=self._check_icons[checked])
        menu.tk.call(menu.entrycget(index, "command"))

    def _invoke(self, menu: tk.Menu, index: int) -> None:
        self.close()
        menu.invoke(index)

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
        self._on_close()
        self.grab_release()
        self.destroy()
        self._check_icons.clear()
        self._menu = None
        self._submenu = None
        self._submenu_row = None
