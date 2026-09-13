"""
数独求解器 — 公共回溯能力演示入口
"""

from typing import List, Optional

from sudoku_backtracking import DEFAULT_BACKTRACKING_SOLVER

Board = List[List[Optional[int]]]


def print_board(board: Board) -> None:
    """漂亮地打印 9×9 数独棋盘"""
    hr = "+-------+-------+-------+"
    print(hr)
    for i in range(9):
        print("|", end=" ")
        for j in range(9):
            v = board[i][j]
            print(f"{v if v else '.'}", end=" ")
            if j in (2, 5):
                print("|", end=" ")
        print("|")
        if i in (2, 5):
            print(hr)
    print(hr)


def solve(board: Board) -> bool:
    """调用公共回溯能力，原位修改 board，返回是否有解。"""
    result = DEFAULT_BACKTRACKING_SOLVER.solve(board)
    if not result.solved or result.solution is None:
        return False

    for row in range(9):
        for col in range(9):
            board[row][col] = result.solution[row][col]
    return True


def solve_with_candidates(board: Board) -> bool:
    """兼容旧接口，内部统一复用公共 MRV 回溯实现。"""
    return solve(board)


# ── 测试用例 ────────────────────────────────────────

def empty_board() -> Board:
    """造一个 9×9 空棋盘"""
    return [[None] * 9 for _ in range(9)]


def parse(text: str) -> Board:
    """
    从文本解析数独，支持 0/. 表示空格，其他数字为已知数。
    示例 9 行文本，每行 9 个字符。
    """
    board = empty_board()
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    for i in range(min(9, len(lines))):
        row = lines[i]
        for j in range(min(9, len(row))):
            ch = row[j]
            if ch.isdigit() and ch != '0':
                board[i][j] = int(ch)
            else:
                board[i][j] = None
    return board


if __name__ == "__main__":
    # ── 世界最难数独之一 ──
    hardest = """
4......2.
..792..61
......3..
...3...97
58..9..3.
.....1...
7..6.9...
...4...8.
..6...5.3
    """

    print("═" * 30)
    print(" 基础回溯法")
    print("═" * 30)

    b1 = parse(hardest)
    print_board(b1)
    ok = solve(b1)
    print(f"\n→ {'有解' if ok else '无解'}")
    if ok:
        print_board(b1)

    print()
    print("═" * 30)
    print(" 候选数法（MRV 优化）")
    print("═" * 30)

    b2 = parse(hardest)
    ok2 = solve_with_candidates(b2)
    print(f"\n→ {'有解' if ok2 else '无解'}")
    if ok2:
        print_board(b2)
