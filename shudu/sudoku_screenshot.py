"""从数独游戏截图恢复可直接启动的游戏输入。
本模块把棋盘定位、正式大数字识别和候选小数字解析隐藏在一个接口后。
正式数字使用字形模板识别，小数字按候选九宫位置解析，二者不会混为一谈。
本模块不依赖 GUI、Game 或求解器，调用方只接收 Puzzle 与候选笔记。
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from shudu.sudoku_puzzles import Puzzle
from shudu.sudoku_rules import Cell

BOARD_PIXELS = 900
CELL_PIXELS = BOARD_PIXELS // 9
NORMALIZED_DIGIT = 64
MIN_BOARD_RATIO = 0.08
LARGE_HEIGHT_RATIO = 0.32
LARGE_AREA_RATIO = 0.012
NOTE_MIN_HEIGHT_RATIO = 0.07
NOTE_MAX_HEIGHT_RATIO = 0.30
NOTE_MIN_AREA_RATIO = 0.0008
OCR_MIN_SCORE = 0.50


@dataclass(frozen=True)
class ScreenshotGameInput:
    """截图导入结果；正式数字进入题面，小数字保留为候选笔记。"""

    puzzle: Puzzle
    notes: tuple[tuple[Cell, frozenset[int]], ...]

    def note_map(self) -> dict[Cell, set[int]]:
        result = {cell: set(values) for cell, values in self.notes}
        return result


def load_screenshot_game(path: str | Path) -> ScreenshotGameInput:
    """读取指定截图并恢复题面和候选笔记。"""
    source = Path(path)
    image = _read_image(source)
    board = _extract_board(image)
    rows, notes = _read_cells(board)
    if not any(char != "." for row in rows for char in row):
        raise ValueError("截图中没有识别到正式大数字")
    puzzle = Puzzle(source.stem or "截图导入", "截图导入", rows)
    puzzle.grid()
    result = ScreenshotGameInput(puzzle, tuple(sorted(notes.items())))
    return result


def _read_image(path: Path) -> np.ndarray:
    if not path.is_file():
        raise ValueError(f"截图文件不存在：{path}")
    data = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"无法读取截图文件：{path}")
    return image


def _extract_board(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        9,
    )
    height, width = gray.shape
    horizontal = _long_lines(binary, max(25, width // 12), horizontal=True)
    vertical = _long_lines(binary, max(25, height // 12), horizontal=False)
    grid = cv2.bitwise_or(horizontal, vertical)
    bounds = _largest_square_bounds(grid)
    if bounds is None:
        raise ValueError("没有找到清晰的 9×9 数独棋盘")
    x, y, side = bounds
    crop = image[y : y + side, x : x + side]
    result = cv2.resize(crop, (BOARD_PIXELS, BOARD_PIXELS), interpolation=cv2.INTER_AREA)
    return result


def _long_lines(binary: np.ndarray, length: int, horizontal: bool) -> np.ndarray:
    shape = (length, 1) if horizontal else (1, length)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, shape)
    result = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    return result


def _largest_square_bounds(grid: np.ndarray) -> tuple[int, int, int] | None:
    contours, _ = cv2.findContours(grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    image_area = grid.shape[0] * grid.shape[1]
    candidates: list[tuple[int, int, int, int]] = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        area = width * height
        ratio = width / height if height else 0
        if area >= image_area * MIN_BOARD_RATIO and 0.82 <= ratio <= 1.18:
            candidates.append((area, x, y, min(width, height)))
    if not candidates:
        return None
    _, x, y, side = max(candidates)
    result = (x, y, side)
    return result


def _read_cells(board: np.ndarray) -> tuple[tuple[str, ...], dict[Cell, frozenset[int]]]:
    rows: list[str] = []
    notes: dict[Cell, frozenset[int]] = {}
    for row in range(9):
        chars: list[str] = []
        for col in range(9):
            cell = _cell_image(board, row, col)
            digit, cell_notes = _read_cell(cell)
            chars.append(str(digit) if digit else ".")
            if digit == 0 and cell_notes:
                notes[(row, col)] = frozenset(cell_notes)
        rows.append("".join(chars))
    result = (tuple(rows), notes)
    return result


def _cell_image(board: np.ndarray, row: int, col: int) -> np.ndarray:
    top = row * CELL_PIXELS
    left = col * CELL_PIXELS
    result = board[top : top + CELL_PIXELS, left : left + CELL_PIXELS]
    return result


def _read_cell(cell: np.ndarray) -> tuple[int, set[int]]:
    binary = _cell_binary(cell)
    labels, stats, centroids = _components(binary)
    large_label = _large_component(stats, centroids)
    if large_label is not None:
        glyph = _component_mask(labels, large_label, stats[large_label])
        digit = _recognize_digit(glyph)
        return digit, set()
    notes = _note_digits(stats, centroids)
    return 0, notes


def _cell_binary(cell: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    margin = max(6, CELL_PIXELS // 14)
    inner = gray[margin:-margin, margin:-margin]
    _, dark_foreground = cv2.threshold(inner, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    _, light_foreground = cv2.threshold(inner, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    inner_binary = _sparser_foreground(dark_foreground, light_foreground)
    result = np.zeros_like(gray)
    result[margin:-margin, margin:-margin] = inner_binary
    return result


def _sparser_foreground(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    first_count = cv2.countNonZero(first)
    second_count = cv2.countNonZero(second)
    result = first if first_count <= second_count else second
    return result


def _components(binary: np.ndarray):
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if count <= 1:
        empty_stats = np.zeros((1, 5), dtype=np.int32)
        empty_centroids = np.zeros((1, 2), dtype=np.float64)
        return labels, empty_stats, empty_centroids
    return labels, stats, centroids


def _large_component(stats: np.ndarray, centroids: np.ndarray) -> int | None:
    cell_area = CELL_PIXELS * CELL_PIXELS
    best = None
    best_area = 0
    for label in range(1, len(stats)):
        _, _, _, height, area = stats[label]
        center_x, center_y = centroids[label]
        centered = 0.20 * CELL_PIXELS <= center_x <= 0.80 * CELL_PIXELS and 0.18 * CELL_PIXELS <= center_y <= 0.82 * CELL_PIXELS
        large = height >= CELL_PIXELS * LARGE_HEIGHT_RATIO and area >= cell_area * LARGE_AREA_RATIO
        if centered and large and area > best_area:
            best = label
            best_area = area
    return best


def _note_digits(stats: np.ndarray, centroids: np.ndarray) -> set[int]:
    result: set[int] = set()
    cell_area = CELL_PIXELS * CELL_PIXELS
    for label in range(1, len(stats)):
        _, _, width, height, area = stats[label]
        if width < 2 or not CELL_PIXELS * NOTE_MIN_HEIGHT_RATIO <= height <= CELL_PIXELS * NOTE_MAX_HEIGHT_RATIO:
            continue
        if area < cell_area * NOTE_MIN_AREA_RATIO:
            continue
        center_x, center_y = centroids[label]
        note_row = min(2, max(0, int(center_y * 3 / CELL_PIXELS)))
        note_col = min(2, max(0, int(center_x * 3 / CELL_PIXELS)))
        result.add(note_row * 3 + note_col + 1)
    return result


def _component_mask(labels: np.ndarray, label: int, stat: np.ndarray) -> np.ndarray:
    x, y, width, height, _ = stat
    mask = np.zeros((height, width), dtype=np.uint8)
    region = labels[y : y + height, x : x + width]
    mask[region == label] = 255
    return mask


def _recognize_digit(glyph: np.ndarray) -> int:
    normalized = _normalize_glyph(glyph)
    best_digit = 0
    best_score = -1.0
    for digit, template in _digit_templates():
        score = _dice_score(normalized, template)
        if score > best_score:
            best_digit = digit
            best_score = score
    if best_score < OCR_MIN_SCORE:
        raise ValueError(f"正式大数字识别置信度不足：{best_score:.2f}")
    return best_digit


def _normalize_glyph(glyph: np.ndarray) -> np.ndarray:
    points = cv2.findNonZero(glyph)
    if points is None:
        return np.zeros((NORMALIZED_DIGIT, NORMALIZED_DIGIT), dtype=np.uint8)
    x, y, width, height = cv2.boundingRect(points)
    crop = glyph[y : y + height, x : x + width]
    scale = min(44 / max(width, 1), 54 / max(height, 1))
    new_width = max(1, round(width * scale))
    new_height = max(1, round(height * scale))
    resized = cv2.resize(crop, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
    canvas = np.zeros((NORMALIZED_DIGIT, NORMALIZED_DIGIT), dtype=np.uint8)
    left = (NORMALIZED_DIGIT - new_width) // 2
    top = (NORMALIZED_DIGIT - new_height) // 2
    canvas[top : top + new_height, left : left + new_width] = resized
    return canvas


@lru_cache(maxsize=1)
def _digit_templates() -> tuple[tuple[int, np.ndarray], ...]:
    templates: list[tuple[int, np.ndarray]] = []
    fonts = (
        cv2.FONT_HERSHEY_SIMPLEX,
        cv2.FONT_HERSHEY_DUPLEX,
        cv2.FONT_HERSHEY_COMPLEX,
        cv2.FONT_HERSHEY_TRIPLEX,
    )
    for digit in range(1, 10):
        for font in fonts:
            for thickness in (2, 3, 4):
                templates.append((digit, _render_template(digit, font, thickness)))
    return tuple(templates)


def _render_template(digit: int, font: int, thickness: int) -> np.ndarray:
    canvas = np.zeros((96, 96), dtype=np.uint8)
    text = str(digit)
    size, baseline = cv2.getTextSize(text, font, 2.4, thickness)
    x = (96 - size[0]) // 2
    y = (96 + size[1]) // 2 - baseline // 2
    cv2.putText(canvas, text, (x, y), font, 2.4, 255, thickness, cv2.LINE_AA)
    _, binary = cv2.threshold(canvas, 32, 255, cv2.THRESH_BINARY)
    result = _normalize_glyph(binary)
    return result


def _dice_score(first: np.ndarray, second: np.ndarray) -> float:
    a = first > 0
    b = second > 0
    denominator = int(a.sum() + b.sum())
    if denominator == 0:
        return 0.0
    intersection = int(np.logical_and(a, b).sum())
    result = 2.0 * intersection / denominator
    return result
