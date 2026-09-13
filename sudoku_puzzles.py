"""定义游戏使用的题面。
默认题面逐格转录自用户提供的第三张截图。
挑战题复用仓库 solver.py 的回溯演示题。
本模块不保存答案，不实现另一套求解器。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Puzzle:
    title: str
    difficulty: str
    rows: tuple[str, ...]

    def grid(self) -> list[list[int]]:
        """严格检查形状与字符，避免旧解析入口静默截断输入。"""
        if len(self.rows) != 9 or any(len(row) != 9 for row in self.rows):
            raise ValueError("题面必须为 9 行，每行 9 格")
        if any(char not in "0123456789." for row in self.rows for char in row):
            raise ValueError("题面仅支持 1–9，以及表示空格的 0 或 .")
        result = [[0 if char == "." else int(char) for char in row] for row in self.rows]
        return result


SCREENSHOT_PUZZLE = Puzzle("关卡 108", "专家", (
    "....9.6.7",
    ".......1.",
    "9.7.2.53.",
    "4...5....",
    ".....8...",
    "13..4.79.",
    "6.89.....",
    ".1.5....2",
    ".......5.",
))

PRACTICE_PUZZLE = Puzzle("入门练习", "练习", (
    "53..7....", "6..195...", ".98....6.",
    "8...6...3", "4..8.3..1", "7...2...6",
    ".6....28.", "...419..5", "....8..79",
))

CHALLENGE_PUZZLE = Puzzle("回溯挑战", "挑战", (
    "4......2.", "..792..61", "......3..",
    "...3...97", "58..9..3.", ".....1...",
    "7..6.9...", "...4...8.", "..6...5.3",
))

PUZZLES = (SCREENSHOT_PUZZLE, PRACTICE_PUZZLE, CHALLENGE_PUZZLE)
