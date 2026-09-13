"""让既有行为测试在目录迁移期间引用同一批内部 Module 对象。
生产代码不依赖这些别名；根目录只保留真正可执行入口。
别名仅保持测试文件的历史导入名，避免为目录整理复制生产兼容层。
架构测试直接检查 shudu 包中的真实文件与依赖方向。
"""

import importlib
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

_INTERNAL_MODULES = (
    "sudoku_backtracking",
    "sudoku_game",
    "sudoku_hint_view",
    "sudoku_hints",
    "sudoku_logic",
    "sudoku_njit_core",
    "sudoku_puzzles",
    "sudoku_rules",
    "sudoku_screenshot",
    "sudoku_step",
    "sudoku_theme",
    "sudoku_view",
)

for _name in _INTERNAL_MODULES:
    sys.modules[_name] = importlib.import_module(f"shudu.{_name}")
