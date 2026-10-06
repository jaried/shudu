# ADR 修订记录：提示全算法与当前候选状态

- 状态：已同步现行 ADR-002 / ADR-005
- 日期：2026-10-06

## ADR-002

1. `ShuduSolver.next_step()` 是提示的算法 Interface，固定扫描全部逻辑算法。
2. Hint 不读取 `UserSettings.auto_techniques`。
3. 完整 `Game.notes` 可作为当前候选状态投影给 solver。
4. 零散 notes 不作为求解约束。
5. Hint 只请求一次 `next_step()`，不再通过多步 fast-forward 推断用户进度。
6. Hint 保持只读且不进入回溯。

## ADR-005

1. `auto_techniques` 只控制自动执行。
2. Hint 的算法集合始终是全部支持算法。
3. 自动配置与 Hint candidate projection 是两个独立维度：
   - auto config：决定自动执行能力；
   - complete candidate notes：决定 Hint 从哪个候选状态继续。

## 依赖方向

```text
UserSettings.auto_techniques
        -> auto execution only

Game.board
        -> Hint
        -> ShuduSolver

complete Game.notes
        -> candidate-state projection
        -> ShuduSolver

sparse Game.notes
        -> display only
```
