# 确认现有 Shudu 可复用能力与接入缺口

Type: research
Mode: AFK
Labels: wayfinder:research
Status: resolved
Assignee: Codex shudu_capabilities
Parent: ../map.md
Blocked by:

## Question

当前 Shudu 的手动填数、选定算法、一键笔记、Hint 与截图输入可复用到哪些边界？外部手机状态接入需要哪些现有接口尚未提供的信息？结论须指向当前源码、测试定义和已接受 ADR。

## Comments

源码只读调查已完成，答案与研究资产已记录；没有运行 GUI、测试或设备命令。

## Answer

现有 Shudu 可直接复用无 GUI 的题面解析、选定算法求解、Hint、笔记计算及 Game 操作能力。截图入口返回 Puzzle 与 notes；Game 将截图全部大数字视作 givens，公开结果没有原图棋盘坐标。当前未见完整棋局持久化或外部设备同步事件入口。目标 iOS App 的识别及点击正确性仍待设备验证。

已完成源码、测试定义与 ADR-001 至 ADR-005 的证据整理；本票解决现状调查问题。外部状态接入的新范围与接口保留给后续业务决定。

研究资产：[Shudu 现有能力与 iOS 接入缺口](../research/existing-shudu-capabilities.md)。资产内含仓库相对源码链接及精确行号定位。
