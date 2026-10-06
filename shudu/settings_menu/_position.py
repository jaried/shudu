"""设置弹层的显示器工作区定位。"""

from __future__ import annotations

import sys
import tkinter as tk


def monitor_bounds(root: tk.Misc, x: int, y: int) -> tuple[int, int, int, int]:
    if sys.platform == "win32":
        import ctypes
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
    return (
        root.winfo_vrootx(),
        root.winfo_vrooty(),
        root.winfo_vrootx() + root.winfo_vrootwidth(),
        root.winfo_vrooty() + root.winfo_vrootheight(),
    )
