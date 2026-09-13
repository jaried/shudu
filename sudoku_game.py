"""实现与图形界面解耦的数独游戏状态。
原题答案统一通过仓库的公共回溯求解器获得。
候选笔记、撤销、错误累计和计时均在本模块管理。
基础规则复用 sudoku_rules，不把手工笔记当作求解约束。
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from time import monotonic
from typing import Callable

from shudu_solver import ShuduSolver
from sudoku_backtracking import DEFAULT_BACKTRACKING_SOLVER
from sudoku_hints import Hint, make_hint
from sudoku_puzzles import Puzzle, SCREENSHOT_PUZZLE
from sudoku_rules import CELLS, PEERS, Cell, candidate_grid, related

Grid = tuple[tuple[int, ...], ...]


@lru_cache(maxsize=16)
def solve_puzzle(puzzle: Puzzle) -> Grid:
    """仅在载入题目时求解，落子和重绘不运行搜索。"""
    result = DEFAULT_BACKTRACKING_SOLVER.solve(puzzle.grid())
    if not result.solved or result.solution is None:
        raise ValueError(result.invalid_reason or "题面无解")
    solution = tuple(tuple(row) for row in result.solution)
    return solution


@dataclass(frozen=True)
class Snapshot:
    board: Grid
    notes: tuple[tuple[Cell, frozenset[int]], ...]
    selected: Cell


class Game:
    def __init__(
        self,
        puzzle: Puzzle = SCREENSHOT_PUZZLE,
        clock: Callable[[], float] = monotonic,
        auto_simple: bool = True,
    ):
        self.puzzle = puzzle
        self.solution = solve_puzzle(puzzle)
        self.givens = tuple(tuple(row) for row in puzzle.grid())
        self.board = [list(row) for row in self.givens]
        self._clock = clock
        self._elapsed = 0.0
        self._started = clock()
        self._init_play_state(auto_simple)
        self.hint_preview: Hint | None = None
        self._auto_solve_simple(remember=False)
        return

    def _init_play_state(self, auto_simple: bool) -> None:
        self.notes: dict[Cell, set[int]] = {}
        self.history: list[Snapshot] = []
        self.selected: Cell = (1, 3)
        self.active_digit = 0
        self.notes_mode = False
        self.auto_clean = True
        self.auto_simple = auto_simple
        self.mistakes = 0
        self.hints_used = 0
        self.status = "playing"
        self.message = "先选择一个格子，再输入数字。"

    def value(self, cell: Cell) -> int:
        result = self.board[cell[0]][cell[1]]
        return result

    def given(self, cell: Cell) -> bool:
        result = bool(self.givens[cell[0]][cell[1]])
        return result

    @property
    def editable(self) -> bool:
        result = self.status == "playing" and not self.given(self.selected)
        return result

    @property
    def elapsed(self) -> int:
        extra = self._clock() - self._started if self.status == "playing" else 0
        result = int(self._elapsed + extra)
        return result

    @property
    def time_text(self) -> str:
        minutes, seconds = divmod(self.elapsed, 60)
        result = f"{minutes:02d}:{seconds:02d}"
        return result

    def select(self, row: int, col: int) -> None:
        if self.status != "playing" or not (0 <= row < 9 and 0 <= col < 9):
            return
        self.selected = (row, col)
        self.active_digit = self.value(self.selected)
        self.message = f"第 {row + 1} 行，第 {col + 1} 列" + (" · 题目已知数" if self.given(self.selected) else "")

    def highlighted_cells(self) -> set[Cell]:
        """合并全部同值大数字的行列宫；空格和笔记只使用当前格。"""
        digit = self.value(self.selected)
        anchors = {self.selected}
        if digit:
            anchors = {cell for cell in CELLS if self.value(cell) == digit}
        result = set(anchors)
        for cell in anchors:
            result.update(PEERS[cell])
        return result

    def move(self, row_delta: int, col_delta: int) -> None:
        row, col = self.selected
        self.select((row + row_delta) % 9, (col + col_delta) % 9)

    def toggle_notes(self) -> None:
        if self.status != "playing":
            return
        self.notes_mode = not self.notes_mode
        self.message = "笔记已开启：数字只作标记，再点一次取消。" if self.notes_mode else "笔记已关闭：数字将正式填入。"

    def _remember(self) -> None:
        board = tuple(tuple(row) for row in self.board)
        notes = tuple((cell, frozenset(values)) for cell, values in self.notes.items())
        self.history.append(Snapshot(board, notes, self.selected))

    def enter(self, digit: int) -> None:
        if not isinstance(digit, int) or isinstance(digit, bool) or not 1 <= digit <= 9:
            raise ValueError("只能输入 1–9")
        if not self.editable:
            return
        self.active_digit = digit
        if self.notes_mode:
            self._toggle_note(digit)
        elif self.value(self.selected) != digit and not self.completed_digit(digit):
            self._place(digit)

    def _toggle_note(self, digit: int) -> None:
        if self.value(self.selected):
            self.message = "已有正式数字，请先擦除，再添加笔记。"
            return
        self._remember()
        values = self.notes.setdefault(self.selected, set())
        values.symmetric_difference_update({digit})
        if not values:
            self.notes.pop(self.selected)
        self.message = f"笔记 {digit} 已切换；笔记不会增加错误次数。"

    def _place(self, digit: int) -> None:
        self._remember()
        row, col = self.selected
        self.board[row][col] = digit
        self.notes.pop(self.selected, None)
        if digit == self.solution[row][col]:
            self._correct_entry(digit)
        else:
            self.mistakes += 1
            self.message = "填入有误：红底标记错误格，橙红数字提示关联冲突。"
        self._check_finished()

    def _correct_entry(self, digit: int) -> None:
        if self.auto_clean:
            self._clean_notes_for(self.selected, digit)
        self.message = f"已填入 {digit}。"
        self._auto_solve_simple(remember=False)

    def _clean_notes_for(self, source: Cell, digit: int) -> None:
        for cell in PEERS[source]:
            if cell in self.notes:
                self.notes[cell].discard(digit)
                if not self.notes[cell]:
                    self.notes.pop(cell)

    def set_auto_simple(self, enabled: bool) -> None:
        """切换简单算法自动求解；从关闭切到开启时立即推进当前盘面。"""
        enabled = bool(enabled)
        changed = enabled != self.auto_simple
        self.auto_simple = enabled
        if changed and enabled:
            self._auto_solve_simple(remember=True)
        elif changed:
            self.message = "已关闭简单算法自动求解。"

    def _auto_solve_simple(self, remember: bool) -> int:
        if not self.auto_simple or self.status != "playing" or self.wrong_cells():
            return 0
        solver = ShuduSolver(self.board)
        count = solver.solve_simple()
        if count == 0:
            return 0
        if remember:
            self._remember()
        previous = [row[:] for row in self.board]
        self.board = [row[:] for row in solver.board]
        self._clean_auto_notes(previous)
        self.active_digit = self.value(self.selected)
        self.message = f"简单算法自动填入 {count} 格；X-Wing 及以上算法未自动执行。"
        self._check_finished()
        return count

    def _clean_auto_notes(self, previous) -> None:
        for cell in CELLS:
            row, col = cell
            digit = self.board[row][col]
            if not previous[row][col] and digit:
                self.notes.pop(cell, None)
                if self.auto_clean:
                    self._clean_notes_for(cell, digit)

    def erase(self) -> None:
        if not self.editable or (not self.value(self.selected) and self.selected not in self.notes):
            return
        self._remember()
        row, col = self.selected
        self.board[row][col] = 0
        self.notes.pop(self.selected, None)
        self.active_digit = 0
        self.message = "已擦除；累计错误次数保持不变。"

    def undo(self) -> None:
        if self.status != "playing" or not self.history:
            return
        snapshot = self.history.pop()
        self.board = [list(row) for row in snapshot.board]
        self.notes = {cell: set(values) for cell, values in snapshot.notes}
        self.selected = snapshot.selected
        self.active_digit = self.value(self.selected)
        self.message = "已撤销，并恢复该操作之前的笔记；错误次数不退回。"

    def wrong_cells(self) -> set[Cell]:
        result = {cell for cell in CELLS if self.value(cell) and self.value(cell) != self.solution[cell[0]][cell[1]]}
        return result

    def conflict_cells(self) -> set[Cell]:
        result = {cell for cell in CELLS if self.value(cell) and any(self.value(other) == self.value(cell) for other in PEERS[cell])}
        return result

    def completed_digit(self, digit: int) -> bool:
        result = sum(self.value(cell) == digit == self.solution[cell[0]][cell[1]] for cell in CELLS) == 9
        return result

    def hint(self) -> None:
        if self.status != "playing":
            return
        self.hint_preview = make_hint(self.board, self.notes, self.wrong_cells())
        self.hints_used += int(self.hint_preview.step is not None)
        self._stop("hint")

    def close_hint(self) -> None:
        if self.status != "hint":
            return
        self.hint_preview = None
        self.status = "playing"
        self._started = self._clock()
        self.message = "提示已关闭；请自行填数或修改笔记。"

    def auto_notes(self) -> None:
        if self.status != "playing":
            return
        if self.wrong_cells():
            self.message = "请先修正红色错误格，再生成合法候选数。"
            return
        candidates = candidate_grid(self.board)
        notes = {cell: set(candidates[cell[0]][cell[1]]) for cell in CELLS if not self.value(cell)}
        self._replace_notes(notes)
        self.notes_mode = True
        self.message = "已重算所有空格的候选笔记；未填写大数字，可一次撤回。"

    def _replace_notes(self, notes: dict[Cell, set[int]]) -> None:
        if notes != self.notes:
            self._remember()
            self.notes = notes

    def toggle_pause(self) -> None:
        if self.status == "playing":
            self._stop("paused")
        elif self.status == "paused":
            self.status = "playing"
            self._started = self._clock()

    def _stop(self, status: str) -> None:
        self._elapsed += self._clock() - self._started
        self.status = status

    def _check_finished(self) -> None:
        if all(self.value(cell) == self.solution[cell[0]][cell[1]] for cell in CELLS):
            self._stop("won")
