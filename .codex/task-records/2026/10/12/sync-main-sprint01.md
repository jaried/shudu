# main 与 Sprint01 同步和推送

- 请求：确认主工作树分支，同步 main 与 Sprint01 的已提交内容，并推送两个分支。
- 模式：Git 分支同步与发布。
- 记录状态：发布前核验与操作范围已定稿；后续 Git 结果直接读回并在交付时汇报。
- 主工作树：/mnt/d/Tony/Documents/invest2026/projects/shudu，当前分支 Sprint01。
- 请求绑定：codex:branch-sync:0d7f02ce-cf83-4c7c-8995-1469e3a11faa
- 写入范围：本任务记录、main 的快进分支引用、两分支的 origin 远端引用及追踪配置。
- 工作区现有 253 项未提交改动保持原样。
- 临时目录：/mnt/d/temp/shudu-branch-sync-ff5JdC，真实路径相同；本任务持有，保存恢复状态和 TaskLifecycle journal，任务结束保留在 Git 外。
- 工具限制：宿主未提供 update_plan，步骤保存于本记录；ponytail Skill 未找到，其余固定 Skill 沿会话规则执行。

## 核验步骤

1. completed：核对主工作树、main 与 Sprint01 的分支关系。main 无独有提交，Sprint01 多 70 个提交。
2. completed：刷新 origin/main 与 origin/Sprint01。远端 main 是当前 Sprint01 的祖先，远端 Sprint01 与本地一致，两个推送目标均满足快进条件。
3. completed：核验本任务记录以外的状态与初始状态一致，暂存区为空；同步范围、保留边界和读回标准已明确。

## Git 收尾动作与完成标准

本记录由 TaskLifecycle writer 写入，经 AutoCommit 仅提交本记录。随后以原 main 提交为比较条件，将 main 快进到 Sprint01 的最新提交；主工作树继续使用 Sprint01。向 origin 原子推送 main 与 Sprint01 两个分支。

交付前从 Git 核验本地两分支具有相同提交和 tree、远端两分支均指向该提交、主工作树分支保持 Sprint01，且既有未提交状态原样保留。本轮不改动运行代码；验证覆盖分支关系、精确提交路径、文件内容一致性和远端读回。
