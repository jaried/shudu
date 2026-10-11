# Windows 字体路线续接

- 请求：拉取 417f79f，继续 wayfinder、grill-with-docs 与 no-negative-echo；运行环境为 Windows。
- 日期：2026-10-12。
- 模式：规划与决策。
- 仓库逻辑路径：D:\Tony\projects\shudu。
- 仓库真实路径：D:\Tony\Documents\invest2026\projects\shudu。
- 临时目录与真实目录：D:\temp\shudu-font-wayfinding-windows-20261012-uGGtQy；owner 为本次 Windows 字体路线续接。
- 临时对象：5 个既有文件备份、路径对齐清单、恢复信息及本次 writer 输入；保留供复查，清理尚未授权。

## 步骤与结果

1. completed：获取 417f79f，确认来自 origin/Sprint01，当前 main 可以快进。
2. completed：核对 265 个未提交路径；257 个与目标内容一致，3 个删除已被目标包含，5 个文件不同。用户明确批准备份并以目标版本对齐。
3. completed：robocopy /SJ /SL 备份 5 个文件，核对原始字节一致；将已核对路径对齐并快进 main 至 417f79f。操作后工作区、暂存区干净，无冲突，与 origin/Sprint01 为 0/0。
4. completed：只读核对 Windows 系统字体、ClearType 与 DPI；Anaconda Tk 8.6.14、uv 已安装 Tk 8.6.12 的隐藏探针分别成功。项目 .venv 缺少 Windows 解释器，真实 GUI 与高 DPI 观感尚未验证。
5. completed：用户确认原生 Tk 与系统字体路线，首选字体缺失时列出名称、使用系统回退并保持正常使用。原乱码发生于 Linux。完整路线已由用户确认，当前决策票置 resolved。
6. completed：保存结果摘要、路线答案与地图索引；本轮唯一决策已完成，下一张为“验证候选文字方案的缩放观感”。

## 当前决策与交付范围

- 决策真源：.scratch/font-rendering/issues/02-rendering-and-font-policy.md。
- 地图：.scratch/font-rendering/map.md。
- Windows 结果摘要：docs/05_预研/界面文字清晰度与乱码/2026-10-12/Windows字体与DPI核验.md。
- 当前任务记录：.codex/task-records/2026/10/12/windows-font-policy.md。
- 生产代码与正式 ADR 由后续批准工程阶段承接。S1-09 的真实修复与业务验收尚未完成。
- Git 仅保存结果文档和当前任务记录。原始输出在会话中消费，备份与 writer 恢复数据留在 Git 外。
- 路线与 Windows 结果摘要已精确提交为 0bcbf51，实际提交仅含上述四个文件，Git 与 AutoCommit readback 成功。
- 当前遗留收尾集合为本任务记录与 docs/01_Sprint记录/sprint01/S1-09/S1-09_遗留问题.md；提交结果由 Git 直接读回确认。

## 遗留与处理

- LEG-S1-09-004：自动远端同步返回 rejected / run_binding_required。本地交付已确认，远端发布尚未完成；由全局 AutoCommit / RemoteSync Runtime 后续承接。
- LEG-S1-09-005：Legacy Record authority producer 返回 invalid_locator。按同一正式合同语义等效完成记录，复用 TypeScript 的 TOML 解析、ID 分配与验证能力；全局 Runtime 定位问题保持 open。
- 已读回同一 machine block 中的五个 open 条目；既有三项保留。原始回执和执行输入保留在 Git 外。
