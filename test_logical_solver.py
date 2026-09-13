from logical_solver import LogicSolver, parse
from logical_solver import HARDEST
from solver import parse as parse_backtracking_board
from solver import solve as solve_with_shared_backtracking


FIRST_PUZZLE = """
6...89..4
.........
23...5..9
..34..5..
.....1.4.
4.8.53.27
.5.72....
3..51.472
7.2...6..
"""

FIRST_SOLUTION = [
    [6, 7, 5, 2, 8, 9, 1, 3, 4],
    [8, 9, 1, 3, 4, 7, 2, 6, 5],
    [2, 3, 4, 1, 6, 5, 7, 8, 9],
    [9, 6, 3, 4, 7, 2, 5, 1, 8],
    [5, 2, 7, 8, 9, 1, 3, 4, 6],
    [4, 1, 8, 6, 5, 3, 9, 2, 7],
    [1, 5, 6, 7, 2, 4, 8, 9, 3],
    [3, 8, 9, 5, 1, 6, 4, 7, 2],
    [7, 4, 2, 9, 3, 8, 6, 5, 1],
]

SECOND_PUZZLE = """
....3..2.
....5.47.
49.....6.
..42.35..
........8
..8..9...
8...1..56
1.7.....3
5....6...
"""

SECOND_SOLUTION = [
    [7, 5, 6, 9, 3, 4, 8, 2, 1],
    [2, 8, 3, 6, 5, 1, 4, 7, 9],
    [4, 9, 1, 7, 2, 8, 3, 6, 5],
    [6, 1, 4, 2, 8, 3, 5, 9, 7],
    [9, 2, 5, 1, 4, 7, 6, 3, 8],
    [3, 7, 8, 5, 6, 9, 1, 4, 2],
    [8, 4, 9, 3, 1, 2, 7, 5, 6],
    [1, 6, 7, 4, 9, 5, 2, 8, 3],
    [5, 3, 2, 8, 7, 6, 9, 1, 4],
]

INVALID_PUZZLE = """
11.......
.........
.........
.........
.........
.........
.........
.........
.........
"""


def test_hardest_puzzle_solves_to_expected_solution():
    solver = LogicSolver(parse(FIRST_PUZZLE))

    solved = solver.solve()

    assert solved is True
    assert solver.board == FIRST_SOLUTION
    assert solver.steps
    assert solver.steps[0].startswith("  [  1] ")
    assert "行 1" in "".join(solver.steps) or "列 1" in "".join(solver.steps) or "(1,1)" in "".join(solver.steps)


def test_apply_next_step_restarts_from_simplest_rule_each_time():
    board = [[0] * 9 for _ in range(9)]
    solver = LogicSolver(board)
    calls = []

    def make_rule(name: str, result: bool):
        def rule() -> bool:
            calls.append(name)
            return result
        return rule

    solver._techniques = lambda: [
        make_rule("naked_single", False),
        make_rule("hidden_single", True),
        make_rule("naked_pair", True),
    ]

    assert solver._apply_next_step() is True
    assert calls == ["naked_single", "hidden_single"]

    calls.clear()
    assert solver._apply_next_step() is True
    assert calls == ["naked_single", "hidden_single"]


def test_technique_order_uses_non_marking_before_marking():
    solver = LogicSolver([[0] * 9 for _ in range(9)])

    non_marking = [tech.__name__ for tech in solver._non_marking_techniques()]
    marking = [tech.__name__ for tech in solver._marking_techniques()]
    all_techniques = [tech.__name__ for tech in solver._techniques()]

    assert non_marking == ["naked_single", "hidden_single"]
    assert all_techniques == non_marking + marking
    assert "naked_pair" in marking
    assert "xy_wing" in marking


def test_second_puzzle_solves_logically_without_backtracking():
    solver = LogicSolver(parse(SECOND_PUZZLE))

    solved = solver.solve()

    assert solved is True
    assert solver.board == SECOND_SOLUTION
    assert solver.fallback_used is False
    assert any("XY-Wing:" in step for step in solver.steps)


def test_hardest_puzzle_does_not_repeat_identical_elimination_logs():
    solver = LogicSolver(parse(HARDEST))

    solved = solver.solve()

    assert solved is True
    messages = [step.split("] ", 1)[1] for step in solver.steps]
    assert len(messages) == len(set(messages))


def test_logic_solver_falls_back_to_shared_backtracking(capsys):
    solver = LogicSolver(parse(FIRST_PUZZLE))
    solver._apply_next_step = lambda: False

    solved = solver.solve()

    captured = capsys.readouterr()
    assert solved is True
    assert solver.fallback_used is True
    assert solver.board == FIRST_SOLUTION
    assert "切换到公共回溯求解" in captured.out
    assert any("Fallback Backtracking:" in step for step in solver.steps)


def test_logic_solver_reports_invalid_input_when_board_has_no_solution(capsys):
    solver = LogicSolver(parse(INVALID_PUZZLE))

    solved = solver.solve()

    captured = capsys.readouterr()
    assert solved is False
    assert solver.error_message is not None
    assert "重复" in solver.error_message
    assert "错误：" in captured.out


def test_solver_module_uses_shared_backtracking_solver():
    board = parse_backtracking_board(FIRST_PUZZLE)

    solved = solve_with_shared_backtracking(board)

    assert solved is True
    assert board == FIRST_SOLUTION
