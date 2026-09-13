# ADR-003 Numba 位掩码逻辑核心

## 状态

已接受 — 2026-09-13

## 背景

此前回溯搜索已经由 `numba.njit` 加速，但人类逻辑技巧仍以 Python `set`、列表推导和 `combinations` 在解释器中执行。随着 GUI 提示、`shudu_solver.py` 和命令行逻辑求解器共用这些技巧，继续保留两套候选表示会产生性能和规则漂移风险。

核心逻辑技巧包括：

- Hidden Single
- Naked Single
- Naked Pair
- Hidden Pair
- Naked Triple
- Pointing Pair
- Box-Line Reduction
- X-Wing
- XY-Wing

## 决策

新增 `sudoku_njit_core.py`，将正式大数字推导出的候选统一编码为 1–9 的整数位掩码，并用 `@numba.njit(cache=True)` 实现基础候选计算、落子传播以及上述九种模式搜索。

新增 `sudoku_logic.py` 作为共享 Python orchestration 层：

- `_masks: np.ndarray[int64]` 是算法候选的唯一热路径状态；
- Python `set` 候选只在兼容接口、日志和 GUI 提示边界临时生成；
- `LogicSolver` 与 `ShuduSolver` 都复用同一 Numba 核心；
- `LogicSolver` 保留旧的 Naked Single → Hidden Single 优先级；
- `ShuduSolver` 保留项目要求的 Hidden Single → Naked Single 优先级；
- 回溯 fallback 继续复用已存在的 njit 回溯实现。

`sudoku_rules.candidate_grid()` 也改为复用同一候选位掩码内核，因此 GUI 的自动笔记与逻辑求解器不会维护两套基础候选算法。

## 影响

### 正面

- 所有产品核心逻辑模式搜索进入 Numba nopython 路径；
- 81 格候选状态由 Python set 网格收敛为紧凑整数矩阵；
- GUI、提示、`logical_solver.py`、`shudu_solver.py` 共用同一基础候选定义；
- 旧公开接口仍可读取 `cands`，避免已有测试和调用方一次性迁移；
- `cache=True` 允许后续进程复用已编译内核。

### 代价

- 首次运行仍有 Numba JIT 编译成本；
- 日志字符串和 GUI 结构化结果保留在 Python 层，因为这些并非计算热点，也不适合放入 nopython 内核；
- `cands` 属性现在返回快照，调用方不应通过修改该快照来改变 solver 内部状态。

## 验证

`tests/test_njit_core.py` 会主动调用全部九种核心 finder，并断言每个 dispatcher 都产生 `nopython_signatures`。完整 GitHub Actions 回归继续在 Python 3.12 + Xvfb 下运行。
