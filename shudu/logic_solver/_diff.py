"""整数候选 mask 的数值差分。"""

import numpy as np
from numba import njit

from ._results import Change


@njit(cache=True)
def mask_diff(before: np.ndarray, after: np.ndarray) -> tuple[np.ndarray, int]:
    """返回固定容量的 row/col/digit 删除数组及有效行数。"""
    changes = np.zeros((81, 3), dtype=np.int64)
    count = 0
    for row in range(9):
        for col in range(9):
            removed = int(before[row, col]) & ~int(after[row, col])
            for digit in range(1, 10):
                if removed & (1 << digit):
                    changes[count, 0] = row
                    changes[count, 1] = col
                    changes[count, 2] = digit
                    count += 1
    return changes, count


def diff_changes(before: np.ndarray, after: np.ndarray) -> tuple[Change, ...]:
    """把固定容量 nopython 结果转换为公开删除 tuple。"""
    raw, count = mask_diff(before, after)
    result = tuple(tuple(int(value) for value in row) for row in raw[:count])
    return result
