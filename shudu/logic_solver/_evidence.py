"""单步结果的解释证据生产。"""

from shudu.sudoku_rules import CELLS, Cell, box_cells, col_cells, related, row_cells


def hidden_single_evidence(board, candidates, target: Cell, digit: int, fallback_unit):
    """按宫、行、列选择单位，并基于执行前 board 计算一次来源。"""
    row, col = target
    preferred = (box_cells(row, col), row_cells(row), col_cells(col))
    unit = next(
        (
            candidate_unit
            for candidate_unit in preferred
            if sum(
                digit in candidates[item_row][item_col]
                for item_row, item_col in candidate_unit
            )
            == 1
        ),
        fallback_unit,
    )
    empty_others = tuple(
        cell for cell in unit if cell != target and not board[cell[0]][cell[1]]
    )
    sources = tuple(
        cell
        for cell in CELLS
        if board[cell[0]][cell[1]] == digit
        and any(related(cell, other) for other in empty_others)
    )
    return sources, (unit,)
