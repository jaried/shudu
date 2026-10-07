"""从公开截图入口验证背景、有效字形和真实原图。"""

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
import pytest
from test_sudoku_screenshot import _large_digit

from shudu.sudoku_screenshot import load_screenshot_game
from sudoku_gui import game_from_screenshot

FIXTURES = Path(__file__).parent / "fixtures" / "screenshots"


def expected_image():
    return json.loads((FIXTURES / "level120-expected.json").read_text(encoding="utf-8"))


def board_image(background=248):
    image = np.full((1000, 1000, 3), background, dtype=np.uint8)
    grid_color = (min(70, background // 2),) * 3
    for index in range(10):
        offset = 50 + index * 100
        width = 5 if index % 3 == 0 else 2
        cv2.line(image, (offset, 50), (offset, 950), grid_color, width)
        cv2.line(image, (50, offset), (950, offset), grid_color, width)
    return image


def write_image(path, image):
    cv2.imencode(".png", image)[1].tofile(path)
    return path


def unreadable_image(path):
    image = board_image()
    for row, col in ((2, 4), (6, 1)):
        x, y = 50 + col * 100, 50 + row * 100
        cv2.line(image, (x + 25, y + 22), (x + 75, y + 78), (70, 70, 70), 4)
        cv2.line(image, (x + 75, y + 22), (x + 25, y + 78), (70, 70, 70), 4)
    return write_image(path, image)


def test_original_wechat_image_restores_every_cell_and_game():
    path = FIXTURES / "level120-wechat.jpg"
    expected = expected_image()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected["sha256"]
    imported = load_screenshot_game(path)
    assert imported.puzzle.rows == tuple(expected["rows"])
    assert imported.note_map() == expected["notes"] == {}
    game = game_from_screenshot(path, auto_techniques={"hidden_triple"}, auto_solve=False)
    assert game.board == imported.puzzle.grid()
    assert sum(game.given((r, c)) for r in range(9) for c in range(9)) == 24
    assert sum(value == 0 for row in game.board for value in row) == 57
    assert game.notes == {} and not game.notes_mode
    assert not game.auto_solve and game.auto_techniques == {"hidden_triple"}


@pytest.mark.parametrize("background,polarity", ((248, -1), (80, 1)))
@pytest.mark.parametrize("contrast", (4, 6, 8, 12, 20, 160))
def test_valid_low_contrast_digits_survive_flat_background(tmp_path, background, polarity, contrast):
    image = board_image(background)
    color = (background + polarity * contrast,) * 3
    for digit in range(1, 10):
        _large_digit(image, 50, 50, 0, digit - 1, digit, color=color)
    imported = load_screenshot_game(write_image(tmp_path / "低对比.png", image))
    assert imported.puzzle.rows == ("123456789",) + (".........",) * 8
    assert imported.note_map() == {}


def test_blank_cells_with_edge_noise_do_not_create_digits_or_notes(tmp_path):
    image = board_image()
    ramp = np.linspace(242, 248, 89, dtype=np.uint8)
    for row in range(9):
        for col in range(9):
            left, top = 56 + col * 100, 56 + row * 100
            image[top : top + 89, left : left + 89] = ramp[None, :, None]
    _large_digit(image, 50, 50, 4, 4, 8)
    imported = load_screenshot_game(write_image(tmp_path / "背景渐变.png", image))
    assert imported.puzzle.rows == (".........",) * 4 + ("....8....",) + (".........",) * 4
    assert imported.note_map() == {}


def test_public_import_stays_within_read_and_compute_budget(monkeypatch):
    import shudu.sudoku_screenshot as screenshot

    counters = {"read": 0, "decode": 0, "cell": 0, "otsu": 0, "threshold": 0}
    fromfile, decode, cell, threshold = np.fromfile, cv2.imdecode, screenshot._read_cell, cv2.threshold

    def read(*args, **kwargs):
        counters["read"] += 1
        return fromfile(*args, **kwargs)

    def read_decode(*args, **kwargs):
        counters["decode"] += 1
        return decode(*args, **kwargs)

    def read_cell(*args, **kwargs):
        counters["cell"] += 1
        return cell(*args, **kwargs)

    def read_threshold(image, value, maximum, mode):
        if image.shape == (86, 86):
            counters["threshold"] += 1
            counters["otsu"] += bool(mode & cv2.THRESH_OTSU)
        return threshold(image, value, maximum, mode)

    monkeypatch.setattr(np, "fromfile", read)
    monkeypatch.setattr(cv2, "imdecode", read_decode)
    monkeypatch.setattr(screenshot, "_read_cell", read_cell)
    monkeypatch.setattr(cv2, "threshold", read_threshold)
    imported = load_screenshot_game(FIXTURES / "level120-wechat.jpg")
    assert imported.puzzle.rows == tuple(expected_image()["rows"])
    assert counters["read"] == counters["decode"] == 1
    assert counters["cell"] == counters["otsu"] == 81
    assert 81 <= counters["threshold"] <= 162
