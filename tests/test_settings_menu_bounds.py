"""通过公开弹层观察 Linux 工作区、高 DPI 和条目操作。"""

from __future__ import annotations

import ctypes
import os
import struct
import sys
import tkinter as tk
from dataclasses import replace

import pytest

from shudu.settings_menu import (
    CommandItem,
    SettingsMenuState,
    TechniqueItem,
    open_settings,
)

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux") or not os.environ.get("DISPLAY"),
    reason="需要 Linux X11 显示环境",
)


class NativeCall:
    """替换 Xlib 的外部调用，保留 ctypes 函数的类型声明接口。"""

    def __init__(self, function):
        self.function = function

    def __call__(self, *args):
        return self.function(*args)


class X11Display:
    def __init__(self, properties):
        self.properties = properties
        self.atoms = {}
        self.buffers = []
        self.XOpenDisplay = NativeCall(lambda name: 1)
        self.XDefaultRootWindow = NativeCall(lambda display: 1)
        self.XCloseDisplay = NativeCall(lambda display: 0)
        self.XFree = NativeCall(lambda data: 0)
        self.XInternAtom = NativeCall(self.atom)
        self.XGetWindowProperty = NativeCall(self.property)
        self.XRRGetMonitors = NativeCall(self.monitors)
        self.XRRFreeMonitors = NativeCall(lambda data: None)
        self.screens = ((0, 0, 600, 400), (600, 0, 600, 400))

    def atom(self, display, name, only_if_exists):
        name = name.decode()
        if name not in self.properties:
            return 0
        self.atoms.setdefault(name, len(self.atoms) + 1)
        return self.atoms[name]

    def property(
        self,
        display,
        window,
        atom,
        offset,
        length,
        delete,
        requested_type,
        actual_type,
        actual_format,
        count,
        remaining,
        data,
    ):
        name = next(name for name, value in self.atoms.items() if value == atom)
        values = self.properties[name]
        buffer = (ctypes.c_ulong * len(values))(*values)
        self.buffers.append(buffer)
        actual_type._obj.value = 6  # XA_CARDINAL，来自 X11 协议。
        actual_format._obj.value = 32
        count._obj.value = len(values)
        remaining._obj.value = 0
        data._obj.value = ctypes.addressof(buffer)
        return 0

    def monitors(self, display, window, active, count):
        # XRRMonitorInfo 的系统 ABI；预期区域直接取自屏幕 fixture。
        records = b"".join(
            struct.pack(
                "@L9i4xP",
                index + 1,
                int(index == 0),
                1,
                0,
                x,
                y,
                width,
                height,
                200,
                140,
                0,
            )
            for index, (x, y, width, height) in enumerate(self.screens)
        )
        buffer = ctypes.create_string_buffer(records)
        self.buffers.append(buffer)
        count._obj.value = len(self.screens)
        return ctypes.addressof(buffer)


@pytest.fixture
def desktop(monkeypatch):
    root = tk.Tk()
    root.tk.call("tk", "scaling", 8 / 3)
    root.update()
    display = X11Display({"_GTK_WORKAREAS_D0": (0, 0, 600, 400, 600, 0, 600, 400)})
    monkeypatch.setattr(ctypes, "CDLL", lambda name: display)
    try:
        yield root, display
    finally:
        root.destroy()


def menu_state():
    return SettingsMenuState(
        auto_solve=True,
        auto_clean=True,
        techniques=(TechniqueItem("hidden_single", "Hidden Single", True),),
        commands=(CommandItem("help", "操作说明"),),
    )


def test_popup_stays_in_pointer_monitor_workarea(desktop):
    root, _ = desktop
    popup = open_settings(
        root,
        menu_state(),
        lambda action: None,
        lambda action: None,
        lambda: None,
        (590, 390),
    )
    try:
        root.update()
        assert (
            0 <= popup.winfo_rootx() < popup.winfo_rootx() + popup.winfo_width() <= 600
        )
        assert (
            0 <= popup.winfo_rooty() < popup.winfo_rooty() + popup.winfo_height() <= 400
        )
    finally:
        popup.close()


def expanded_state():
    return replace(
        menu_state(),
        techniques=tuple(
            TechniqueItem(f"technique_{index}", f"Technique number {index}", False)
            for index in range(10)
        ),
    )


