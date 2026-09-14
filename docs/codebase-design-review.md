# Codebase Design Review

## Status

COMPLETE — 2026-09-14

本轮按 `.claude/skills/engineering/codebase-design` 对提示链、目录结构、完成动画和本地用户偏好继续深化。目标是让算法知识只存在于真正执行算法的 Module 中，让调用方只消费稳定的 Interface；同时把带时间性的视觉效果留在 View，把持久化文件格式留在独立偏好 Module。

## 当前结构

```text
根目录
├─ sudoku_gui.py       GUI 可执行入口
├─ shudu_solver.py     项目级逻辑 solver seam / CLI
├─ logical_solver.py   legacy 兼容入口 / CLI
├─ solver.py           回溯演示入口
└─ techniques.py       技巧演示入口

shudu/
├─ auto_techniques.py       自动算法目录与默认配置真源
├─ user_settings.py         本地用户偏好深 Module
├─ sudoku_njit_core.py      Numba 纯计算核心
├─ sudoku_rules.py          行、列、宫与基础候选规则
├─ sudoku_backtracking.py   公共完整解能力
├─ sudoku_logic.py          solver 状态、技巧编排、算法证据
├─ sudoku_step.py           LogicStep Interface
├─ sudoku_hints.py          LogicStep → Hint 语义适配
├─ sudoku_game.py           游戏状态机与完成单位查询
├─ sudoku_screenshot.py     截图输入深 Module
├─ sudoku_view.py           普通绘制与完成扫光动画
├─ sudoku_hint_view.py      统一提示效果绘制
├─ sudoku_theme.py          主题常量
└─ sudoku_puzzles.py        题面
```

根目录不承载普通实现文件。`tests/test_architecture.py` 会直接失败于新的根级非入口 Python 文件，防止结构重新摊平。

## 1. solver 拥有算法证据

`ShuduSolver.next_step()` 通过一个 `LogicStep` 返回算法已经确定的完整事实：

- `sources`：该步依据格；
- `units`：需要观察的行、列、宫；
- `placements` / `eliminations`：实际动作；
- `candidates`：动作前候选快照。

提示层不重新扫描候选来证明 Naked Pair、Pointing、X-Wing、XY-Wing 等算法，因此修改算法只需要维护 solver 一处，保持 Locality。

## 2. Hint Module 只做语义适配

`shudu/sudoku_hints.py` 只负责：

1. 跳过玩家已经手工完成的合法排除；
2. 将 `LogicStep.sources / units / targets` 转为统一视觉语义；
3. 生成用户可读的中文说明。

算法名字、模式判定和证据所有权集中在 solver；提示文案可以独立调整而不会改变数独规则。

## 3. Hint View 不跨越私有 Interface

普通棋盘与提示效果只复用 `SudokuView.draw_header()`、`SudokuView.draw_grid_lines()` 这两个公开绘制 Interface，不再跨 Module 调用 `_draw_header()`、`_draw_grid_lines()` 等私有实现。

当前只有一个真实 Canvas 实现，因此不额外引入 Protocol、Adapter 注册表或第二套 View abstraction。

## 4. 非入口实现集中到包目录

仓库根目录定义为可执行入口层，内部 Implementation 集中在 `shudu/`。内部依赖使用显式 `shudu.*` 路径，不依赖工作目录偶然性。

## 5. 自动算法目录成为单一真源

自动算法顺序、菜单标签和默认勾选状态统一由 `shudu/auto_techniques.py` 拥有。`ShuduSolver`、`Game` 与本地配置解码都消费同一份目录，不再各自维护算法名称集合。

这个 Module 只描述稳定元数据与校验，不执行求解、不做文件 IO，也不依赖 GUI。

## 6. 本地偏好是独立深 Module

`shudu/user_settings.py` 只暴露：

- `UserSettings`；
- `UserSettingsStore.load()`；
- `UserSettingsStore.save()`。

它在内部隐藏跨平台配置目录、JSON 版本、未知算法兼容和原子替换写入。GUI 不知道 JSON 字段与文件路径；Game/solver 不知道磁盘持久化。

产品入口启动时读取一次配置，设置菜单修改自动算法后保存完整配置。测试可注入临时路径的同一个 Store，不需要增加第二个存储 Adapter。

## 7. 完成动画属于 View 内部行为

“行、列、宫完成”分为三个职责：

- `Game.completed_units()` 只回答当前哪些单位已经按照唯一解正确完成，是无时间、无 Tk 的确定性状态查询；
- `SudokuWindow` 在一个用户动作前后比较完成集合，只把新完成的单位作为事件送给 View；
- `SudokuView.animate_completed_units()` 使用 `after()` 驱动青色扫光帧，只维护瞬态颜色，不修改 board、notes、history 或 Game 状态。

因此规则、事件检测和动画时序分别落在最内聚的位置。删除动画不会改变 Game；替换动画实现也不需要改数独规则。

## 8. 可执行架构门禁

`tests/test_architecture.py` 锁定：

- 根目录只允许五个 Python 可执行入口；
- rules 不向 GUI / Game / Hint / solver orchestration 反向依赖；
- Hint 只依赖项目级 `ShuduSolver` Interface；
- Hint 不调用 solver 私有 step 方法，也不重新实现高级算法模式识别；
- Hint View 不调用普通 View 私有绘制方法；
- 截图深 Module 不依赖 GUI、Game 或 solver；
- 自动算法目录是配置元数据的唯一生产真源；
- 本地偏好 Module 不依赖 GUI、Game、View 或 solver；
- Game/View 不依赖持久化 Module；
- 完成动画的 `after()` 时序只存在于 View，而不进入 Game。

这些测试描述 seam 与依赖方向，不绑定函数内部实现细节。

## 明确不做

- 不为九种技巧各建 Strategy class；现有 Numba finder 已经是内聚的计算实现。
- 不引入 View Protocol；只有一个真实 Canvas 实现，没有第二个 Adapter。
- 不为本地设置创建抽象存储端口；只有一个真实本地 JSON 存储实现，测试直接注入路径。
- 不把 NumPy 位掩码暴露给 Hint 或 GUI。
- 不让用户笔记成为 solver 候选真源。
- 不把完成动画状态存入 Game、撤回快照或用户配置。
- 不保存整局游戏进度；本次只持久化用户要求的自动算法配置。

## 验证

GitHub Actions 使用 Python 3.12 + Tk + Xvfb 执行完整回归。架构、逻辑、GUI、完成动画、本地配置、截图输入与 Numba nopython 门禁都在同一测试套件中验证。
