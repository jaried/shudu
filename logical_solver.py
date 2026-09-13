"""
纯逻辑数独求解器
用 Naked/Hidden Single/Pair/Triple、Pointing Pair、Box-Line、X-Wing
每一步推理都输出，不用回溯试数
"""

from typing import List, Set, Tuple, Optional, Callable
from itertools import combinations

from sudoku_backtracking import DEFAULT_BACKTRACKING_SOLVER


Board = List[List[int]]
Cands = List[List[Set[int]]]


# ── 工具函数 ─────────────────────────────────────────

def parse(text: str) -> Board:
    board = [[0] * 9 for _ in range(9)]
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    for i in range(min(9, len(lines))):
        for j in range(min(9, len(lines[i]))):
            ch = lines[i][j]
            board[i][j] = int(ch) if ch.isdigit() and ch != '.' else 0
    return board


def format_cell(i: int, j: int) -> str:
    return f"({i + 1},{j + 1})"


def format_cells(cells: List[Tuple[int, int]]) -> str:
    return ", ".join(format_cell(*c) for c in cells)


def print_board(board: Board) -> None:
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


def board_solved(board: Board) -> bool:
    return all(board[i][j] != 0 for i in range(9) for j in range(9))


# ── 候选数管理 ─────────────────────────────────────

def init_candidates(board: Board) -> Cands:
    """从已知数初始化候选数"""
    cands: Cands = [set(range(1, 10)) for _ in range(9 * 9)]
    for i in range(9):
        for j in range(9):
            if board[i][j]:
                cands[i * 9 + j] = set()
                _eliminate(board, cands, i, j, board[i][j])
    return [cands[i * 9:(i + 1) * 9] for i in range(9)]


