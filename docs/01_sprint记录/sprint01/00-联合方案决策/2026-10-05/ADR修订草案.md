# ADR 修订草案：提示推荐策略与自动执行配置解耦

- 状态：草案，方向已闭合，待最终确认
- 日期：2026-10-05
- 正式 ADR：暂不修改
- 目标：最终批准后修订 ADR-002 与 ADR-005，使 recommendation 与自动执行配置拥有单一现行语义

## 1. ADR-002 修订方向

继续保持：

- solver 拥有候选状态、技巧执行和算法证据；
- `ShuduSolver.next_step()` 返回完整 `LogicStep`；
- Hint 只消费结构化步骤，不重新识别高级算法；
- 用户笔记不是 solver 推理前提。

修订为：

1. Hint recommendation 的输入闭集为当前正式棋盘与错误状态。
2. `ShuduSolver.next_step()` 按全部逻辑算法稳定优先级返回第一条 `LogicStep`。
3. `Game.notes` 不参与推荐步骤选择或“已完成”判断。
4. 删除 `already_noted` 和多步 fast-forward 语义。
5. 玩家只改变候选笔记、未改变正式棋盘时，后续提示允许重复同一逻辑消除。
6. Hint 保持只读，不使用 full solve / backtracking。

执行面结果：

- recommendation 从可能多 transition 扫描收缩为一次 `next_step()`；
- read / compute / effect / process / remote 均不扩大。

## 2. ADR-005 修订方向

1. 自动算法目录继续提供算法名称、显示标签、稳定顺序与自动默认集合。
2. `UserSettings.auto_techniques` 只表示用户允许自动执行的算法集合。
3. `Game.auto_solve_enabled()` / `ShuduSolver.solve_techniques_result(names)` 只执行该集合。
4. recommendation 不读取 `UserSettings`，也不以自动集合裁剪算法。
5. recommendation 固定使用全部逻辑算法稳定顺序。
6. 自动完成真实改变正式棋盘后，后续 recommendation 根据新棋盘重新计算。
7. 自动算法生成的可见候选继续属于 `Game.notes` 展示状态，不成为 recommendation 输入。

## 3. 目标依赖方向

```text
逻辑算法实现 / 稳定顺序
        ├── recommendation: 全部算法 -> first step
        └── auto execution: 用户勾选集合 -> run selected techniques

UserSettings.auto_techniques
        └── auto execution

Game.board + wrong_cells
        └── recommendation

Game.notes
        └── 可见笔记 / 玩家交互
```

推荐与自动执行共享算法实现，不共享选择配置。

## 4. 同步表面

正式批准后同步：

- `README.md`
- `docs/codebase-design-review.md`
- `tests/test_architecture.py`
- 提示、自动配置、截图导入相关行为测试

本变更直接修订 ADR-002 与 ADR-005 已拥有的责任，不新增平行 ADR。本草案不改变已接受 ADR 状态。
