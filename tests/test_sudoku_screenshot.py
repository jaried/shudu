"""验证截图输入只通过公开导入接口恢复游戏状态。
合成截图同时包含正式大数字和 3×3 候选小数字。
测试锁定二者不会互相误判，并覆盖中文路径读取。
不依赖 Tk 窗口或外部 OCR 服务。
"""

from pathlib import Path

import cv2
import numpy as np

from sudoku_gui import game_from_screenshot
from sudoku_screenshot import load_screenshot_game


def _synthetic_screenshot(path: Path) -> None:
    image = np.full((1_000, 1_000, 3), 248, dtype=np.uint8)
    left = 50
    top = 50
    side = 900
    cell = 100
    for index in range(10):
        width = 5 if index % 3 == 0 else 2
        x = left + index * cell
        y = top + index * cell
        cv2.line(image, (x, top), (x, top + side), (70, 70, 70), width)
        cv2.line(image, (left, y), (left + side, y), (70, 70, 70), width)
    _large_digit(image, left, top, 0, 0, 8)
    _large_digit(image, left, top, 4, 4, 3)
    _large_digit(image, left, top, 8, 8, 5)
    _note_digit(image, left, top, 0, 1, 2)
    _note_digit(image, left, top, 0, 1, 6)
    _note_digit(image, left, top, 6, 6, 6)
    _note_digit(image, left, top, 6, 6, 8)
    encoded = cv2.imencode(".png", image)[1]
    encoded.tofile(path)


def _large_digit(image, left, top, row, col, digit) -> None:
    cell_left = left + col * 100
    cell_top = top + row * 100
    text = str(digit)
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 2.2
    thickness = 4
    size, baseline = cv2.getTextSize(text, font, scale, thickness)
    x = cell_left + (100 - size[0]) // 2
    y = cell_top + (100 + size[1]) // 2 - baseline // 2
    cv2.putText(image, text, (x, y), font, scale, (80, 80, 80), thickness, cv2.LINE_AA)


def _note_digit(image, left, top, row, col, digit) -> None:
    cell_left = left + col * 100
    cell_top = top + row * 100
    slot_row, slot_col = divmod(digit - 1, 3)
    center_x = cell_left + round((slot_col + 0.5) * 100 / 3)
    center_y = cell_top + round((slot_row + 0.5) * 100 / 3)
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.55
    thickness = 1
    size, baseline = cv2.getTextSize(str(digit), font, scale, thickness)
    x = center_x - size[0] // 2
    y = center_y + size[1] // 2 - baseline // 2
    cv2.putText(image, str(digit), (x, y), font, scale, (90, 90, 90), thickness, cv2.LINE_AA)


def test_screenshot_import_distinguishes_formal_digits_and_notes(tmp_path):
    path = tmp_path / "数独截图.png"
    _synthetic_screenshot(path)
    imported = load_screenshot_game(path)
    grid = imported.puzzle.grid()
    notes = imported.note_map()
    assert grid[0][0] == 8
    assert grid[4][4] == 3
    assert grid[8][8] == 5
    assert grid[0][1] == 0
    assert notes[(0, 1)] == {2, 6}
    assert notes[(6, 6)] == {6, 8}
    assert (0, 0) not in notes


def test_gui_startup_game_preserves_screenshot_notes(tmp_path):
    path = tmp_path / "input.png"
    _synthetic_screenshot(path)
    game = game_from_screenshot(path)
    assert game.given((0, 0))
    assert game.value((0, 0)) == 8
    assert game.notes[(0, 1)] == {2, 6}
    assert game.notes[(6, 6)] == {6, 8}
    assert game.notes_mode
    assert game.auto_simple


def test_missing_screenshot_has_clear_error(tmp_path):
    path = tmp_path / "missing.png"
    try:
        load_screenshot_game(path)
    except ValueError as error:
        assert "不存在" in str(error)
    else:
        raise AssertionError("缺失截图必须明确失败")
