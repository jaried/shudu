"""验证挑战完成后的棋盘保留与行列宫完成动画。
完成态停止游戏输入，但不再用遮罩替换棋盘。
行、列、宫从未完成变为正确完成时，由 View 播放只读青色扫光。
暂停态仍保留原遮罩行为。
"""

import os
import sys
import time
import tkinter as tk

import pytest

from sudoku_gui import SudokuWindow
from sudoku_theme import HEIGHT, WIDTH

pytestmark = pytest.mark.skipif(
    sys.platform.startswith("linux") and not os.environ.get("DISPLAY"),
    reason="GUI 测试需要显示环境或 xvfb-run",
)


def make_app():
    root = tk.Tk()
    app = SudokuWindow(root)
    root.geometry(f"{WIDTH}x{HEIGHT}+20+20")
    root.update()
    return app


def test_completed_game_keeps_full_board_visible():
    app = make_app()
    app.game.board = [list(row) for row in app.game.solution]
    app.game._check_finished()
    app.view.draw()
    app.root.update()
    assert app.game.status == "won"
    assert app.view.find_withtag("cell-0-0")
    assert app.view.find_withtag("cell-8-8")
    assert app.view.find_withtag("value-0-0")
    assert app.view.find_withtag("value-8-8")
    assert app.view.find_withtag("completion-status")
    assert app.view.itemcget("completion-status", "text") == "挑战完成"
    assert "overlay:restart" not in app.view.targets
    app.close()


def test_completed_game_controls_are_read_only():
    app = make_app()
    app.game.board = [list(row) for row in app.game.solution]
    app.game._check_finished()
    app.view.draw()
    assert not app.view.targets["erase"][1]
    assert not app.view.targets["undo"][1]
    assert not app.view.targets["notes"][1]
    assert not app.view.targets["auto-notes"][1]
    assert not app.view.targets["hint"][1]
    assert not app.view.targets["pause"][1]
    app.close()


def test_pause_still_hides_board_behind_overlay():
    app = make_app()
    app.game.toggle_pause()
    app.view.draw()
    assert app.game.status == "paused"
    assert not app.view.find_withtag("cell-0-0")
    assert app.view.targets["overlay:pause"][1]
    app.close()


def test_finishing_cell_reports_exact_row_col_and_box():
    app = make_app()
    game = app.game
    game.auto_techniques.clear()
    cell = next(
        cell
        for cell in ((row, col) for row in range(9) for col in range(9))
        if not game.given(cell)
    )
    game.board = [list(row) for row in game.solution]
    game.board[cell[0]][cell[1]] = 0
    before = set(game.completed_units())
    game.select(*cell)
    game.enter(game.solution[cell[0]][cell[1]])
    completed = tuple(unit for unit in game.completed_units() if unit not in before)
    assert len(completed) == 3
    assert sum(len({row for row, _ in unit}) == 1 for unit in completed) == 1
    assert sum(len({col for _, col in unit}) == 1 for unit in completed) == 1
    assert sum(
        len({row for row, _ in unit}) == 3
        and len({col for _, col in unit}) == 3
        for unit in completed
    ) == 1
    app.close()


def test_dispatch_plays_completion_wave_without_mutating_board():
    app = make_app()
    game = app.game
    game.auto_techniques.clear()
    cell = next(
        cell
        for cell in ((row, col) for row in range(9) for col in range(9))
        if not game.given(cell)
    )
    game.board = [list(row) for row in game.solution]
    game.board[cell[0]][cell[1]] = 0
    game.select(*cell)
    digit = game.solution[cell[0]][cell[1]]
    app.view.draw()
    app.dispatch(f"digit:{digit}")
    solved = [row[:] for row in game.board]
    time.sleep(0.09)
    app.root.update()
    assert app.view.find_withtag("completion-flash")
    assert game.board == solved
    app.close()
