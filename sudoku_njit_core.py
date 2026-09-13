"""Numba 加速的数独逻辑核心。
所有模式搜索只处理整数棋盘和候选位掩码，避免 Python set 热路径。
Python 层负责日志、UI 结构化结果和兼容旧接口。
本模块不读取用户笔记，也不执行回溯。
"""

from __future__ import annotations

import numpy as np
from numba import njit

ALL_DIGITS_MASK = 0x3FE
UNIT_COUNT = 27
CELL_COUNT = 81


@njit(cache=True)
def count_bits(mask: int) -> int:
    count = 0
    while mask:
        mask &= mask - 1
        count += 1
    return count


@njit(cache=True)
def mask_digit(mask: int) -> int:
    for digit in range(1, 10):
        if mask == 1 << digit:
            return digit
    return 0


@njit(cache=True)
def unit_cell(unit_index: int, offset: int) -> tuple[int, int]:
    if unit_index < 18:
        index = unit_index // 2
        if unit_index % 2 == 0:
            return index, offset
        return offset, index
    box = unit_index - 18
    base_row = (box // 3) * 3
    base_col = (box % 3) * 3
    return base_row + offset // 3, base_col + offset % 3


@njit(cache=True)
def candidate_masks(board: np.ndarray) -> np.ndarray:
    masks = np.zeros((9, 9), dtype=np.int64)
    for row in range(9):
        for col in range(9):
            if board[row, col] != 0:
                continue
            mask = ALL_DIGITS_MASK
            for index in range(9):
                row_value = board[row, index]
                col_value = board[index, col]
                if row_value:
                    mask &= ~(1 << row_value)
                if col_value:
                    mask &= ~(1 << col_value)
            base_row = (row // 3) * 3
            base_col = (col // 3) * 3
            for other_row in range(base_row, base_row + 3):
                for other_col in range(base_col, base_col + 3):
                    value = board[other_row, other_col]
                    if value:
                        mask &= ~(1 << value)
            masks[row, col] = mask
    return masks


@njit(cache=True)
def apply_placement(masks: np.ndarray, row: int, col: int, digit: int) -> None:
    bit = 1 << digit
    masks[row, col] = 0
    for index in range(9):
        masks[row, index] &= ~bit
        masks[index, col] &= ~bit
    base_row = (row // 3) * 3
    base_col = (col // 3) * 3
    for other_row in range(base_row, base_row + 3):
        for other_col in range(base_col, base_col + 3):
            masks[other_row, other_col] &= ~bit


@njit(cache=True)
def find_naked_single(board: np.ndarray, masks: np.ndarray) -> tuple[int, int, int]:
    for row in range(9):
        for col in range(9):
            if board[row, col] == 0 and count_bits(masks[row, col]) == 1:
                return row, col, mask_digit(masks[row, col])
    return -1, -1, 0


@njit(cache=True)
def _hidden_single_in_unit(board: np.ndarray, masks: np.ndarray, unit_index: int, digit: int) -> tuple[int, int, int]:
    bit = 1 << digit
    count = 0
    found_row = -1
    found_col = -1
    for offset in range(9):
        row, col = unit_cell(unit_index, offset)
        if board[row, col] == 0 and masks[row, col] & bit:
            count += 1
            found_row = row
            found_col = col
    return count, found_row, found_col


@njit(cache=True)
def find_hidden_single(board: np.ndarray, masks: np.ndarray) -> tuple[int, int, int, int]:
    for unit_index in range(UNIT_COUNT):
        for digit in range(1, 10):
            count, row, col = _hidden_single_in_unit(board, masks, unit_index, digit)
            if count == 1:
                return unit_index, row, col, digit
    return -1, -1, -1, 0


@njit(cache=True)
def _unit_has_intersection(board: np.ndarray, masks: np.ndarray, unit_index: int, skip_a: int, skip_b: int, mask: int) -> bool:
    for offset in range(9):
        if offset == skip_a or offset == skip_b:
            continue
        row, col = unit_cell(unit_index, offset)
        if board[row, col] == 0 and masks[row, col] & mask:
            return True
    return False


@njit(cache=True)
def find_naked_pair(board: np.ndarray, masks: np.ndarray) -> tuple[int, int, int, int, int, int]:
    for unit_index in range(UNIT_COUNT):
        for first in range(8):
            row_a, col_a = unit_cell(unit_index, first)
            mask = masks[row_a, col_a]
            if board[row_a, col_a] != 0 or count_bits(mask) != 2:
                continue
            for second in range(first + 1, 9):
                row_b, col_b = unit_cell(unit_index, second)
                if board[row_b, col_b] != 0 or masks[row_b, col_b] != mask:
                    continue
                if _unit_has_intersection(board, masks, unit_index, first, second, mask):
                    return unit_index, row_a, col_a, row_b, col_b, mask
    return -1, -1, -1, -1, -1, 0


@njit(cache=True)
def _digit_offsets(board: np.ndarray, masks: np.ndarray, unit_index: int, digit: int) -> tuple[int, int, int]:
    bit = 1 << digit
    count = 0
    first = -1
    second = -1
    for offset in range(9):
        row, col = unit_cell(unit_index, offset)
        if board[row, col] == 0 and masks[row, col] & bit:
            if count == 0:
                first = offset
            elif count == 1:
                second = offset
            count += 1
    return count, first, second


@njit(cache=True)
def find_hidden_pair(board: np.ndarray, masks: np.ndarray) -> tuple[int, int, int, int, int, int, int]:
    for unit_index in range(UNIT_COUNT):
        for digit_a in range(1, 9):
            count_a, first_a, second_a = _digit_offsets(board, masks, unit_index, digit_a)
            if count_a != 2:
                continue
            for digit_b in range(digit_a + 1, 10):
                count_b, first_b, second_b = _digit_offsets(board, masks, unit_index, digit_b)
                if count_b != 2 or first_a != first_b or second_a != second_b:
                    continue
                row_a, col_a = unit_cell(unit_index, first_a)
                row_b, col_b = unit_cell(unit_index, second_a)
                pair_mask = (1 << digit_a) | (1 << digit_b)
                if masks[row_a, col_a] & ~pair_mask or masks[row_b, col_b] & ~pair_mask:
                    return unit_index, row_a, col_a, row_b, col_b, digit_a, digit_b
    return -1, -1, -1, -1, -1, 0, 0


@njit(cache=True)
def _triple_has_target(board: np.ndarray, masks: np.ndarray, unit_index: int, first: int, second: int, third: int, union_mask: int) -> bool:
    for offset in range(9):
        if offset == first or offset == second or offset == third:
            continue
        row, col = unit_cell(unit_index, offset)
        if board[row, col] == 0 and masks[row, col] & union_mask:
            return True
    return False


@njit(cache=True)
def find_naked_triple(board: np.ndarray, masks: np.ndarray) -> tuple[int, int, int, int, int, int, int, int]:
    for unit_index in range(UNIT_COUNT):
        for first in range(7):
            row_a, col_a = unit_cell(unit_index, first)
            count_a = count_bits(masks[row_a, col_a])
            if board[row_a, col_a] != 0 or count_a < 2 or count_a > 3:
                continue
            for second in range(first + 1, 8):
                row_b, col_b = unit_cell(unit_index, second)
                count_b = count_bits(masks[row_b, col_b])
                if board[row_b, col_b] != 0 or count_b < 2 or count_b > 3:
                    continue
                for third in range(second + 1, 9):
                    row_c, col_c = unit_cell(unit_index, third)
                    count_c = count_bits(masks[row_c, col_c])
                    if board[row_c, col_c] != 0 or count_c < 2 or count_c > 3:
                        continue
                    union_mask = masks[row_a, col_a] | masks[row_b, col_b] | masks[row_c, col_c]
                    if count_bits(union_mask) != 3:
                        continue
                    if _triple_has_target(board, masks, unit_index, first, second, third, union_mask):
                        return unit_index, row_a, col_a, row_b, col_b, row_c, col_c, union_mask
    return -1, -1, -1, -1, -1, -1, -1, 0


@njit(cache=True)
def _box_digit_positions(board: np.ndarray, masks: np.ndarray, base_row: int, base_col: int, digit: int) -> tuple[int, int, int, int, int]:
    bit = 1 << digit
    count = 0
    first_row = -1
    first_col = -1
    same_row = 1
    same_col = 1
    for row in range(base_row, base_row + 3):
        for col in range(base_col, base_col + 3):
            if board[row, col] != 0 or not masks[row, col] & bit:
                continue
            if count == 0:
                first_row = row
                first_col = col
            else:
                if row != first_row:
                    same_row = 0
                if col != first_col:
                    same_col = 0
            count += 1
    return count, first_row, first_col, same_row, same_col


@njit(cache=True)
def find_pointing_pair(board: np.ndarray, masks: np.ndarray) -> tuple[int, int, int, int, int]:
    for base_row in range(0, 9, 3):
        for base_col in range(0, 9, 3):
            for digit in range(1, 10):
                count, row, col, same_row, same_col = _box_digit_positions(board, masks, base_row, base_col, digit)
                if count < 2 or count > 3:
                    continue
                bit = 1 << digit
                if same_row:
                    for other_col in range(9):
                        if base_col <= other_col < base_col + 3:
                            continue
                        if board[row, other_col] == 0 and masks[row, other_col] & bit:
                            return base_row, base_col, digit, 0, row
                if same_col:
                    for other_row in range(9):
                        if base_row <= other_row < base_row + 3:
                            continue
                        if board[other_row, col] == 0 and masks[other_row, col] & bit:
                            return base_row, base_col, digit, 1, col
    return -1, -1, 0, -1, -1


@njit(cache=True)
def _row_candidate_columns(board: np.ndarray, masks: np.ndarray, row: int, digit: int) -> tuple[int, int, int, int]:
    bit = 1 << digit
    count = 0
    first = -1
    second = -1
    third = -1
    for col in range(9):
        if board[row, col] == 0 and masks[row, col] & bit:
            if count == 0:
                first = col
            elif count == 1:
                second = col
            elif count == 2:
                third = col
            count += 1
    return count, first, second, third


@njit(cache=True)
def _col_candidate_rows(board: np.ndarray, masks: np.ndarray, col: int, digit: int) -> tuple[int, int, int, int]:
    bit = 1 << digit
    count = 0
    first = -1
    second = -1
    third = -1
    for row in range(9):
        if board[row, col] == 0 and masks[row, col] & bit:
            if count == 0:
                first = row
            elif count == 1:
                second = row
            elif count == 2:
                third = row
            count += 1
    return count, first, second, third


@njit(cache=True)
def find_box_line(board: np.ndarray, masks: np.ndarray) -> tuple[int, int, int, int, int]:
    for row in range(9):
        for digit in range(1, 10):
            count, first, second, third = _row_candidate_columns(board, masks, row, digit)
            if count < 2 or count > 3:
                continue
            box_col = first // 3
            if second // 3 != box_col or count == 3 and third // 3 != box_col:
                continue
            base_row = (row // 3) * 3
            base_col = box_col * 3
            bit = 1 << digit
            for other_row in range(base_row, base_row + 3):
                if other_row == row:
                    continue
                for col in range(base_col, base_col + 3):
                    if board[other_row, col] == 0 and masks[other_row, col] & bit:
                        return 0, row, digit, base_row, base_col
    for col in range(9):
        for digit in range(1, 10):
            count, first, second, third = _col_candidate_rows(board, masks, col, digit)
            if count < 2 or count > 3:
                continue
            box_row = first // 3
            if second // 3 != box_row or count == 3 and third // 3 != box_row:
                continue
            base_row = box_row * 3
            base_col = (col // 3) * 3
            bit = 1 << digit
            for row in range(base_row, base_row + 3):
                for other_col in range(base_col, base_col + 3):
                    if other_col == col:
                        continue
                    if board[row, other_col] == 0 and masks[row, other_col] & bit:
                        return 1, col, digit, base_row, base_col
    return -1, -1, 0, -1, -1


@njit(cache=True)
def find_x_wing(board: np.ndarray, masks: np.ndarray) -> tuple[int, int, int, int, int, int]:
    for digit in range(1, 10):
        bit = 1 << digit
        for row_a in range(8):
            count_a, col_a, col_b, _ = _row_candidate_columns(board, masks, row_a, digit)
            if count_a != 2:
                continue
            for row_b in range(row_a + 1, 9):
                count_b, other_a, other_b, _ = _row_candidate_columns(board, masks, row_b, digit)
                if count_b != 2 or col_a != other_a or col_b != other_b:
                    continue
                for row in range(9):
                    if row == row_a or row == row_b:
                        continue
                    if masks[row, col_a] & bit or masks[row, col_b] & bit:
                        return 0, digit, row_a, row_b, col_a, col_b
    for digit in range(1, 10):
        bit = 1 << digit
        for col_a in range(8):
            count_a, row_a, row_b, _ = _col_candidate_rows(board, masks, col_a, digit)
            if count_a != 2:
                continue
            for col_b in range(col_a + 1, 9):
                count_b, other_a, other_b, _ = _col_candidate_rows(board, masks, col_b, digit)
                if count_b != 2 or row_a != other_a or row_b != other_b:
                    continue
                for col in range(9):
                    if col == col_a or col == col_b:
                        continue
                    if masks[row_a, col] & bit or masks[row_b, col] & bit:
                        return 1, digit, row_a, row_b, col_a, col_b
    return -1, 0, -1, -1, -1, -1


@njit(cache=True)
def see_each_other(row_a: int, col_a: int, row_b: int, col_b: int) -> bool:
    return row_a == row_b or col_a == col_b or (row_a // 3 == row_b // 3 and col_a // 3 == col_b // 3)


@njit(cache=True)
def find_xy_wing(board: np.ndarray, masks: np.ndarray) -> tuple[int, int, int, int, int, int, int]:
    for pivot_index in range(CELL_COUNT):
        pivot_row = pivot_index // 9
        pivot_col = pivot_index % 9
        pivot = masks[pivot_row, pivot_col]
        if board[pivot_row, pivot_col] != 0 or count_bits(pivot) != 2:
            continue
        for first_index in range(CELL_COUNT):
            first_row = first_index // 9
            first_col = first_index % 9
            first = masks[first_row, first_col]
            if first_index == pivot_index or board[first_row, first_col] != 0 or count_bits(first) != 2:
                continue
            if not see_each_other(pivot_row, pivot_col, first_row, first_col) or count_bits(first & pivot) != 1:
                continue
            for second_index in range(first_index + 1, CELL_COUNT):
                second_row = second_index // 9
                second_col = second_index % 9
                second = masks[second_row, second_col]
                if second_index == pivot_index or board[second_row, second_col] != 0 or count_bits(second) != 2:
                    continue
                if not see_each_other(pivot_row, pivot_col, second_row, second_col) or count_bits(second & pivot) != 1:
                    continue
                union = pivot | first | second
                shared = first & second
                if count_bits(union) != 3 or count_bits(shared) != 1 or shared & pivot:
                    continue
                digit = mask_digit(shared)
                bit = 1 << digit
                for target_index in range(CELL_COUNT):
                    target_row = target_index // 9
                    target_col = target_index % 9
                    if target_index == pivot_index or target_index == first_index or target_index == second_index:
                        continue
                    if board[target_row, target_col] != 0 or not masks[target_row, target_col] & bit:
                        continue
                    if see_each_other(target_row, target_col, first_row, first_col) and see_each_other(target_row, target_col, second_row, second_col):
                        return pivot_row, pivot_col, first_row, first_col, second_row, second_col, digit
    return -1, -1, -1, -1, -1, -1, 0


def masks_from_board(board) -> np.ndarray:
    array = np.asarray(board, dtype=np.int64)
    result = candidate_masks(array)
    return result


def candidate_sets(masks: np.ndarray) -> list[list[set[int]]]:
    result = [[set() for _ in range(9)] for _ in range(9)]
    for row in range(9):
        for col in range(9):
            mask = int(masks[row, col])
            result[row][col] = {digit for digit in range(1, 10) if mask & (1 << digit)}
    return result


def mask_digits(mask: int) -> set[int]:
    result = {digit for digit in range(1, 10) if mask & (1 << digit)}
    return result
