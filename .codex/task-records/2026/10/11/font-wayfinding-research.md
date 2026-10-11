# 界面文字修复路线研究

- 请求：调用 engineering:wayfinder、engineering:research、no-negative-echo，继续已登记的界面文字缩放锯齿与乱码问题。
- 当前模式：规划与研究。
- 用户已确认：同时覆盖 Linux 和 Windows。
- 完成状态：本轮路线建图与研究已完成；渲染路线选择、原型及正式验收规格由后续决策承接。
- 请求绑定：codex:font-wayfinding:009effa7-c675-4867-9844-6ac3656d3489
- 仓库逻辑路径：/home/tony/projects/shudu
- 仓库真实路径：/mnt/d/Tony/Documents/invest2026/projects/shudu
- 进度工具：当前宿主未提供 update_plan；步骤保存于本记录。
- 固定工具缺口：ponytail Skill 未找到；其余固定 Skill 沿当前会话规则执行。
- 临时目录与真实目录：/mnt/d/temp/shudu-font-research-zhLggI；owner 为本次研究；保存探测原件、任务状态及恢复数据，当前保留在 Git 外。

## 步骤与结果

1. completed：核对技能路由、已有需求与领域术语；用户明确确认 Linux 与 Windows。
2. completed：建立本地决策地图和四张子票，记录父子关系与阻塞依赖。
3. completed：后台 Agent 核对官方资料并交付单份研究报告；主 Agent 完成当前 Linux 环境、字体选择及加载库的只读核验。
4. completed：研究票写入答案并置 resolved，地图记录结果索引。唯一可继续的决策为“选择文字渲染路线与字体交付策略”。
5. completed：实际读回最终文档，检查六个本地链接、四张子票的依赖和状态；校验通过。冻结下列七个文件作为精确提交集合。

## 研究结果与验证边界

- 当前 Linux 的 uv Tk 9.0.4 较强地符合 X core 字体后端；系统 Fontconfig 可匹配的 Noto/DejaVu 在 Tk 中不可见。
- 源码将 named font TkDefaultFont 用作 family，实测得到 fixed；正确读取或复制 named font 得到 nimbus sans l。应用在窗口尺寸变化时重算字号并重建文字。
- 候选路线、官方来源和 ADR 边界已写入研究报告。优先验证原生 Tk 运行时的抗锯齿能力与字体选择，再决定字体交付方式。
- Windows 的真实字体平滑与 DPI 行为、原乱码字符、候选修复的实际视觉质量仍待验证；后续人工决策保持 open。
- 本轮文档核验通过；运行代码和正式 ADR 的修改属于后续批准阶段。

## 精确提交集合

- .scratch/font-rendering/map.md
- .scratch/font-rendering/issues/01-rendering-and-glyph-research.md
- .scratch/font-rendering/issues/02-rendering-and-font-policy.md
- .scratch/font-rendering/issues/03-scaling-visual-prototype.md
- .scratch/font-rendering/issues/04-cross-platform-acceptance.md
- docs/05_预研/界面文字清晰度与乱码/2026-10-11/字体与渲染技术研究.md
- .codex/task-records/2026/10/11/font-wayfinding-research.md

本记录随上述文件进入同次提交。提交 hash、消息、实际路径、任务范围状态、暂存区和范围外状态由提交后的实际 Git 读回确认，并在交付时汇报；原始回执保留在 Git 外。范围外并行修改继续保留。
