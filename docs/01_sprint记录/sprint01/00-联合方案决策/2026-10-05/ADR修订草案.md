# ADR 修订记录：提示算法事实与候选进度分离

- 状态：已同步现行 ADR-002 / ADR-005
- 日期：2026-10-06

## 1. ADR-002 现行语义

继续保持：

- solver 拥有候选状态、技巧执行与算法证据；
- `ShuduSolver.next_step()` 返回完整 `LogicStep`；
- Hint 不重新识别高级算法模式；
- 用户笔记不是 solver 推理前提。

补充：

1. Hint 固定使用全部逻辑算法，不读取自动算法配置。
2. 算法成立只由正式棋盘与 solver 候选状态决定。
3. `Game.notes` 只作为候选删除进度。
4. elimination 已全部反映在 notes 时，Hint 在同一 solver 内推进到下一步。
5. 部分完成时只暴露仍待删除的候选。
6. `LogicStep` 保留完整算法事实，`Hint.pending_eliminations` 表达当前 UI 动作。
7. Hint 保持只读，不使用 full solve / backtracking。

## 2. ADR-005 现行语义

1. `UserSettings.auto_techniques` 只控制自动执行。
2. `Game.auto_solve_enabled()` / `ShuduSolver.solve_techniques_result(names)` 只执行用户勾选集合。
3. Hint 不读取该集合，始终可使用全部逻辑算法。
4. 自动执行产生的 notes 与截图/玩家 notes 一样，只能作为 Hint 的候选删除进度，不能成为算法证明。
5. 正式棋盘变化后，Hint 基于新棋盘重新计算算法事实。

## 3. 依赖方向

```text
Game.board
   -> ShuduSolver
   -> LogicStep
   -> Hint

Game.notes
   -> Hint progress projection
   -> pending_eliminations

UserSettings.auto_techniques
   -> auto execution only
```

推荐与自动执行共享算法实现，不共享选择配置；Hint 的算法事实与用户候选进度也保持分离。
