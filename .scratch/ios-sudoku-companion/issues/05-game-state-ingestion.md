# 决定手机盘面如何接入 Shudu 棋局

Type: grilling
Mode: HITL
Labels: wayfinder:grilling
Status: open
Assignee: unassigned
Parent: ../map.md
Blocked by: 03, 04

## Question

如何保留题面线索与玩家已填值的区别，并把后续手机观测应用到同一局 Shudu？确定首次接入中途棋局、新局识别、笔记恢复、撤销历史和算法已证明删除的语义。

当前截图入口返回 Puzzle + notes，Game 会将 Puzzle 中所有大数字作为线索数；直接重复导入截图会把玩家已填值固定，不能直接作为双向同步方案。保持原截图能力合同，若需要新能力或 ADR 修订，形成可供用户判断的具体草案。
