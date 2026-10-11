# 界面文字跨平台清晰度与字符完整性修复路线

Labels: wayfinder:map
Status: charted
Created: 2026-10-11

## Destination

形成可交给“界面文字缩放锯齿与乱码”正式方案决策的修复路线：明确 Linux 和 Windows 的文字渲染、字体获取、中文与符号覆盖，以及窗口缩放和 DPI 验收场景。终点是待决问题均有真实答案并形成可实施规格。

## Notes

- 用户已批准的需求见[界面文字缩放锯齿与乱码](../../docs/01_Sprint记录/sprint01/S1-09/S1-09_原始需求.md)。本轮用户明确选择同时覆盖 Linux 和 Windows。
- 本轮模式为规划与研究。正式 Sprint 状态继续由现有[待办清单](../../docs/00_待办列表/Sprint待办列表/Sprint01.md)维护。
- Tracker 沿用仓库已有 Local Markdown 约定：地图与独立子票在本目录，阻塞关系写在子票的 `Blocked by`，认领通过 `Status` 与 `Assignee`，答案写在票的 `Answer`。
- 每次继续先读本地图和当前开放子票。研究使用 engineering:research 与 evidence-calibrated-reasoning；人工决策使用 productivity:grilling、engineering:domain-modeling 和 engineering:codebase-design；最终产物使用 no-negative-echo。
- 沿用[领域词汇](../../CONTEXT.md)区分正式数字与候选笔记。架构服从[现行 ADR](../../docs/02_架构决策记录/README.md)，尤其是设置菜单的 Tk Adapter 与资源生命周期要求；架构取舍在后续批准时处理。
- 分别核验字形轮廓的可缩放性、屏幕抗锯齿、字符覆盖与字符串编码，以实际显示满足清晰度和字符完整性要求。
- 研究资产位于 `docs/05_预研/界面文字清晰度与乱码/2026-10-11/`；原始日志和截图保留在本次系统临时目录，Git 只保存研究结果和必要来源定位。

## Decisions so far

- [核验现有文字渲染链与字体字符覆盖](issues/01-rendering-and-glyph-research.md)：已取得 Linux 字体后端与默认字体选择的实测结果；优先验证原生 Tk 路线，Windows 与原乱码场景继续按报告中的边界核验。

## Not yet specified

- 原乱码对应的具体字符、页面和运行环境尚未明确；补齐场景后，判断是否需要独立的编码或缺字诊断。
- 后续验证若发现特定符号或原生控件存在独立限制，再细化专项决策。
- 两平台候选路线的实际缩放表现和 DPI 差异，可能提出额外的跨显示器验证问题。

## Out of scope

本轮交付决策地图与研究结果；运行代码和正式 ADR 的修改由后续已批准实施阶段承接。
