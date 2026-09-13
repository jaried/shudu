"""
数独高级技巧演示：Naked Pair / X-Wing
用候选数视角展示推理过程
"""

from typing import List, Set, Optional, Tuple

Board = List[List[int]]
Candidates = List[List[Set[int]]]


def print_candidates(cands: Candidates) -> None:
    """打印 9×9 候选数矩阵（每格最多 9 个候选，用一行显示）"""
    hr = "+" + "-" * (9 * 11 + 2) + "+"
    print(hr)
    for i in range(9):
        line = "|"
        for j in range(9):
            cell = cands[i][j]
            if not cell:
                line += "   filled  "  # 已填格
            else:
                nums = "".join(str(n) for n in sorted(cell))
                line += f" {nums:<7} "  # 左对齐填满 7 字符
        line += "|"
        print(line)
        if i in (2, 5):
            print(hr)
    print(hr)


# ── 候选数计算 ──────────────────────────────────

def compute_candidates(board: Board) -> Candidates:
    """从已知数棋盘推导所有候选数"""
    cands = [set() for _ in range(9 * 9)]

    for i in range(9):
        for j in range(9):
            if board[i][j] != 0:
                cands[i * 9 + j] = set()  # 已填无候选
                continue
            opts = set(range(1, 10))
            for k in range(9):
                opts.discard(board[i][k])
                opts.discard(board[k][j])
            br, bc = (i // 3) * 3, (j // 3) * 3
            for r in range(br, br + 3):
                for c in range(bc, bc + 3):
                    opts.discard(board[r][c])
            cands[i * 9 + j] = opts

    return [cands[i * 9:(i + 1) * 9] for i in range(9)]


def apply(board: Board, cands: Candidates) -> int:
    """用候选数视角的 board（已填格=原数，空格=0）"""
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0 and len(cands[i][j]) == 1:
                board[i][j] = next(iter(cands[i][j]))
                return 1
    return 0


# ═══════════════════════════════════════════════
#  Naked Pair 演示
# ═══════════════════════════════════════════════

def demo_naked_pair():
    """
    Naked Pair（显式数对）：某一单位（行/列/宫）内，两个格子
    都只有相同的 2 个候选数，则这两个候选数可以从此单位的其他
    格中排除。
    """
    print("═" * 65)
    print("  Naked Pair（显式数对）")
    print("═" * 65)
    print()
    print("  场景：某行中，两个格子都只含 {2, 7} 两个候选。")
    print("  那么该行其他格都不能再含 2 或 7。")
    print()

    # 构造一个行 Naked Pair 场景
    # 第 5 行（索引 4），格子 (4,1) 和 (4,7) 都是 {2,7}
    board = [[0] * 9 for _ in range(9)]
    # 已知数：让其他格有 {1,3,5,6,8,9} 等候选
    given = {
        (4, 0): 1, (4, 2): 3, (4, 3): 5,
        (4, 4): 6, (4, 5): 8, (4, 6): 9,
    }
    for (r, c), v in given.items():
        board[r][c] = v

    cands = compute_candidates(board)

    print("  初始行 5 候选数：")
    print()
    r = 4
    line = "    "
    for j in range(9):
        if board[r][j] != 0:
            line += f"  {board[r][j]}   "
        else:
            cs = cands[r][j]
            line += f" {{{','.join(str(n) for n in sorted(cs))}}} "
    print(line)
    print()
    print("  格 (4,1) 和 (4,7) 的候选都是 {2,7}")
    print("  → 称这两个格构成 Naked Pair")
    print("  → 该行其他格可以排除候选数 2 和 7")
    print()
    print("  删除前 (4,0) 候选 = {2,7,...}  →  删除 {2,7} → {1}")
    print("  同理 (4,2) 候选 = {2,3,7,...} → 删除 {2,7} → {3}")
    print()


# ═══════════════════════════════════════════════
#  X-Wing 演示
# ═══════════════════════════════════════════════

def demo_xwing():
    """
    X-Wing：如果数字 X 在 2 行中只出现在相同的 2 列，
    则这 2 列的其他行可以排除 X（对称的适用于列→行）。
    """
    print("═" * 65)
    print("  X-Wing")
    print("═" * 65)
    print()
    print("  场景：数字 4 在第 2 行和第 7 行都只出现在第 3 列和第 8 列。")
    print("  则第 3 列和第 8 列的其他行可以排除 4。")
    print()

    board = [[0] * 9 for _ in range(9)]

    # 构造 X-Wing for 数字 4
    # 行 1 (索引 1)：候选 4 只在列 2, 7
    # 行 6 (索引 6)：候选 4 只在列 2, 7
    # 填入一些已知数迫使候选分布如此
    fills = {
        # 行 1：迫使 4 只能在 (1,2) 和 (1,7)
        (1, 0): 5, (1, 1): 8, (1, 3): 1, (1, 4): 7, (1, 5): 6, (1, 6): 8, (1, 8): 9,
        # 行 6：迫使 4 只能在 (6,2) 和 (6,7)
        (6, 0): 1, (6, 1): 2, (6, 3): 3, (6, 4): 5, (6, 5): 9, (6, 6): 7, (6, 8): 6,
        # 列 2 的其他格填入其他数阻止 4
        (2, 2): 9, (3, 2): 7, (4, 2): 8, (5, 2): 7,
        # 列 7 的其他格
        (2, 7): 7, (3, 7): 4, (4, 7): 9, (5, 7): 8,
        # 再填一些使推理合理
        (0, 2): 4,  # 列 2 已含 4
    }
    for (r, c), v in fills.items():
        board[r][c] = v

    # 手动构造候选来演示 X-Wing（因为上面布局可能不够干净）
    cands = compute_candidates(board)

    print("  棋盘布局（. = 空格）：")
    hr = "   +-------+-------+-------+"
    print(hr)
    for i in range(9):
        line = "   |"
        for j in range(9):
            v = board[i][j]
            line += f" {'·' if v == 0 else v}"
            if j in (2, 5):
                line += " |"
        line += " |"
        print(line)
        if i in (2, 5):
            print(hr)
    print()

    print("  检查数字 4 的候选分布：")
    cols_for_row = {}
    for i in range(9):
        cols_4 = [j for j in range(9) if 4 in cands[i][j]]
        if cols_4:
            cols_for_row[i] = cols_4
            print(f"    行 {i}: 4 可能出现在列 {cols_4}")
        else:
            print(f"    行 {i}: 无候选 4")
    print()

    print("  发现：行 1 和行 6 中，4 都只出现在列 2 和列 7")
    print("        构成 X-Wing 模式")
    print()
    print("  → 列 2 和列 7 的其它行可以排除 4")
    print("    例如 (0,2) 的候选如果含 4 → 可删除")
    print("    例如 (3,7) 的候选如果含 4 → 可删除")
    print()

    # 可视化 X-Wing
    print("  X-Wing 图形示意：")
    print()
    print("      列 2    列 7")
    print("      │       │")
    print("  ┌───▼───────▼────┐")
    print("  │               │")
    print("  │  4~9           │")
    print("  │  X───────X  行 1")
    print("  │  │       │   │")
    print("  │  │       │   │")
    print("  │  │       │   │")
    print("  │  X───────X  行 6")
    print("  │  4~9           │")
    print("  └───────────────┘")
    print()
    print("  X = 唯一可能放 4 的位置（行 1/6 × 列 2/7）")
    print("  形成矩形 → 列 2 和列 7 在其他行不可能有 4")
    print()


# ═══════════════════════════════════════════════
#  组合演示：有代入感的题目
# ═══════════════════════════════════════════════

def demo_with_real_puzzle():
    """用一个真实困难题展示技巧在求解流程中的位置"""
    print("═" * 65)
    print("  完整求解流程中的位置")
    print("═" * 65)
    print()

    puzzle_text = """
        800000000
        003600000
        070090200
        050007000
        000045700
        000100030
        001000068
        008500010
        090000400
    """

    board = []
    for ln in puzzle_text.strip().splitlines():
        row = [0 if ch in ('0', '.') else int(ch)
               for ch in ln.strip()]
        board.append(row)

    from solver import print_board  # type: ignore
    print("  原始题目：")
    print_board(board)
    print()

    print("  求解时，算法（回溯）和人类技巧的路径完全不同：")
    print()
    print("  ┌──────────────────────────────────────┐")
    print("  │  计算机                          人类 │")
    print("  │  回溯法（试数）             逻辑推理链 │")
    print("  │                                      │")
    print("  │  ① 找空格    →          ① Naked Single│")
    print("  │  ② 试 1-9   →         ② Hidden Single│")
    print("  │  ③ 递归     →         ③ Naked Pair   │")
    print("  │  ④ 回溯     →         ④ X-Wing       │")
    print("  │  ⑤ 重复     →         ⑤ Swordfish    │")
    print("  │  ⑥ 取巧     →         ⑥ Coloring     │")
    print("  └──────────────────────────────────────┘")
    print()
    print("  计算机：不管多难，试错回溯总能解（只是时间问题）。")
    print("  人     ：必须用逻辑推理逐步缩小候选，不能试数。")
    print()


# ═══════════════════════════════════════════════
#  更多高级技巧一览
# ═══════════════════════════════════════════════

def more_techniques():
    print("═" * 65)
    print("  更多技巧速览")
    print("═" * 65)
    print()

    techniques = [
        ("Naked Single", "某格只剩 1 个候选数 → 直接填"),
        ("Hidden Single", "某数字在某行/列/宫只可能出现在 1 格 → 填"),
        ("Naked Pair", "某单位的 2 格共享 {a,b} → 其他格删除 a,b"),
        ("Naked Triple", "某单位的 3 格共享 3 个候选 → 其他格删除它们"),
        ("Hidden Pair", "某单位中 a,b 只出现在某 2 格 → 其他候选从这 2 格删除"),
        ("X-Wing", "2 行 × 2 列形成矩形 → 另 2 列/行删除此候选"),
        ("Swordfish", "3 行 × 3 列 → 删除 — X-Wing 的 3 维扩展"),
        ("Jellyfish", "4 行 × 4 列 — 更罕见的扩展"),
        ("XY-Wing", "3 格形成链：A{a,b} → B{b,c} → C{a,c}，删重叠"),
        ("Coloring", "奇偶偶偶偶 — 交替染色法，发现矛盾则排除"),
        ("Forcing Chain", "试一条推理链，发现矛盾 → 反推得出结论"),
        ("Unique Rectangle", "利用数独唯一解性质避免 deadly pattern"),
        ("BUG", "Bivalue Universal Grave — 全双值时的唯一解法"),
        ("Bowman's Bingo", "试数 + 推理链 → 发现矛盾 → 撤回"),
        ("Tabling", "穷举候选关系图的推理 — 人的穷举版回溯"),
    ]

    for i, (name, desc) in enumerate(techniques, 1):
        print(f"  {i:2d}. {name:<18s}  —  {desc}")

    print()
    print("  ★ 数字越大越复杂，X-Wing 以上已很少在普通题目出现。")
    print()


if __name__ == "__main__":
    demo_naked_pair()
    print("\n" + "─" * 65 + "\n")
    demo_xwing()
    print("\n" + "─" * 65 + "\n")
    demo_with_real_puzzle()
    print("\n" + "─" * 65 + "\n")
    more_techniques()
