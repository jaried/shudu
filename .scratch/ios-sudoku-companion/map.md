# Shudu 与 iOS 数独双向同步伴玩

Labels: wayfinder:map
Status: charted
Created: 2026-10-07

## Destination

形成可实施的接入规格：在电脑上的现有 Shudu 中手动操作、按指定算法自动求解、一键笔记和查看提示，将需要应用的操作回写到已安装的 iOS 数独 App；用户直接在手机上操作后，电脑自动同步棋盘与笔记。明确免费设备接入、盘面识别、操作对应、同步语义和真机验收条件。

## Notes

- 用户已确认：功能与现有 Shudu 一致，包含电脑操作和手机手动操作后的自动同步；软件免费，当前没有开发者账号，完全没有可用 Mac。Windows 10 与 Ubuntu 26 均为候选。
- 目标 App 已选定，具体名称、手机型号和 iOS 版本尚未提供。普通 Apple 账户免费侧载条件由相应人工决策票确认；本轮只做研究和地图登记。
- 当前 Git 根是 `D:/Tony/Documents/invest2026/projects/shudu`，逻辑入口 `D:/Tony/projects/shudu` 的父目录是 junction。调查基线为 Sprint01 / `bf3d8d4cd0466ca80eb23e7eb3df8324a7cdd9bb`，调查前工作树干净。文档写入使用真实根。
- Tracker 采用 engineering:wayfinder 的 Local Markdown 合同，地图和决策票存放于当前目录；现有 Sprint tracker 保留其业务状态。
- 领域词汇见 [CONTEXT.md](../../CONTEXT.md)。架构遵守已接受的 [ADR-002](../../docs/02_架构决策记录/ADR-002-共享规则内核与求解器公共接口.md) 与 [ADR-004](../../docs/02_架构决策记录/ADR-004-截图输入深模块.md)，以及该目录其余已接受 ADR。
- 每次继续先读本地图、开放票状态及当前 Git/ADR。研究调用 engineering:research、anysearch（沿用当前系统代理）、evidence-calibrated-reasoning；人工决策调用 productivity:grilling、engineering:domain-modeling、engineering:codebase-design。实施规格形成后再进入对应实施流程。
- 电脑求解和界面控制是不同能力。现有截图与 solver 的成功不能作为手机控制或双向同步已成功的证据。
- 研究票答案和细节仅保存在各票的 Answer 与其资产中；本地图保留摘要索引。

## Decisions so far

- [核验无 Mac 和开发者账号的免费设备接入](issues/02-free-device-control.md)：已找到有源码和作者实机案例的 Windows 免费侧载候选 SideTap；包准备、用户设备和 Ubuntu 免费首次准备链仍需验证。
- [确认现有 Shudu 可复用能力与接入缺口](issues/03-existing-shudu-capabilities.md)：现有识别、笔记、Hint 和选定算法可复用；手机观测、线索/已填值区分、动作回写及同步需要后续接入决定。

## Not yet specified

- 目标 App 的实际字体、数字颜色、笔记排布、数字键盘、提示和完成页面可能引出新的识别或操作问题；取得真实样本后再判断是否需要额外票。
- 连续多局、难度选择和非棋盘页面的范围，待第一局的伴玩与同步规格明确后再判断。
- 真机稳定性、同步耗时及恢复体验的具体目标，待接入能力和基本同步策略明确后确定。

## Out of scope

- 付费软件订阅与付费开发者计划的采购，超出本次免费的成本约束。
- 支持所有 iOS App 的通用远控平台，超出本次指定数独 App 的目标。
- 本轮生产代码实施和现行 ADR 修订，地图阶段交付决策路径及待确认事项。
