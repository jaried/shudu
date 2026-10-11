"""设置弹层的显示器工作区定位。"""

from __future__ import annotations

import ctypes
import sys
import tkinter as tk


def monitor_bounds(root: tk.Misc, x: int, y: int) -> tuple[int, int, int, int]:
    if sys.platform == "win32":
        from ctypes import wintypes

        class MonitorInfo(ctypes.Structure):
            _fields_ = [
                ("size", wintypes.DWORD),
                ("monitor", wintypes.RECT),
                ("work", wintypes.RECT),
                ("flags", wintypes.DWORD),
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
    if sys.platform.startswith("linux"):
        try:
            return _linux_bounds(root, x, y)
        except (OSError, AttributeError) as error:
            raise tk.TclError(f"无法查询 Linux 显示器工作区：{error}") from error
    return (
        root.winfo_vrootx(),
        root.winfo_vrooty(),
        root.winfo_vrootx() + root.winfo_vrootwidth(),
        root.winfo_vrooty() + root.winfo_vrootheight(),
    )


def _cardinals(xlib, display, window: int, name: str) -> list[int]:
    atom = xlib.XInternAtom(display, name.encode(), True)
    if not atom:
        return []
    actual_type = ctypes.c_ulong()
    actual_format = ctypes.c_int()
    count = ctypes.c_ulong()
    remaining = ctypes.c_ulong()
    data = ctypes.c_void_p()
    try:
        status = xlib.XGetWindowProperty(
            display,
            window,
            atom,
            0,
            4096,
            False,
            6,
            ctypes.byref(actual_type),
            ctypes.byref(actual_format),
            ctypes.byref(count),
            ctypes.byref(remaining),
            ctypes.byref(data),
        )
        if status != 0 or remaining.value:
            raise tk.TclError(f"无法完整读取 X11 工作区属性：{name}")
        if not count.value:
            return []
        if actual_type.value != 6 or actual_format.value != 32 or not data.value:
            raise tk.TclError(f"X11 工作区属性格式无效：{name}")
        values = ctypes.cast(data, ctypes.POINTER(ctypes.c_ulong))
        return [values[index] & 0xFFFFFFFF for index in range(count.value)]
    finally:
        if data.value:
            xlib.XFree(data)


class _MonitorInfo(ctypes.Structure):
    """Xrandr.h 中 XRRMonitorInfo 的原生布局。"""

    _fields_ = [
        ("name", ctypes.c_ulong),
        ("primary", ctypes.c_int),
        ("automatic", ctypes.c_int),
        ("noutput", ctypes.c_int),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("mwidth", ctypes.c_int),
        ("mheight", ctypes.c_int),
        ("outputs", ctypes.c_void_p),
    ]


def _screen_rectangles(display, window: int) -> list[tuple[int, int, int, int]]:
    randr = ctypes.CDLL("libXrandr.so.2")
    randr.XRRGetMonitors.argtypes = [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
    ]
    randr.XRRGetMonitors.restype = ctypes.c_void_p
    randr.XRRFreeMonitors.argtypes = [ctypes.c_void_p]
    randr.XRRFreeMonitors.restype = None
    count = ctypes.c_int()
    data = randr.XRRGetMonitors(display, window, True, ctypes.byref(count))
    if not data:
        raise tk.TclError("X11 未提供显示器几何信息")
    try:
        if count.value <= 0:
            raise tk.TclError("X11 未提供活动显示器")
        monitors = ctypes.cast(data, ctypes.POINTER(_MonitorInfo))
        areas = []
        for index in range(count.value):
            monitor = monitors[index]
            if monitor.width <= 0 or monitor.height <= 0:
                raise tk.TclError("X11 显示器尺寸无效")
            areas.append(
                (
                    monitor.x,
                    monitor.y,
                    monitor.x + monitor.width,
                    monitor.y + monitor.height,
                )
            )
        return areas
    finally:
        randr.XRRFreeMonitors(data)


def _nearest_area(
    areas: list[tuple[int, int, int, int]], x: int, y: int
) -> tuple[int, int, int, int]:
    return min(
        areas,
        key=lambda area: (
            max(area[0] - x, 0, x - area[2] + 1) ** 2
            + max(area[1] - y, 0, y - area[3] + 1) ** 2
        ),
    )


def _workarea_on_screen(
    screen: tuple[int, int, int, int],
    areas: list[tuple[int, int, int, int]],
) -> tuple[int, int, int, int]:
    intersections = []
    for area in areas:
        left, top = max(screen[0], area[0]), max(screen[1], area[1])
        right, bottom = min(screen[2], area[2]), min(screen[3], area[3])
        if left < right and top < bottom:
            intersections.append((left, top, right, bottom))
    if not intersections:
        raise tk.TclError("X11 工作区与当前显示器没有交集")
    return max(
        intersections, key=lambda area: (area[2] - area[0]) * (area[3] - area[1])
    )


def _linux_bounds(root: tk.Misc, x: int, y: int) -> tuple[int, int, int, int]:
    xlib = ctypes.CDLL("libX11.so.6")
    xlib.XOpenDisplay.argtypes = [ctypes.c_char_p]
    xlib.XOpenDisplay.restype = ctypes.c_void_p
    xlib.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    xlib.XDefaultRootWindow.restype = ctypes.c_ulong
    xlib.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    xlib.XInternAtom.restype = ctypes.c_ulong
    xlib.XGetWindowProperty.argtypes = [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_long,
        ctypes.c_long,
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.POINTER(ctypes.c_ulong),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_ulong),
        ctypes.POINTER(ctypes.c_ulong),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    xlib.XGetWindowProperty.restype = ctypes.c_int
    xlib.XFree.argtypes = [ctypes.c_void_p]
    xlib.XFree.restype = ctypes.c_int
    xlib.XCloseDisplay.argtypes = [ctypes.c_void_p]
    xlib.XCloseDisplay.restype = ctypes.c_int
    display = xlib.XOpenDisplay(root.winfo_screen().encode())
    if not display:
        raise tk.TclError("无法连接 X11 显示器以定位设置菜单")
    try:
        window = xlib.XDefaultRootWindow(display)
        screen = _nearest_area(_screen_rectangles(display, window), x, y)
        desktop = _cardinals(xlib, display, window, "_NET_CURRENT_DESKTOP")
        index = desktop[0] if desktop else 0
        values = _cardinals(xlib, display, window, f"_GTK_WORKAREAS_D{index}")
        if not values:
            values = _cardinals(xlib, display, window, "_NET_WORKAREA")
            if not values:
                return screen
            if len(values) % 4 or index >= len(values) // 4:
                raise tk.TclError("X11 当前桌面工作区无效")
            values = values[4 * index : 4 * index + 4]
        if len(values) % 4:
            raise tk.TclError("X11 未提供有效的显示器工作区")
        areas = []
        for offset in range(0, len(values), 4):
            left = ctypes.c_int32(values[offset]).value
            top = ctypes.c_int32(values[offset + 1]).value
            width, height = values[offset + 2 : offset + 4]
            if not width or not height:
                raise tk.TclError("X11 显示器工作区尺寸无效")
            areas.append((left, top, left + width, top + height))
        return _workarea_on_screen(screen, areas)
    finally:
        xlib.XCloseDisplay(display)
