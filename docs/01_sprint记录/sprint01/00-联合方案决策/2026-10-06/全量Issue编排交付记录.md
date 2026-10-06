# Sprint01 全量 Issue 编排交付记录

四个批准的 Issue 已完成设计、独立评审、实施、必要整改、Sprint 集成与真实测试，均进入待验收。依赖保持 S1-01 → S1-02、S1-03；S1-04 独立。上游待验收后释放下游实施，S1-02/S1-03 并行由各自 Luna Worker 完成，Leader/HOST 负责跨 Issue 集成。

| Issue | 内容 | 实际状态 | 依赖 | 已进入 Sprint 的正式源尖端 |
| --- | --- | --- | --- | --- |
| S1-01 | 求解模块目录迁移 | 待验收 | — | `f7b03aa2b7887b0c507cc00327baf70c00837c4a` |
| S1-02 | 单步事实能力 | 待验收 | S1-01 | `1f368d528e8040f8eb4dc9b162521db9643bd6b9` |
| S1-03 | 自动结果能力 | 待验收 | S1-01 | `86a671eb820f03542544553ed871d5904f7a3895` |
| S1-04 | 设置菜单能力 | 待验收 | — | `61d15ac59001e66799d49ff3acc23cf152ff377d` |

完整组合的共同被测 Git tip 为 `594be277321bc5d438422eddeac0caa09a96dbd6`，本记录观察 tip 为 `0e5eb06cee85f5fbfb272d2ba306e40f06385659`，两者之间的产品、测试和依赖声明保持相同。

- `S1-03-required-1`：101 passed in 9.34s，退出码 0。
- `S1-03-full`：269 passed in 28.73s，退出码 0。
- `S1-03-capability-integration`：42 passed in 2.16s，退出码 0。

能力执行面：7 个版本化固定场景的外部结果与基线一致，各调用数保持在原预算内，数组输入范围保持 9×9。新进程读回公开导入不加载单步、证据、自动或差分实现；单步调用只加载单步与证据，自动调用只加载自动与差分，兼容元数据成功路径只加载必要差分。无进展的自动扫描从每个 finder 的 Python 候选投影收敛到 mask pass。具体计数与输入形状见 [联合执行面与回归读回](证据/联合执行面与回归读回.json)。

S1-03 首评的按需导入问题由原 Worker 修正，同一 Reviewer 定向复核关闭唯一 finding。两处真实合并冲突由 Leader 组合已批准的单步/自动实现，保持两个公开能力局部导入，单步 finally 清理及自动 Numba 差分。方案与测试迁移依照 ADR-002/003/005 和逐票冻结设计执行。

测试门禁保留原始 237 passed / 1 Tk setup error 两次记录；S1-04 承接资源修复后完整回归真实通过，最终组合完整回归通过。四票各自 required、独立 Reviewer、正式版本及 MainDelivery receipt 均有真实读回。

后置收尾：四票正式 Issue worktree 与已合并分支均经公开 owner 核对边界、clean 状态及 ancestry 后清理；本次仅使用正式 Issue worktree。四票候选扫描各为 0，MD/HTML 报告齐备，PostIssueCloseout 均为 done/present/completed。前台 DAG 检查每 30 秒执行并在四票待验收后退出；阶段完成即续派，健康检查每 5 分钟。最终 ready 集合为空。

Runtime 遗留保留于各票记录：路径/版本读取、AutoCommit、任务 journal、merge readback 和 closeout binding 的实际错误沿原合同语义续接；真实测试和 Issue 依赖各自验证。对应 Runtime owner 后续以真实回归关闭开放记录。已验证的环境修复记录已关闭。

远端读取退出码 128，实际错误为 `Permission denied (publickey)`；远端 Sprint SHA 与同步完成状态保留为未验证。RemoteSync 公开回执与真实 SSH stderr 保存于收尾 JSON。

[全量编排收尾读回](证据/全量编排收尾读回.json) 保存各票 sourceTip、MainDelivery、PostIssueCloseout、cleanup 命令及结果、实际测试原文、Legacy machine facts、合并决议、DAG 和远端结果。用户业务验收由后续 acceptance 阶段执行。
