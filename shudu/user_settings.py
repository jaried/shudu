"""持久化桌面端用户偏好。
Module 隐藏跨平台配置路径、JSON 兼容、校验和原子写入细节。
当前 Interface 只暴露完整 UserSettings 的 load/save，避免 GUI 理解文件格式。
本模块不依赖 Game、View 或 Tkinter。
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys

from shudu.auto_techniques import (
    AUTO_TECHNIQUE_NAMES,
    DEFAULT_AUTO_TECHNIQUES,
    validate_auto_techniques,
)

SETTINGS_VERSION = 1


@dataclass(frozen=True)
class UserSettings:
    auto_techniques: frozenset[str] = DEFAULT_AUTO_TECHNIQUES

    @classmethod
    def from_auto_techniques(cls, names) -> "UserSettings":
        values = frozenset(validate_auto_techniques(names))
        result = cls(values)
        return result


class UserSettingsStore:
    """本地 JSON 偏好存储；文件格式和落盘策略对调用方不可见。"""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else _default_settings_path()
        return

    def load(self) -> UserSettings:
        """读取偏好；文件不存在或内容损坏时回到产品默认配置。"""
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return UserSettings()
        try:
            payload = json.loads(text)
            result = _decode_settings(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
            result = UserSettings()
        return result

    def save(self, settings: UserSettings) -> None:
        """使用同目录临时文件 + replace 原子保存完整偏好。"""
        validated = UserSettings.from_auto_techniques(settings.auto_techniques)
        payload = {
            "version": SETTINGS_VERSION,
            "auto_techniques": [
                name
                for name in AUTO_TECHNIQUE_NAMES
                if name in validated.auto_techniques
            ],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.tmp")
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, self.path)
        return


def _decode_settings(payload) -> UserSettings:
    if not isinstance(payload, dict):
        raise ValueError("配置根节点必须是对象")
    names = payload.get("auto_techniques")
    if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
        raise ValueError("auto_techniques 必须是字符串列表")
    known = frozenset(name for name in names if name in AUTO_TECHNIQUE_NAMES)
    result = UserSettings(known)
    return result


def _default_settings_path() -> Path:
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Roaming"
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        base = os.environ.get("XDG_CONFIG_HOME")
        root = Path(base) if base else Path.home() / ".config"
    result = root / "shudu" / "settings.json"
    return result
