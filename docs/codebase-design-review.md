# Codebase Design Review

## Status

COMPLETE — 2026-09-13

## Review goal

按 `improve-codebase-design` 的目标检查本次“优先 Hidden Single”需求是否应该继续直接改动大型 `logical_solver.py`，以及 GUI、提示层与求解器之间是否出现职责漂移。

## Current design

- `logical_solver.py`：既有完整逻辑技巧实现，已经包含 Hidden Single、Naked Single 和高级排除技巧。
- `sudoku_hints.py`：把求解器的一步动作转换为只读 GUI 提示。
- `sudoku_game.py`：用户输入、手工笔记、撤回、错误计数等游戏状态。

算法候选 `LogicSolver.cands` 与 `Game.notes` 本来就是两种不同状态：前者由正式大数字推导，后者由用户维护。保持这条边界是本次最重要的设计约束。

## Decision

### 1. 增加稳定的项目级 solver seam

新增 `shudu_solver.py`，`ShuduSolver` 继承既有 `LogicSolver`，只负责定义 shudu 项目的技巧优先级：

1. Hidden Single：某行、列或宫里，某个数字在**算法自己的候选**中只剩一个落点，直接填写；
2. Naked Single：某一格只剩一个算法候选；
3. 后续继续复用既有 Pair / Triple / Pointing / Box-Line / X-Wing / XY-Wing。

这样既满足新优先级，又不复制任何高级算法。

### 2. GUI 提示依赖项目级 solver，而不是修改用户笔记

`sudoku_hints.py` 改为实例化 `ShuduSolver`。提示推演继续发生在 solver 副本中，算法候选不读取 `Game.notes`；用户笔记仍只用于判断某个“删除候选”的提示是否已经由用户手工完成。

### 3. 不为一次优先级变化重写 monolithic solver

没有把 `logical_solver.py` 立即拆成九个技巧文件，也没有引入策略注册框架。当前只有一个项目需要覆盖优先级，继承 seam 比大范围搬迁更小、更可回滚，也符合 KISS / YAGNI。

## Dependency direction

```text
logical_solver.py   （稳定的既有技巧实现）
       ↑
shudu_solver.py     （项目级优先级 / 对外入口）
       ↑
sudoku_hints.py    （只读提示适配）
       ↑
sudoku_game.py / sudoku_gui.py
```

## Technical debt kept explicit

`logical_solver.py` 仍同时包含候选管理、拓扑 helpers 和技巧实现。若未来第二个调用方也需要不同的候选策略，届时再把候选/拓扑提取到独立规则模块；当前没有足够收益证明应扩大本次重构范围。