def test_expanded_menu_fits_small_workarea_at_high_dpi(desktop):
    root, _ = desktop
    popup = open_settings(
        root,
        expanded_state(),
        lambda action: None,
        lambda action: None,
        lambda: None,
        (590, 390),
    )
    try:
        popup.nametowidget("menu.auto_technique").event_generate("<Enter>")
        root.update()
        assert (
            0 <= popup.winfo_rootx() < popup.winfo_rootx() + popup.winfo_width() <= 600
        )
        assert (
            0 <= popup.winfo_rooty() < popup.winfo_rooty() + popup.winfo_height() <= 400
        )
    finally:
        popup.close()


def test_keyboard_reveals_and_selects_last_scrolled_algorithm(desktop):
    root, _ = desktop
    selected = []
    popup = open_settings(
        root,
        expanded_state(),
        selected.append,
        lambda action: None,
        lambda: None,
        (590, 390),
    )
    try:
        popup.nametowidget("menu.auto_technique").event_generate("<Enter>")
        root.update()
        row = popup.nametowidget("submenu.auto_technique_technique_9")
        row.focus_set()
        root.update()
        viewport = next(
            child for child in popup.winfo_children() if isinstance(child, tk.Canvas)
        )
        assert viewport.winfo_rooty() <= row.winfo_rooty()
        assert (
            row.winfo_rooty() + row.winfo_height()
            <= viewport.winfo_rooty() + viewport.winfo_height()
        )
        row.event_generate("<Return>")
        root.update()
        assert selected[-1].name == "technique_9" and selected[-1].enabled
        assert popup.winfo_ismapped()
    finally:
        popup.close()


def test_mouse_wheel_reveals_last_algorithm_without_closing_menu(desktop):
    root, _ = desktop
    selected = []
    popup = open_settings(
        root,
        expanded_state(),
        selected.append,
        lambda action: None,
        lambda: None,
        (590, 390),
    )
    try:
        popup.nametowidget("menu.auto_technique").event_generate("<Enter>")
        root.update()
        row = popup.nametowidget("submenu.auto_technique_technique_9")
        before = row.winfo_rooty()
        popup.event_generate("<Button-5>", x=10, y=10)
        root.update()
        assert row.winfo_rooty() < before
        viewport = next(
            child for child in popup.winfo_children() if isinstance(child, tk.Canvas)
        )
        assert (
            row.winfo_rooty() + row.winfo_height()
            <= viewport.winfo_rooty() + viewport.winfo_height()
        )
        row.event_generate("<Enter>")
        row.event_generate("<ButtonPress-1>", x=20, y=20)
        row.event_generate("<ButtonRelease-1>", x=20, y=20)
        root.update()
        assert selected[-1].name == "technique_9" and selected[-1].enabled
        assert popup.winfo_ismapped()
    finally:
        popup.close()


def test_scrolled_main_menu_keeps_hovered_command_in_place(desktop):
    root, _ = desktop
    commands, closed = [], []
    state = replace(
        menu_state(),
        commands=tuple(
            CommandItem("level", f"Level {index}", index) for index in range(10)
        )
        + (CommandItem("help", "操作说明"),),
    )
    popup = open_settings(
        root,
        state,
        lambda action: None,
        commands.append,
        lambda: closed.append(True),
        (590, 390),
    )
    try:
        root.update()
        viewport = next(
            child for child in popup.winfo_children() if isinstance(child, tk.Canvas)
        )
        viewport.yview_moveto(1)
        root.update()
        row = popup.nametowidget("menu.help")
        before = row.winfo_rooty()
        assert popup.winfo_rooty() <= before
        assert before + row.winfo_height() <= popup.winfo_rooty() + popup.winfo_height()
        row.event_generate("<Leave>", x=-1, y=-1)
        row.event_generate("<Enter>", x=20, y=20)
        root.update()
        assert row.winfo_rooty() == before
        row.event_generate("<ButtonPress-1>", x=20, y=20)
        row.event_generate("<ButtonRelease-1>", x=20, y=20)
        root.update()
        assert commands[0].item.kind == "help"
        assert closed == [True] and root.grab_current() is None
    finally:
        popup.close()


