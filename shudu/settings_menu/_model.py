"""设置菜单的业务快照、动作值域和条目模型。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SettingKind = Literal["auto_solve", "auto_technique", "auto_clean"]
CommandKind = Literal["import_screenshot", "restart", "level", "help"]


@dataclass(frozen=True)
class TechniqueItem:
    name: str
    label: str
    checked: bool

    @property
    def action_key(self) -> str:
        return f"auto_technique:{self.name}"


@dataclass(frozen=True)
class CommandItem:
    kind: CommandKind
    label: str
    value: object | None = None

    @property
    def action_key(self) -> str:
        if self.kind == "level":
            if self.value is None:
                raise ValueError("关卡命令必须提供关卡值")
            return f"level:{getattr(self.value, 'title', self.value)}"
        return self.kind


@dataclass(frozen=True)
class SettingsMenuState:
    auto_solve: bool
    auto_clean: bool
    techniques: tuple[TechniqueItem, ...]
    commands: tuple[CommandItem, ...]

    def validate(self) -> None:
        names = [item.name for item in self.techniques]
        if len(names) != len(set(names)) or any(not name for name in names):
            raise ValueError("自动算法名称必须唯一且非空")
        if any(not item.label for item in self.techniques):
            raise ValueError("自动算法标签不能为空")
        keys = [item.action_key for item in self.commands]
        if len(keys) != len(set(keys)):
            raise ValueError("设置命令必须唯一")
        for item in self.commands:
            if item.kind == "level" and item.value is None:
                raise ValueError("关卡命令必须提供关卡值")


@dataclass(frozen=True)
class SettingAction:
    kind: SettingKind
    enabled: bool
    name: str | None = None

    @property
    def action_key(self) -> str:
        if self.kind == "auto_technique":
            if self.name is None:
                raise ValueError("自动算法动作必须提供名称")
            return f"auto_technique:{self.name}"
        if self.name is not None:
            raise ValueError("设置动作名称只用于自动算法")
        return self.kind


@dataclass(frozen=True)
class CommandAction:
    item: CommandItem

    @property
    def action_key(self) -> str:
        return self.item.action_key


def action_widget_name(action_key: str) -> str:
    """把业务 action 映射为稳定的 Tk widget name。"""

    result = "".join(character if character.isalnum() else "_" for character in action_key)
    if not result or result[0].isdigit():
        result = f"action_{result}"
    return result
