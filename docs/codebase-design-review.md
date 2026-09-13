# Codebase Design Review

## Status

COMPLETE — 2026-09-13

本轮按 `improve-codebase-design` 继续审查整个仓库，并在前一轮职责拆分基础上完成逻辑核心的 Numba 收敛。目标仍然是：单一真源、稳定 API、低耦合、低重复、可验证，而不是为了“优化”机械拆文件。

## 当前结论

此前最大的剩余技术债是：回溯已经 `njit`，但人类逻辑技巧仍运行在 Python `set` / 列表组合热路径中，而且 `logical_solver.py` 与项目级 `ShuduSolver` 仍存在两套执行层。现在已经收敛为：

```text
sudoku_njit_core.py    纯计算热路径：位掩码 + njit
        ↑
sudoku_logic.py        共享 orchestration / 日志 / fallback
        ↑
logical_solver.py      兼容旧 API 与旧优先级
shudu_solver.py        项目优先级 + next_step()
        ↑
sudoku_hints.py        只读提示
        ↑
sudoku_game.py         游戏状态
        ↑
sudoku_view.py / sudoku_gui.py
```

`sudoku_rules.py` 继续提供拓扑真源，但基础候选计算也已经复用 `sudoku_njit_core`，从而避免自动笔记和 solver 各自维护候选算法。

## 已完成的结构优化

### 1. `sudoku_rules.py` 保持纯领域边界

统一定义：

- `Cell`、`CELLS`；
- 行、列、宫及 `UNITS`；
- `PEERS` / `related()`；
- `unit_name()`。

它不依赖 GUI、Game、Hint 或 solver orchestration。基础 `candidate_grid()` 只负责把 Numba 位掩码结果转换为兼容的候选集合。

### 2. 新增 `sudoku_njit_core.py` 作为唯一计算热路径

候选数统一使用 1–9 的整数位掩码，核心函数全部使用 `@numba.njit(cache=True)`：

- 基础候选计算；
- 落子后的候选传播；
- Hidden Single；
- Naked Single；
- Naked Pair；
- Hidden Pair；
- Naked Triple；
- Pointing Pair；
- Box-Line Reduction；
- X-Wing；
- XY-Wing。

该模块不生成中文日志、不读取用户笔记、不依赖 GUI，也不执行回溯。

### 3. 新增 `sudoku_logic.py` 收敛共享 solver 状态

`NumbaLogicSolver` 以 `_masks: numpy.ndarray[int64]` 作为算法候选唯一内部状态。Python `set` 网格只在兼容接口、测试和 GUI 提示边界临时生成，不再作为核心模式搜索的数据结构。

这一层负责：

- 技巧编排；
- 中文步骤日志；
- `solve()` 控制流；
- 卡住后的共享回溯 fallback；
- 与旧 `cands` 读取接口兼容。

计算密集循环与日志/UI 语义因此分层，不把字符串和可变 Python 容器硬塞进 nopython 内核。

### 4. `LogicSolver` 与 `ShuduSolver` 不再复制算法

`logical_solver.py` 现在是兼容 facade，保留旧 helpers、CLI 和 Naked Single → Hidden Single 优先级。

`shudu_solver.py` 只保留项目差异：

1. Hidden Single；
2. Naked Single；
3. 其余技巧继承共享 Numba 实现；
4. 提供公开 `next_step()` 结构化 API。

因此两套公开 solver 共享同一核心算法实现，不再出现“项目版本修了、legacy 版本没修”的漂移。

### 5. 自动笔记与逻辑候选共享基础计算

`sudoku_rules.candidate_grid()` 改为复用 Numba 候选位掩码内核。Game 的一键自动笔记、`LogicSolver` 和 `ShuduSolver` 因而共享正式大数字 → 基础候选这一条规则真源。

用户手工笔记仍然是独立状态：

- `Game.notes`：用户可编辑；
- `_masks`：算法内部候选；
- 二者绝不互相偷读。

### 6. 提示层保持只依赖公共 API

`sudoku_hints.py` 继续只调用 `ShuduSolver.next_step()`，不访问 `_apply_next_step()`，也不直接依赖 `sudoku_njit_core`。Numba 属于 solver 内部实现细节，不泄漏到 UI。

### 7. 增加 Numba 架构门禁

新增 `tests/test_njit_core.py`：

- 主动调用全部九个核心 finder；
- 断言每个 Numba dispatcher 都生成 `nopython_signatures`；
- 断言 `LogicSolver` / `ShuduSolver` 都共享 `NumbaLogicSolver`；
- 锁定两者各自的 Single 技巧优先级。

现有架构测试继续防止 rules / hints / game 依赖方向回退。

## 为什么不是“所有代码都 njit”

`njit` 只用于适合 nopython 的计算核心。以下部分明确保留 Python：

- Tkinter 绘制；
- 中文日志字符串；
- 用户笔记字典；
- 撤回快照；
- `LogicStep` / `Hint` 结构化 UI 数据；
- 菜单和键鼠事件。

这些不是性能热点，强行 JIT 会扩大边界复杂度却没有实际收益。当前做法把 Numba 放在真正的 O(81×技巧扫描) 热路径上，符合 KISS 和第一性原理。

## 明确不做的伪优化

### 不为每个技巧创建一个 Python 类

九种技巧现在已经是独立 njit kernel。再套一层 Strategy class 只会增加对象和注册表，没有第二种运行时组合需求。

### 不让 UI 直接持有 NumPy 位掩码

GUI 只需要语义化候选和步骤。把 `_masks` 暴露到 UI 会破坏 solver 边界并让撤回/提示与计算表示绑定。

### 不删除兼容 `cands` 读取接口

当前测试、提示快照和潜在外部调用仍需要 set 形式。它现在是按需快照，不再控制内部算法状态，因此兼容成本很低。

## 验证

GitHub Actions 使用 Python 3.12 + Tk + Xvfb 执行完整回归。全核心 Numba 改造后的最新验证结果：

```text
141 passed in 8.35s
```

其中新增测试明确验证全部核心 finder 进入 Numba nopython 模式。

## 后续触发条件

只有出现以下事实时再继续结构拆分：

1. 需要第二种候选编码或第二种 JIT 后端；
2. GUI 之外出现新的前端并需要共享完整 Game 状态机；
3. 需要持久化 solver session 或跨进程复用中间候选；
4. 性能 profiling 证明 Python 包装层而不是 njit kernel 成为新瓶颈。

在这些触发条件出现前，继续增加抽象不会带来可测收益。
