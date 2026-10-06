# ADR 修订记录：提示全算法与现有笔记候选状态

- 状态：已同步现行 ADR-002 / ADR-005
- 日期：2026-10-06

## ADR-002

1. `ShuduSolver.next_step()` 是提示的算法 Interface，固定扫描全部逻辑算法。
2. Hint 不读取 `UserSettings.auto_techniques`。
3. `Game.notes` 按格投影当前候选状态：
   - 有 notes 的格使用现有候选；
   - 无 notes 的格保持 solver 基础候选。
4. 不要求 notes 覆盖全部空格。
5. Hint 只请求一次 `next_step()`。
6. Hint 保持只读且不进入回溯。

## ADR-005

1. `auto_techniques` 只控制自动执行；`set_auto_technique()` 只修改配置，不立即改变当前棋盘或笔记。
2. Hint 的算法集合始终是全部支持算法。
3. 自动配置与 notes 候选状态是两个独立维度：
   - auto config：决定自动执行能力；
   - existing notes：逐格决定 Hint 当前候选状态。

## 依赖方向

```text
UserSettings.auto_techniques
        -> auto execution only

Game.board
        -> Hint
        -> ShuduSolver

existing Game.notes
        -> per-cell candidate projection
        -> ShuduSolver
```
