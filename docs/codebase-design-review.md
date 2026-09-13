# Codebase Design Review

## Status

COMPLETE — 2026-09-14

本轮按 `.claude/skills/engineering/codebase-design` 对提示链和目录结构做深化。目标是让算法知识只存在于真正执行算法的 Module 中，让调用方只消费稳定的 Interface，并把非入口实现从仓库根目录收进 `shudu/` 包。

## 当前结构

```text
根目录
├─ sudoku_gui.py       GUI 可执行入口
├─ shudu_solver.py     项目级逻辑 solver seam / CLI
├─ logical_solver.py   legacy 兼容入口 / CLI
├─ solver.py           回溯演示入口
└─ techniques.py       技巧演示入口

shudu/
├─ sudoku_njit_core.py      Numba 纯计算核心
├─ sudoku_rules.py          行、列、宫与基础候选规则
├─ sudoku_backtracking.py   公共完整解能力
├─ sudoku_logic.py          solver 状态、技巧编排、算法证据
├─ sudoku_step.py           LogicStep Interface
├─ sudoku_hints.py          LogicStep → Hint 语义适配
├─ sudoku_game.py           游戏状态机
├─ sudoku_screenshot.py     截图输入深模块
├─ sudoku_view.py           普通游戏绘制
├─ sudoku_hint_view.py      统一提示效果绘制
├─ sudoku_theme.py          主题常量
└─ sudoku_puzzles.py        题面
```

根目录不再承载普通实现文件。`tests/test_architecture.py` 会直接失败于新的根级非入口 Python 文件，防止结构重新摊平。

## 1. solver 拥有算法证据

此前 `ShuduSolver.next_step()` 只返回 placements / eliminations，`sudoku_hints.py` 为了画绿色依据和蓝框，又根据候选重新识别 Naked Pair、Hidden Pair、Naked Triple、Pointing、Box-Line、X-Wing、XY-Wing。

这违反 Locality：修改算法时，需要同时维护 solver 与提示层中的两套模式知识。

现在每个技巧在真正命中时就记录：

- `sources`：该步依据格；
- `units`：需要观察的行、列、宫；
- `placements` / `eliminations`：实际动作；
- `candidates`：动作前候选快照。

`ShuduSolver.next_step()` 通过一个 `LogicStep` 一次返回完整事实。提示层不再扫描候选来重新证明算法。

这使 `LogicStep` 成为 solver 与提示之间唯一的步骤 Interface：实现复杂度留在 solver，调用方获得更高 Leverage。

## 2. Hint Module 只做语义适配

`sudoku_hints.py` 现在只负责：

1. 跳过玩家已经手动完成的合法排除；
2. 将 `LogicStep.sources / units / targets` 转为统一视觉语义；
3. 生成用户可读的中文说明。

已删除提示层中的 `_x_wing_context()`、`_pointing_context()`、`_xy_wing_context()` 等二次识别实现。

算法名字、模式判定和证据所有权因此集中在 solver 一处；提示文案可以独立调整而不会改变数独规则。

## 3. Hint View 不跨越私有 Interface

此前 `sudoku_hint_view.py` 直接调用 `SudokuView._draw_header()` 和 `_draw_grid_lines()`。这让私有实现事实上变成跨 Module 契约。

现在复用能力被明确为两个公开绘制 Interface：

- `SudokuView.draw_header()`；
- `SudokuView.draw_grid_lines()`。

提示效果只通过公开绘制 Interface 与通用 Canvas primitives 工作，不再访问 `SudokuView` 私有方法。没有为此增加 Protocol、Adapter 注册表或第二套 View abstraction，因为当前没有第二个真实实现需要那个 seam。

## 4. 非入口实现集中到包目录

目录调整不是按“每个类一个文件”机械拆分，而是把仓库根目录定义为可执行入口层，把内部实现集中到 `shudu/`。

这样做的收益：

- 根目录直接表达“怎么运行”；
- 内部依赖使用显式 `shudu.*` 路径，不依赖工作目录偶然性；
- 测试和维护者可快速区分入口 Interface 与内部 Implementation；
- 不新增无真实变化需求的 Adapter 或抽象基类。

## 5. 可执行架构门禁

`tests/test_architecture.py` 现在锁定：

- 根目录只允许五个 Python 可执行入口；
- rules 不向 GUI / Game / Hint / solver orchestration 反向依赖；
- Hint 只依赖项目级 `ShuduSolver` Interface；
- Hint 不调用 solver 私有 step 方法；
- Hint 不重新实现高级算法模式识别；
- Hint View 不调用 View 私有绘制方法；
- 截图深模块不依赖 GUI、Game 或 solver；
- GUI 只通过截图 loader Interface 使用图像识别。

这些测试描述的是 seam 和依赖方向，而不是具体函数内部写法。

## 明确不做

- 不为九种技巧各建 Strategy class；现有 Numba finder 已经是内聚的计算实现。
- 不引入 View Protocol；只有一个真实 Canvas 实现，没有第二个 Adapter。
- 不把 NumPy 位掩码暴露给 Hint 或 GUI。
- 不让用户笔记成为 solver 候选真源。
- 不因为移动目录改变现有启动命令和 GUI 行为。

## 验证

GitHub Actions 使用 Python 3.12 + Tk + Xvfb 执行完整回归。架构、逻辑、GUI、截图输入与 Numba nopython 门禁都在同一测试套件中验证。
