# ADR 修订草案：提示推荐策略与自动执行配置解耦

- 状态：草案，等待联合方案确认
- 日期：2026-10-05
- 正式 ADR：暂不修改
- 目标：在最终批准后修订 ADR-002 与 ADR-005，使推荐策略与自动执行配置拥有清晰、单一的现行语义

## 1. 需要修订的现行决策

### ADR-002 共享规则内核与求解器公共接口

现行有效部分继续保持：

- solver 拥有候选状态、技巧执行和算法证据；
- `ShuduSolver.next_step()` 返回完整 `LogicStep`；
- Hint 只消费结构化步骤，不重新识别高级算法；
- 用户笔记不是 solver 推理前提。

需要收敛的部分：

- Hint 的步骤选择不能再通过可见 `Game.notes` 间接接受自动算法候选投影；
- 最终 grilling 选择决定“玩家显式候选消除”是否作为独立 recommendation progress。

### ADR-005 本地自动算法偏好与完成动画

需要明确：

- `UserSettings.auto_techniques` 的责任是**自动执行选择集合**；
- 提示/推荐不读取这个集合；
- 提示/推荐固定使用项目支持的全部逻辑算法稳定顺序；
- 算法实现继续共享，配置策略分离，不复制第二套算法。

## 2. 共同目标依赖方向

```text
逻辑算法实现 / 稳定顺序
        ├── recommendation policy: 全部算法 -> first step
        └── auto policy: 用户勾选集合 -> run selected techniques

UserSettings.auto_techniques
        └── auto policy

Game.board
        └── recommendation

Game.notes
        └── 可见笔记 / 玩家交互
```

推荐与自动执行共享算法实现，不共享选择配置。

## 3. 分支 B（推荐）：正式棋盘是推荐选择真源

若 grilling 选择 B，ADR-002 的最终现行语义写为：

1. Hint recommendation 的输入闭集为当前正式棋盘与错误状态。
2. `ShuduSolver.next_step()` 按全部逻辑算法稳定优先级返回第一条 `LogicStep`。
3. `Game.notes` 不参与推荐步骤选择或“已完成”判断。
4. 删除 `already_noted` 和多步 fast-forward 语义。
5. 玩家只改变候选笔记、未改变正式棋盘时，后续提示允许重复同一逻辑消除。
6. Hint 保持只读，不使用 full solve / backtracking。

执行面结果：

- recommendation 从可能多 transition 扫描收缩为一次 `next_step()`；
- read / compute / effect / process / remote 均不扩大。

## 4. 分支 A：保留玩家手工消除推进

若 grilling 选择 A，ADR-002 的最终现行语义写为：

1. visible notes 只负责显示与玩家交互，不作为 recommendation progress 真源。
2. `Game` 显式维护玩家在本应用中完成的 candidate elimination。
3. screenshot 导入 notes 不自动成为玩家逻辑进度。
4. 自动算法生成的 candidate projection 不自动成为玩家逻辑进度；自动算法自己已经证明并执行的 eliminations 由其独立状态表达。
5. recommendation 只在 solver 自己证明同一消除成立后，使用显式玩家进度跳过展示。
6. manual elimination 不进入 solver 候选真源。
7. Snapshot/undo/erase 对显式进度提供完整生命周期。

## 5. ADR-005 的最终共同语义

无论 A/B：

1. 自动算法目录继续提供算法名称、显示标签、稳定顺序与自动默认集合。
2. `UserSettings.auto_techniques` 只表示用户允许自动执行的算法集合。
3. `Game.auto_solve_enabled()` / `ShuduSolver.solve_techniques_result(names)` 只执行该集合。
4. recommendation 不读取 `UserSettings`，也不以自动集合裁剪算法。
5. 自动完成真实改变正式棋盘后，后续 recommendation 根据新棋盘重新计算。

## 6. 不新增 ADR

本变更直接修订 ADR-002 与 ADR-005 已拥有的责任，不另建平行 ADR。正式批准后以现行合同替换冲突段落，并同步：

- `README.md`
- `docs/codebase-design-review.md`
- 架构与行为测试

本草案不改变已接受 ADR 状态。
