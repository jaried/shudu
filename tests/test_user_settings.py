"""验证自动算法偏好的本地持久化 Interface。
测试只通过 UserSettingsStore 的 load/save 观察行为。
配置损坏时回到产品默认，未来未知算法不会污染当前运行。
测试使用临时目录，不访问真实用户配置目录。
"""

import json

from shudu.auto_techniques import DEFAULT_AUTO_TECHNIQUES
from shudu.user_settings import UserSettings, UserSettingsStore


def test_missing_settings_uses_product_defaults(tmp_path):
    store = UserSettingsStore(tmp_path / "settings.json")
    assert store.load().auto_techniques == DEFAULT_AUTO_TECHNIQUES


def test_settings_round_trip_preserves_exact_selection(tmp_path):
    path = tmp_path / "settings.json"
    store = UserSettingsStore(path)
    settings = UserSettings.from_auto_techniques({"x_wing", "hidden_pair"})
    store.save(settings)
    assert store.load() == settings
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["auto_techniques"] == ["hidden_pair", "x_wing"]


def test_corrupt_settings_falls_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{bad-json", encoding="utf-8")
    store = UserSettingsStore(path)
    assert store.load().auto_techniques == DEFAULT_AUTO_TECHNIQUES


def test_unknown_future_algorithm_is_ignored(tmp_path):
    path = tmp_path / "settings.json"
    payload = {
        "version": 99,
        "auto_techniques": ["x_wing", "future-technique"],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    store = UserSettingsStore(path)
    assert store.load().auto_techniques == frozenset({"x_wing"})
