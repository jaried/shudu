"""定义自动逻辑算法的稳定目录。
算法顺序、界面标签和默认勾选状态只有这一份生产真源。
求解器、Game 与本地偏好都通过这个 Module 共享配置语义。
本模块不执行求解、不访问 GUI，也不进行文件 IO。
"""

from __future__ import annotations

from collections.abc import Iterable

AUTO_TECHNIQUE_SPECS = (
    ("hidden_single", "Hidden Single", True),
    ("naked_single", "Naked Single", True),
    ("naked_pair", "Naked Pair", True),
    ("hidden_pair", "Hidden Pair", False),
    ("naked_triple", "Naked Triple", True),
    ("pointing_pair", "Pointing Pair", True),
    ("box_line_reduction", "Box-Line Reduction", False),
    ("x_wing", "X-Wing", False),
    ("xy_wing", "XY-Wing", False),
)
AUTO_TECHNIQUE_NAMES = tuple(name for name, _, _ in AUTO_TECHNIQUE_SPECS)
DEFAULT_AUTO_TECHNIQUES = frozenset(
    name
    for name, _, enabled_by_default in AUTO_TECHNIQUE_SPECS
    if enabled_by_default
)


def validate_auto_techniques(names: Iterable[str]) -> set[str]:
    """校验算法配置并返回可修改集合。"""
    result = set(names)
    if any(not isinstance(name, str) for name in result):
        raise ValueError("自动算法名称必须是字符串")
    unknown = result.difference(AUTO_TECHNIQUE_NAMES)
    if unknown:
        raise ValueError(f"未知自动算法：{', '.join(sorted(unknown))}")
    return result