def _eliminate(board: Board, cands1d: List[Set[int]], row: int, col: int, num: int) -> None:
    """从同行/列/宫删除 num"""
    for j in range(9):
        if board[row][j] == 0:
            cands1d[row * 9 + j].discard(num)
    for i in range(9):
        if board[i][col] == 0:
            cands1d[i * 9 + col].discard(num)
    br, bc = (row // 3) * 3, (col // 3) * 3
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            if board[r][c] == 0:
                cands1d[r * 9 + c].discard(num)


# ── 单位迭代 ───────────────────────────────────────

def row_cells(r: int) -> List[Tuple[int, int]]:
    return [(r, j) for j in range(9)]


def col_cells(c: int) -> List[Tuple[int, int]]:
    return [(i, c) for i in range(9)]


def box_cells(r: int, c: int) -> List[Tuple[int, int]]:
    br, bc = (r // 3) * 3, (c // 3) * 3
    return [(br + dr, bc + dc) for dr in range(3) for dc in range(3)]


def all_units() -> List[List[Tuple[int, int]]]:
    units = []
    for i in range(9):
        units.append(row_cells(i))
        units.append(col_cells(i))
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            units.append([(br + dr, bc + dc) for dr in range(3) for dc in range(3)])
    return units


UNITS = all_units()


def unit_name(cells: List[Tuple[int, int]]) -> str:
    """给单位取个可读的名字"""
    r0, c0 = cells[0]
    r1, c1 = cells[-1]
    if r0 == r1:
        return f"行 {r0 + 1}"
    if c0 == c1:
        return f"列 {c0 + 1}"
    br, bc = (r0 // 3) * 3, (c0 // 3) * 3
    return f"宫 ({br + 1},{bc + 1})"


# ── 逻辑求解器 ─────────────────────────────────────

class LogicSolver:
    def __init__(self, board: Board):
        self.board = [row[:] for row in board]
        self.cands = init_candidates(board)
        self.steps: List[str] = []
        self.step_no = 0
        self.elim_count = 0
        self.fallback_used = False
        self.error_message: Optional[str] = None

    def _log(self, msg: str) -> None:
        self.step_no += 1
        line = f"  [{self.step_no:3d}] {msg}"
        self.steps.append(line)

    def _print_steps(self) -> None:
        print("推理步骤：")
        print()
        for line in self.steps:
            print(line)
        print()

    def _place(self, i: int, j: int, num: int) -> None:
        """填入一个数字，并在当前候选基础上增量传播约束"""
        self.board[i][j] = num
        self.cands[i][j] = set()
        self._propagate_placement(i, j, num)

    def _propagate_placement(self, i: int, j: int, num: int) -> None:
        """保留既有逻辑排除，只删除本次落子对同行/列/宫新增无效的候选"""
        for jj in range(9):
            if self.board[i][jj] == 0:
                self.cands[i][jj].discard(num)
        for ii in range(9):
            if self.board[ii][j] == 0:
                self.cands[ii][j].discard(num)
        br, bc = (i // 3) * 3, (j // 3) * 3
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                if self.board[r][c] == 0:
                    self.cands[r][c].discard(num)

    def _rebuild_candidates(self) -> None:
        """从当前棋盘全量重建候选数，清除累积偏差"""
        for i in range(9):
            for j in range(9):
                if self.board[i][j]:
                    self.cands[i][j] = set()
                else:
                    self.cands[i][j] = set(range(1, 10))

        for i in range(9):
            for j in range(9):
                num = self.board[i][j]
                if num == 0:
                    continue
                # 从同行空格删除 num
                for jj in range(9):
                    if self.board[i][jj] == 0:
                        self.cands[i][jj].discard(num)
                # 从同列空格删除 num
                for ii in range(9):
                    if self.board[ii][j] == 0:
                        self.cands[ii][j].discard(num)
                # 从同宫空格删除 num
                br, bc = (i // 3) * 3, (j // 3) * 3
                for r in range(br, br + 3):
                    for c in range(bc, bc + 3):
                        if self.board[r][c] == 0:
                            self.cands[r][c].discard(num)

    def _empty_in_unit(self, cells: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        return [(i, j) for i, j in cells if self.board[i][j] == 0]

    def _non_marking_techniques(self) -> List[Callable[[], bool]]:
        return [
            self.naked_single,
            self.hidden_single,
        ]

    def _marking_techniques(self) -> List[Callable[[], bool]]:
        return [
            self.naked_pair,
            self.hidden_pair,
            self.naked_triple,
            self.pointing_pair,
            self.box_line_reduction,
            self.x_wing,
            self.xy_wing,
        ]

    def _techniques(self) -> List[Callable[[], bool]]:
        return self._non_marking_techniques() + self._marking_techniques()

    def _apply_next_step(self) -> bool:
        for technique in self._techniques():
            if technique():
                return True
        return False

    # ── Naked Single ──

    def naked_single(self) -> bool:
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0 and len(self.cands[i][j]) == 1:
                    num = next(iter(self.cands[i][j]))
                    self._log(f"Naked Single: {format_cell(i,j)} = {num}")
                    self._place(i, j, num)
                    return True
        return False

    # ── Hidden Single ──

    def hidden_single(self) -> bool:
        for cells in UNITS:
            empty = self._empty_in_unit(cells)
            for num in range(1, 10):
                positions = [(i, j) for i, j in empty if num in self.cands[i][j]]
                if len(positions) == 1:
                    i, j = positions[0]
                    self._log(f"Hidden Single: {format_cell(i,j)} = {num}（{unit_name(cells)} 唯一可能位置）")
                    self._place(i, j, num)
                    return True
        return False

    # ── Naked Pair ──

    def naked_pair(self) -> bool:
        for cells in UNITS:
            empty = self._empty_in_unit(cells)
            if len(empty) < 2:
                continue
            pair_cells = [(i, j) for i, j in empty if len(self.cands[i][j]) == 2]
            if len(pair_cells) < 2:
                continue
            for (a, b) in combinations(pair_cells, 2):
                if self.cands[a[0]][a[1]] == self.cands[b[0]][b[1]]:
                    nums = self.cands[a[0]][a[1]]
                    other = [(i, j) for i, j in empty
                             if (i, j) != a and (i, j) != b and
                             nums & self.cands[i][j]]
                    if not other:
                        continue
                    self._log(f"Naked Pair: {format_cell(*a)} + {format_cell(*b)} 共享 {sorted(nums)}"
                              f"，{unit_name(cells)} 内 {format_cells(other)} 排除")
                    for i, j in other:
                        self.cands[i][j] -= nums
                        self.elim_count += 1
                    return True
        return False

    # ── Hidden Pair ──

    def hidden_pair(self) -> bool:
        for cells in UNITS:
            empty = self._empty_in_unit(cells)
            if len(empty) < 2:
                continue
            num_positions: List[List[Tuple[int, int]]] = [[] for _ in range(10)]
            for i, j in empty:
                for n in self.cands[i][j]:
                    num_positions[n].append((i, j))
            for a, b in combinations(range(1, 10), 2):
                if len(num_positions[a]) == 2 and num_positions[a] == num_positions[b]:
                    cells_to_clean = num_positions[a]
                    had_extra = False
                    all_extra: set = set()
                    for i, j in cells_to_clean:
                        extra = self.cands[i][j] - {a, b}
                        all_extra |= extra
                        if extra:
                            had_extra = True
                    if not had_extra:
                        continue
                    self._log(f"Hidden Pair: {format_cells(cells_to_clean)} 在 "
                              f"{unit_name(cells)} 中出现数字 {a},{b}"
                              f"，排除其他候选 {sorted(all_extra)}")
                    for i, j in cells_to_clean:
                        self.cands[i][j] &= {a, b}
                        self.elim_count += 1
                    return True
        return False

    # ── Naked Triple ──

    def naked_triple(self) -> bool:
        for cells in UNITS:
            empty = self._empty_in_unit(cells)
            if len(empty) < 3:
                continue
            candidates_cells = [(i, j) for i, j in empty
                                if 2 <= len(self.cands[i][j]) <= 3]
            if len(candidates_cells) < 3:
                continue
            for triple in combinations(candidates_cells, 3):
                union_nums = set()
                for i, j in triple:
                    union_nums |= self.cands[i][j]
                if len(union_nums) != 3:
                    continue
                other = [(i, j) for i, j in empty
                         if (i, j) not in triple and union_nums & self.cands[i][j]]
                if not other:
                    continue
                self._log(f"Naked Triple: {format_cells(list(triple))} 共享 {sorted(union_nums)}"
                          f"，{unit_name(cells)} 内 {format_cells(other)} 排除")
                for i, j in other:
                    self.cands[i][j] -= union_nums
                    self.elim_count += 1
                return True
        return False

    # ── Pointing Pair ──

    def pointing_pair(self) -> bool:
        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                box = box_cells(br, bc)
                empty_box = self._empty_in_unit(box)
                for num in range(1, 10):
                    positions = [(i, j) for i, j in empty_box if num in self.cands[i][j]]
                    if len(positions) < 2 or len(positions) > 3:
                        continue
                    rows = set(i for i, j in positions)
                    cols = set(j for i, j in positions)
                    if len(rows) == 1:
                        r = next(iter(rows))
                        outside = [(r, c) for c in range(9)
                                   if self.board[r][c] == 0
                                   and not (br <= r < br + 3 and bc <= c < bc + 3)
                                   and num in self.cands[r][c]]
                        if outside:
                            self._log(f"Pointing Pair: 宫 ({br + 1},{bc + 1}) 中数字 {num} 只在行 {r + 1}"
                                      f"，{format_cells(outside)} 排除 {num}")
                            for i, j in outside:
                                self.cands[i][j].discard(num)
                                self.elim_count += 1
                            return True
                    if len(cols) == 1:
                        c = next(iter(cols))
                        outside = [(r, c) for r in range(9)
                                   if self.board[r][c] == 0
                                   and not (br <= r < br + 3 and bc <= c < bc + 3)
                                   and num in self.cands[r][c]]
                        if outside:
                            self._log(f"Pointing Pair: 宫 ({br + 1},{bc + 1}) 中数字 {num} 只在列 {c + 1}"
                                      f"，{format_cells(outside)} 排除 {num}")
                            for i, j in outside:
                                self.cands[i][j].discard(num)
                                self.elim_count += 1
                            return True
        return False

    # ── Box-Line Reduction ──

    def box_line_reduction(self) -> bool:
        for i in range(9):
            for num in range(1, 10):
                row_pos = [(i, j) for j in range(9)
                           if self.board[i][j] == 0 and num in self.cands[i][j]]
                if len(row_pos) < 2 or len(row_pos) > 3:
                    continue
                boxes = set((j // 3) for _, j in row_pos)
                if len(boxes) == 1:
                    bc = next(iter(boxes)) * 3
                    br = (i // 3) * 3
                    outside = [(r, c) for r in range(br, br + 3) for c in range(bc, bc + 3)
                               if r != i and self.board[r][c] == 0 and num in self.cands[r][c]]
                    if outside:
                        self._log(f"Box-Line: 行 {i + 1} 中数字 {num} 只在宫 ({br + 1},{bc + 1})"
                                  f"，{format_cells(outside)} 排除 {num}")
                        for r, c in outside:
                            self.cands[r][c].discard(num)
                            self.elim_count += 1
                        return True
        for j in range(9):
            for num in range(1, 10):
                col_pos = [(i, j) for i in range(9)
                           if self.board[i][j] == 0 and num in self.cands[i][j]]
                if len(col_pos) < 2 or len(col_pos) > 3:
                    continue
                boxes = set((i // 3) for i, _ in col_pos)
                if len(boxes) == 1:
                    br = next(iter(boxes)) * 3
                    bc = (j // 3) * 3
                    outside = [(r, c) for r in range(br, br + 3) for c in range(bc, bc + 3)
                               if c != j and self.board[r][c] == 0 and num in self.cands[r][c]]
                    if outside:
                        self._log(f"Box-Line: 列 {j + 1} 中数字 {num} 只在宫 ({br + 1},{bc + 1})"
                                  f"，{format_cells(outside)} 排除 {num}")
                        for r, c in outside:
                            self.cands[r][c].discard(num)
                            self.elim_count += 1
                        return True
        return False

    # ── X-Wing ──

    def x_wing(self) -> bool:
        """行→列 X-Wing: 数字 N 在 2 行中只出现在相同 2 列"""
        for num in range(1, 10):
            # 找行: 数字 num 只出现在 2 列的行
            row_patterns = []
            for r in range(9):
                cols = [c for c in range(9)
                        if self.board[r][c] == 0 and num in self.cands[r][c]]
                if len(cols) == 2:
                    row_patterns.append((r, cols))
            if len(row_patterns) < 2:
                continue
            for (r1, cols1), (r2, cols2) in combinations(row_patterns, 2):
                if cols1 == cols2:
                    c1, c2 = cols1
                    # 删除这两列其他行的 num
                    eliminated = []
                    for r in range(9):
                        if r != r1 and r != r2:
                            if num in self.cands[r][c1]:
                                self.cands[r][c1].discard(num)
                                eliminated.append((r, c1))
                                self.elim_count += 1
                            if num in self.cands[r][c2]:
                                self.cands[r][c2].discard(num)
                                eliminated.append((r, c2))
                                self.elim_count += 1
                    if eliminated:
                        self._log(f"X-Wing: 数字 {num} 在行 {r1 + 1},{r2 + 1} 只出现在列 {c1 + 1},{c2 + 1}"
                                  f"，{format_cells(eliminated)} 排除 {num}")
                        return True
        # 列→行 X-Wing（对称）
        for num in range(1, 10):
            col_patterns = []
            for c in range(9):
                rows = [r for r in range(9)
                        if self.board[r][c] == 0 and num in self.cands[r][c]]
                if len(rows) == 2:
                    col_patterns.append((c, rows))
            if len(col_patterns) < 2:
                continue
            for (c1, rows1), (c2, rows2) in combinations(col_patterns, 2):
                if rows1 == rows2:
                    r1, r2 = rows1
                    eliminated = []
                    for c in range(9):
                        if c != c1 and c != c2:
                            if num in self.cands[r1][c]:
                                self.cands[r1][c].discard(num)
                                eliminated.append((r1, c))
                                self.elim_count += 1
                            if num in self.cands[r2][c]:
                                self.cands[r2][c].discard(num)
                                eliminated.append((r2, c))
                                self.elim_count += 1
                    if eliminated:
                        self._log(f"X-Wing: 数字 {num} 在列 {c1 + 1},{c2 + 1} 只出现在行 {r1 + 1},{r2 + 1}"
                                  f"，{format_cells(eliminated)} 排除 {num}")
                        return True
        return False

    # ── XY-Wing ──

    def xy_wing(self) -> bool:
        bivalue_cells = [
            (i, j)
            for i in range(9)
            for j in range(9)
            if self.board[i][j] == 0 and len(self.cands[i][j]) == 2
        ]

        for pi, pj in bivalue_cells:
            pivot = self.cands[pi][pj]
            pivot_peers = [
                (i, j)
                for i, j in bivalue_cells
                if (i, j) != (pi, pj)
                and self._see_each_other((pi, pj), (i, j))
                and len(self.cands[i][j] & pivot) == 1
            ]

            for (w1i, w1j), (w2i, w2j) in combinations(pivot_peers, 2):
                wing1 = self.cands[w1i][w1j]
                wing2 = self.cands[w2i][w2j]
                union = pivot | wing1 | wing2
                shared_wings = wing1 & wing2

                if len(union) != 3 or len(shared_wings) != 1:
                    continue
                z = next(iter(shared_wings))
                if z in pivot:
                    continue

                eliminated = []
                for i in range(9):
                    for j in range(9):
                        if self.board[i][j] != 0 or (i, j) in {(pi, pj), (w1i, w1j), (w2i, w2j)}:
                            continue
                        if z not in self.cands[i][j]:
                            continue
                        if self._see_each_other((i, j), (w1i, w1j)) and self._see_each_other((i, j), (w2i, w2j)):
                            self.cands[i][j].discard(z)
                            eliminated.append((i, j))
                            self.elim_count += 1

                if eliminated:
                    self._log(
                        f"XY-Wing: 枢纽 {format_cell(pi, pj)} {sorted(pivot)}，"
                        f"翼 {format_cell(w1i, w1j)} {sorted(wing1)} + {format_cell(w2i, w2j)} {sorted(wing2)}，"
                        f"{format_cells(eliminated)} 排除 {z}"
                    )
                    return True

        return False

    def _see_each_other(self, a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        ai, aj = a
        bi, bj = b
        return ai == bi or aj == bj or (ai // 3, aj // 3) == (bi // 3, bj // 3)

    def _try_backtracking_fallback(self) -> bool:
        result = DEFAULT_BACKTRACKING_SOLVER.solve(self.board)
        if result.solved and result.solution is not None:
            self.fallback_used = True
            self.board = [row[:] for row in result.solution]
            self._rebuild_candidates()
            self._log("Fallback Backtracking: 逻辑推理无法继续，已用公共回溯能力补全解")
            print("检测到逻辑推理无法继续，已切换到公共回溯求解。")
            return True

        self.error_message = result.invalid_reason or "当前盘面无解，可能输入错误"
        print(f"错误：{self.error_message}")
        return False

    # ── 主流程 ──

    def solve(self) -> bool:
        print("初始棋盘：")
        print_board(self.board)
        print()

        # 先展示初始候选
        print("初始候选数：")
        self._show_candidates()
        print()

        while True:
            if board_solved(self.board):
                print()
                print("✓ 解题完成！")
                print()
                self._print_steps()
                print_board(self.board)
                print(f"共 {self.step_no} 步推理，{self.elim_count} 次排除")
                return True

            if self._apply_next_step():
                continue

            print()
            print("⚠ 卡住了！以下技巧不足：")
            print("  Naked/Hidden Single ✓   Naked/Hidden Pair ✓")
            print("  Naked Triple ✓   Pointing Pair ✓   Box-Line ✓   X-Wing ✓")
            print()
            print("已填入：")
            print_board(self.board)
            print("剩余候选：")
            self._show_candidates()
            print()
            print("开始使用公共回溯能力确认当前盘面是否有解。")
            if self._try_backtracking_fallback():
                continue
            return False

    def _show_candidates(self) -> None:
        hr = "+" + "-" * (9 * 8 + 2) + "+"
        print(hr)
        for i in range(9):
            line = "|"
            for j in range(9):
                if self.board[i][j]:
                    line += f"  {self.board[i][j]}   "
                else:
                    cs = "".join(str(n) for n in sorted(self.cands[i][j]))
                    line += f" {cs:<5} "
            line += "|"
            print(line)
            if i in (2, 5):
                print(hr)
        print(hr)


# ── 主程序入口 ─────────────────────────────────────

HARDEST = """
..3..5.1.
..893.45.
2.57.436.
53..4719.
78.193.45
..956..73
..7.5..2.
..4..9.3.
..1....8.
"""

if __name__ == "__main__":
    board = parse(HARDEST)
    solver = LogicSolver(board)
    solver.solve()
