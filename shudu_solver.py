"""提供 shudu 使用的逻辑求解器入口。
在既有 LogicSolver 上只定义项目需要的技巧优先级。
算法候选来自求解器自己的 cands，不读取 GUI 用户笔记。
保留旧求解器实现，避免复制高级技巧和制造第二套规则。
"""

from __future__ import annotations

from logical_solver import LogicSolver, parse, print_board


class ShuduSolver(LogicSolver):
    """项目级逻辑求解器：行/列/宫唯一落点优先。"""

    def _non_marking_techniques(self):
        result = [self.hidden_single, self.naked_single]
        return result

    def algorithm_candidates(self):
        """返回算法内部候选快照；调用方修改快照不会影响求解器。"""
        result = [[set(values) for values in row] for row in self.cands]
        return result


DEFAULT_BOARD = """
....9.6.7
.......1.
9.7.2.53.
4...5....
.....8...
13..4.79.
6.89.....
.1.5....2
.......5.
"""


def main(board_text: str = DEFAULT_BOARD) -> None:
    board = parse(board_text)
    solver = ShuduSolver(board)
    solved = solver.solve()
    if solved:
        print_board(solver.board)


if __name__ == "__main__":
    # 直接修改这里即可像 GUI 一样自定义题面；0 或 . 表示空格。
    CUSTOM_BOARD = DEFAULT_BOARD
    main(CUSTOM_BOARD)
