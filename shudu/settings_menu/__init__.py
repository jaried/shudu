"""设置菜单 Deep Module 的唯一公开入口。"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from ._model import (
    CommandAction,
    CommandItem,
    SettingAction,
    SettingsMenuState,
    TechniqueItem,
)
from ._popup import SettingsPopup


def open_settings(
    root: tk.Misc,
    state: SettingsMenuState,
    on_setting: Callable[[SettingAction], None],
    on_command: Callable[[CommandAction], None],
    on_close: Callable[[], None],
    pointer: tuple[int, int],
    font: tuple[str, int] = ("TkDefaultFont", 11),
) -> SettingsPopup:
    popup = SettingsPopup(root, state, on_setting, on_command, on_close, font=font)
    popup.post(*pointer)
    return popup


__all__ = [
    "CommandAction",
    "CommandItem",
    "SettingAction",
    "SettingsMenuState",
    "SettingsPopup",
    "TechniqueItem",
    "open_settings",
]