@pytest.mark.parametrize("width", [1200, 600])
def test_bottom_edge_expansion_keeps_algorithm_row_at_hover_position(desktop, width):
    root, display = desktop
    display.screens = ((0, 0, width, 700),)
    display.properties["_GTK_WORKAREAS_D0"] = (0, 0, width, 700)
    state = replace(
        expanded_state(),
        commands=(
            CommandItem("import_screenshot", "从截图导入"),
            CommandItem("restart", "重新开始"),
            *(CommandItem("level", f"Level {index}", index) for index in range(3)),
            CommandItem("help", "操作说明"),
        ),
    )
    popup = open_settings(
        root,
        state,
        lambda action: None,
        lambda action: None,
        lambda: None,
        (width - 10, 690),
    )
    try:
        root.update()
        row = popup.nametowidget("menu.auto_technique")
        before = (row.winfo_rootx(), row.winfo_rooty())
        row.event_generate("<Enter>", x=20, y=20)
        root.update()
        assert popup.nametowidget("submenu").winfo_ismapped()
        assert row.winfo_rooty() == before[1]
        if width == 1200:
            assert row.winfo_rootx() == before[0]
        assert popup.winfo_rooty() + popup.winfo_height() <= 700
    finally:
        popup.close()


def test_missing_workarea_uses_pointer_screen_geometry(desktop):
    root, display = desktop
    display.properties.clear()
    popup = open_settings(
        root,
        menu_state(),
        lambda action: None,
        lambda action: None,
        lambda: None,
        (1190, 390),
    )
    try:
        root.update()
        assert (
            600
            <= popup.winfo_rootx()
            < popup.winfo_rootx() + popup.winfo_width()
            <= 1200
        )
        assert (
            0 <= popup.winfo_rooty() < popup.winfo_rooty() + popup.winfo_height() <= 400
        )
    finally:
        popup.close()


def test_pointer_over_panel_keeps_menu_on_its_monitor(desktop):
    root, display = desktop
    display.properties["_GTK_WORKAREAS_D0"] = (0, 0, 600, 400, 680, 0, 520, 400)
    popup = open_settings(
        root,
        menu_state(),
        lambda action: None,
        lambda action: None,
        lambda: None,
        (620, 390),
    )
    try:
        root.update()
        assert (
            680
            <= popup.winfo_rootx()
            < popup.winfo_rootx() + popup.winfo_width()
            <= 1200
        )
    finally:
        popup.close()


def test_standard_workarea_respects_current_desktop_and_panel(desktop):
    root, display = desktop
    display.properties = {
        "_NET_CURRENT_DESKTOP": (1,),
        "_NET_WORKAREA": (0, 20, 1200, 380, 0, 40, 1200, 360),
    }
    popup = open_settings(
        root,
        menu_state(),
        lambda action: None,
        lambda action: None,
        lambda: None,
        (1190, 0),
    )
    try:
        root.update()
        assert (
            600
            <= popup.winfo_rootx()
            < popup.winfo_rootx() + popup.winfo_width()
            <= 1200
        )
        assert (
            40
            <= popup.winfo_rooty()
            < popup.winfo_rooty() + popup.winfo_height()
            <= 400
        )
    finally:
        popup.close()


def test_display_query_failure_leaves_no_popup_or_grab(desktop):
    root, display = desktop
    display.XOpenDisplay = NativeCall(lambda name: 0)
    before = root.winfo_children()
    closed = []
    with pytest.raises(tk.TclError, match="无法连接 X11"):
        open_settings(
            root,
            menu_state(),
            lambda action: None,
            lambda action: None,
            lambda: closed.append(True),
            (590, 390),
        )
    assert root.winfo_children() == before
    assert root.grab_current() is None
    assert closed == [True]


def test_missing_x11_library_is_a_clear_popup_error(desktop, monkeypatch):
    root, _ = desktop

    def unavailable(name):
        raise OSError("missing X11 library")

    monkeypatch.setattr(ctypes, "CDLL", unavailable)
    with pytest.raises(tk.TclError, match="无法查询 Linux 显示器工作区"):
        open_settings(
            root,
            menu_state(),
            lambda action: None,
            lambda action: None,
            lambda: None,
            (590, 390),
        )
    assert root.winfo_children() == [] and root.grab_current() is None
