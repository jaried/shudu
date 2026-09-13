"""实现与图形界面解耦的数独游戏状态。
原题答案统一通过仓库的公共回溯求解器获得。
候选笔记、撤销、错误累计和计时均在本模块管理。
自动算法按独立开关组合执行，不把手工笔记当作求解约束。
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from time import monotonic
from typing import Callable

from shudu_solver import (
    AUTO_TECHNIQUE_NAMES,
    AUTO_TECHNIQUE_SPECS,
    DEFAULT_AUTO_TECHNIQUES,
    ShuduSolver,
)
from shudu.sudoku_backtracking import DEFAULT_BACKTRACKING_SOLVER
from shudu.sudoku_hints import Hint, make_hint
from shudu.sudoku_puzzles import Puzzle, SCREENSHOT_PUZZLE
from shudu.sudoku_rules import CELLS, PEERS, Cell, candidate_grid
from shudu.sudoku_step import Change

Grid = tuple[tuple[int, ...], ...]


@lru_cache(maxsize=16)
def solve_puzzle(puzzle: Puzzle) -> Grid:
    """仅在载入题目时求解，落子和重绘不运行搜索。"""
    result = DEFAULT_BACKTRACKING_SOLVER.solve(puzzle.grid())
    if not result.solved or result.solution is None:
        raise ValueError(result.invalid_reason or "题面无解")
    solution = tuple(tuple(row) for row in result.solution)
    return solution


def _validated_auto_techniques(names: Iterable[str]) -> set[str]:
    result = set(names)
    unknown = result.difference(AUTO_TECHNIQUE_NAMES)
    if unknown:
        raise ValueError(f"未知自动算法：{', '.join(sorted(unknown))}")
    return result


@dataclass(frozen=True)
class Snapshot:
    board: Grid
    notes: tuple[tuple[Cell, frozenset[int]], ...]
    selected: Cell
    simple_eliminations: tuple[Change, ...]


class Game:
    def __init__(
        self,
        puzzle: Puzzle = SCREENSHOT_PUZZLE,
        clock: Callable[[], float] = monotonic,
        auto_simple: bool = False,
        auto_techniques: Iterable[str] | None = None,
    ):
        self.puzzle = puzzle
        self.solution = solve_puzzle(puzzle)
        self.givens = tuple(tuple(row) for row in puzzle.grid())
        self.board = [list(row) for row in self.givens]
        self._clock = clock
        self._elapsed = 0.0
        self._started = clock()
        self._init_play_state(auto_simple, auto_techniques)
        self.hint_preview: Hint | None = None
        return

    def _init_play_state(self, auto_simple: bool, auto_techniques: Iterable[str] | None) -> None:
        self.notes: dict[Cell, set[int]] = {}
        self.history: list[Snapshot] = []
        self.simple_eliminations: set[Change] = set()
        self.auto_techniques = self._initial_auto_techniques(auto_simple, auto_techniques)
        self.selected: Cell = (1, 3)
        self.active_digit = 0
        self.notes_mode = False
        self.auto_clean = True
        self.mistakes = 0
        self.hints_used = 0
        self.status = "playing"
        self.message = "先选择一个格子，再输入数字。"

    def _initial_auto_techniques(self, auto_simple: bool, names: Iterable[str] | None) -> set[str]:
        if names is not None:
            return _validated_auto_techniques(names)
        result = set(DEFAULT_AUTO_TECHNIQUES) if auto_simple else set()
        return result

    @property
    def auto_simple(self) -> bool:
        """兼容旧开关：有任一自动算法启用时视为开启。"""
        result = bool(self.auto_techniques)
        return result

    @auto_simple.setter
    def auto_simple(self, enabled: bool) -> None:
        """兼容旧赋值：True 恢复默认简单算法，False 关闭全部自动算法。"""
        self.auto_techniques = set(DEFAULT_AUTO_TECHNIQUES) if enabled else set()

    def auto_technique_settings(self) -> tuple[tuple[str, str, bool], ...]:
        """返回 GUI 可直接渲染的算法名称、标签与勾选状态。"""
        result = tuple(
            (name, label, name in self.auto_techniques)
            for name, label, _ in AUTO_TECHNIQUE_SPECS
        )
        return result

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
        eliminations = tuple(sorted(self.simple_eliminations))
        self.history.append(Snapshot(board, notes, self.selected, eliminations))

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
        self.auto_solve_enabled(remember=False)

    def _clean_notes_for(self, source: Cell, digit: int) -> None:
        for cell in PEERS[source]:
            if cell in self.notes:
                self.notes[cell].discard(digit)
                if not self.notes[cell]:
                    self.notes.pop(cell)

    def set_auto_technique(self, name: str, enabled: bool) -> None:
        """独立切换一个自动算法；开启时立即推进全部已启用算法到固定点。"""
        if name not in AUTO_TECHNIQUE_NAMES:
            raise ValueError(f"未知自动算法：{name}")
        enabled = bool(enabled)
        changed = (name in self.auto_techniques) != enabled
        if not changed:
            return
        if enabled:
            self.auto_techniques.add(name)
            self.auto_solve_enabled(remember=True)
        else:
            self.auto_techniques.remove(name)
            self.message = f"已关闭 {self._technique_label(name)} 自动求解。"

    def _technique_label(self, name: str) -> str:
        result = next(label for key, label, _ in AUTO_TECHNIQUE_SPECS if key == name)
        return result

    def set_auto_simple(self, enabled: bool) -> None:
        """兼容旧总开关；True 启用默认集合，False 关闭全部自动算法。"""
        target = set(DEFAULT_AUTO_TECHNIQUES) if enabled else set()
        changed = target != self.auto_techniques
        self.auto_techniques = target
        if changed and enabled:
            self.auto_solve_enabled(remember=True)
        elif changed:
            self.message = "已关闭全部自动算法。"

    def auto_solve_enabled(self, remember: bool = False) -> int:
        """执行全部已启用算法到固定点，并同步最终算法候选小数字。"""
        if not self.auto_techniques or self.status != "playing" or self.wrong_cells():
            return 0
        solver = ShuduSolver(self.board)
        solver.apply_candidate_eliminations(self.simple_eliminations)
        result = solver.solve_techniques_result(self.auto_techniques)
        changed = self._apply_auto_result(solver, result, remember)
        return result.placements if changed else 0

    def auto_solve_simple(self, remember: bool = False) -> int:
        """兼容既有调用；实际执行当前勾选的全部自动算法。"""
        result = self.auto_solve_enabled(remember)
        return result

    def _apply_auto_result(self, solver: ShuduSolver, result, remember: bool) -> bool:
        next_board = [row[:] for row in solver.board]
        next_notes = self._solver_notes(solver)
        next_eliminations = self.simple_eliminations | set(result.eliminations)
        changed = self._auto_result_changed(next_board, next_notes, next_eliminations)
        if not changed:
            return False
        if remember:
            self._remember()
        self.board = next_board
        self.notes = next_notes
        self.simple_eliminations = next_eliminations
        self.notes_mode = True
        self.active_digit = self.value(self.selected)
        self._set_auto_message(result.placements)
        self._check_finished()
        return True

    def _auto_result_changed(self, board, notes, eliminations) -> bool:
        result = board != self.board or notes != self.notes or eliminations != self.simple_eliminations
        return result

    def _solver_notes(self, solver: ShuduSolver) -> dict[Cell, set[int]]:
        candidates = solver.algorithm_candidates()
        result = {
            cell: set(candidates[cell[0]][cell[1]])
            for cell in CELLS
            if not solver.board[cell[0]][cell[1]] and candidates[cell[0]][cell[1]]
        }
        return result

    def _set_auto_message(self, placements: int) -> None:
        count = len(self.auto_techniques)
        if placements:
            self.message = f"{count} 个自动算法填入 {placements} 格，并已同步全部候选小数字。"
        else:
            self.message = f"{count} 个自动算法已推进到固定点，并已同步全部候选小数字。"

    def erase(self) -> None:
        if not self.editable or (not self.value(self.selected) and self.selected not in self.notes):
            return
        self._remember()
        row, col = self.selected
        self.board[row][col] = 0
        self.notes.pop(self.selected, None)
        self.simple_eliminations.clear()
        self.active_digit = 0
        self.message = "已擦除；算法候选将从当前盘面重新推导，累计错误次数保持不变。"

    def undo(self) -> None:
        if self.status != "playing" or not self.history:
            return
        snapshot = self.history.pop()
        self.board = [list(row) for row in snapshot.board]
        self.notes = {cell: set(values) for cell, values in snapshot.notes}
        self.simple_eliminations = set(snapshot.simple_eliminations)
        self.selected = snapshot.selected
        self.active_digit = self.value(self.selected)
        self.message = "已撤销，并恢复该操作之前的笔记和算法候选状态；错误次数不退回。"

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
        if self.auto_techniques:
            self.auto_solve_enabled(remember=True)
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
