# Codebase Design Review

## Status

COMPLETE — 2026-09-13

本轮按 `improve-codebase-design` 目标对整个仓库做结构审查，不以“文件越多越好”为目标，而以职责边界、依赖方向、重复规则、稳定 API、可测试性和回归成本为判断标准。

## 结论

当前最值得优化的不是继续拆 GUI，也不是把每个数独技巧拆成一个文件，而是消除**领域规则重复**和**跨层访问私有求解器实现**。这两项已经完成，并增加 CI 作为长期回归门禁。

## 已完成的结构优化

### 1. 提取 `sudoku_rules.py` 作为纯领域规则内核

统一定义：

- `Cell`、`CELLS`；
- 行、列、宫及 `UNITS`；
- `PEERS` / `related()`；
- `unit_name()`；
- 仅由正式大数字推导的 `candidate_grid()`。

它不依赖 GUI、Game、LogicSolver 或用户笔记。这样 UI、游戏状态和提示层不会各自维护一套“同行/同列/同宫”的定义。

### 2. `ShuduSolver` 成为唯一项目级逻辑求解入口

`logical_solver.py` 保留为既有算法实现库；`shudu_solver.py` 负责项目策略：

1. Hidden Single；
2. Naked Single；
3. Pair / Triple / Pointing / Box-Line / X-Wing / XY-Wing。

同时新增稳定的 `next_step()`，返回不可变 `LogicStep`。调用方不再直接访问 `_apply_next_step()`。

### 3. 提示层只依赖公共 API

`sudoku_hints.py` 现在只依赖：

- `ShuduSolver.next_step()`；
- `sudoku_rules` 的拓扑；
- `LogicStep` 的结构化差异。

提示层不再从 `logical_solver.py` 导入 `UNITS`、`row_cells()`、`box_cells()` 等内部 helper，也不再直接调用求解器私有方法。

### 4. Game 不再依赖 `logical_solver.py`

一键自动笔记改为调用 `sudoku_rules.candidate_grid()`。

因此用户交互状态与算法实现完全分离：

- `Game.notes`：用户可编辑的小数字；
- `ShuduSolver.cands`：算法自己的候选状态；
- `candidate_grid()`：只依据正式大数字计算的基础合法候选。

三者语义现在明确且互不偷读。

### 5. 统一领域类型

`sudoku_step.py` 复用 `sudoku_rules.Cell`，不再重复定义坐标类型。`LogicStep` 继续作为 GUI 提示与求解器之间的不可变数据边界。

### 6. 增加长期 CI 门禁

新增 `.github/workflows/tests.yml`：

- Python 3.12；
- 安装 Tk / Xvfb；
- 运行完整 `pytest`；
- GUI 测试在虚拟显示中执行，而不是静默跳过。

首个 GitHub Actions run 已通过。

## 当前依赖方向

```text
sudoku_rules.py        纯领域规则，无项目上层依赖
        ↑
logical_solver.py      既有算法技巧实现
        ↑
shudu_solver.py        项目优先级 + 公共 next_step API
        ↑
sudoku_hints.py        只读提示适配
        ↑
sudoku_game.py         游戏状态 / 用户笔记 / 撤回 / 计时
        ↑
sudoku_view.py         绘制
        ↑
sudoku_gui.py          窗口与输入编排
```

`solver.py` / `sudoku_backtracking.py` 仍提供完整解与校验能力，Game 只在题面载入时使用它得到标准答案。

## 明确不做的“伪优化”

### 不把 `logical_solver.py` 拆成九个技巧文件

它虽然较大，但这些技巧共享同一 `board/cands` 状态、单位遍历和传播机制。当前强行按技巧拆文件会增加跳转、参数传递和注册层，却没有第二套算法状态模型需要复用，属于复杂度搬家。

### 不引入策略框架、依赖注入容器或事件总线

当前只有一个桌面应用、一个项目级技巧优先级。`ShuduSolver` 这一层 seam 已足够替换策略，再增加抽象没有新的调用方支撑。

### 不把 GUI 继续按每个按钮拆类

`sudoku_view.py` 已把主题和提示视图拆开。剩余普通棋盘/工具栏共享同一个 Canvas 坐标系和缩放状态，继续拆分会制造跨对象绘制协调，收益低于成本。

### 保留 `techniques.py` 演示文件

它不是生产调用路径，只承担教学演示。生产规则已经统一在 `sudoku_rules.py` + `ShuduSolver`；为删除一个独立演示脚本而扩大兼容性变更没有收益。

## 验证策略

新增 `tests/test_sudoku_rules.py` 检查：

- 81 格、27 个单位、每格 20 个 peer；
- `related()` 对称性；
- 新共享候选与旧 `logical_solver.init_candidates()` 等价；
- 候选计算不修改棋盘。

`tests/test_shudu_solver.py` 改为通过公共 `next_step()` 验证首步 Hidden Single 和结构化落子，不再让测试把私有 `_apply_next_step()` 当作项目 API。

## 后续触发条件

只有出现以下事实时才继续结构拆分：

1. 第二种求解器状态模型需要复用高级技巧；
2. 多个前端需要共享 Game 状态机；
3. 普通棋盘视图出现第二套渲染后端；
4. `logical_solver.py` 的技巧修改开始频繁产生跨技巧回归。

在这些触发条件出现前，当前边界已经满足 KISS、DRY、YAGNI、高内聚低耦合和可测试性要求。
