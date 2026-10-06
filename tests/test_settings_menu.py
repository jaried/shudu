"""设置菜单 Deep Module 的 action/state 和真实 Tk 生命周期契约。"""

from __future__ import annotations

import tkinter as tk

from shudu.settings_menu import (
    CommandItem,
    SettingsMenuState,
    TechniqueItem,
    open_settings,
)


def state() -> SettingsMenuState:
    return SettingsMenuState(
        auto_solve=True,
        auto_clean=True,
        techniques=(
            TechniqueItem("hidden_single", "Hidden Single", True),
            TechniqueItem("x_wing", "X-Wing", False),
        ),
        commands=(
            CommandItem("import_screenshot", "从截图导入…"),
            CommandItem("restart", "重新开始当前关卡"),
            CommandItem("help", "操作说明"),
        ),
    )


def test_state_action_keys_are_business_names():
    current = state()
    current.validate()
    assert current.techniques[1].action_key == "auto_technique:x_wing"
    assert current.commands[0].action_key == "import_screenshot"


def test_popup_uses_action_names_and_setting_keeps_popup_open():
    root = tk.Tk()
    settings = []
    commands = []
    closed = []
    try:
        popup = open_settings(root, state(), settings.append, commands.append, lambda: closed.append(True), (20, 20))
        root.update()
        popup.nametowidget("menu.auto_solve").invoke()
        assert settings[-1].action_key == "auto_solve"
        assert popup.winfo_ismapped()
        popup.nametowidget("submenu.auto_technique_x_wing").invoke()
        assert settings[-1].action_key == "auto_technique:x_wing"
        assert popup.winfo_ismapped()
        popup.nametowidget("menu.restart").invoke()
        root.update()
        assert commands[-1].action_key == "restart"
        assert closed == [True]
        popup.close()
        assert closed == [True]
    finally:
        root.destroy()
