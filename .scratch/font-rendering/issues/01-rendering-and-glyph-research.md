# 核验现有文字渲染链与字体字符覆盖

Type: research
Mode: AFK
Labels: wayfinder:research
Status: resolved
Assignee: Codex font_research
Parent: ../map.md
Blocked by:

## Question

Shudu 的数字、候选笔记、中文、界面符号、菜单和提示分别经过哪些渲染入口？当前 Linux 环境的实际字体与 Tk 后端是什么，哪些字形覆盖或配置能够解释锯齿与乱码？Linux 和 Windows 官方接口支持哪些修复能力，哪些结论必须靠实际显示验证？给出一手来源、已验证事实和仍待定位的范围。

## Comments

研究由后台 Agent 核对一手资料，主 Agent 完成本机只读核验。

## Answer

已核对 Canvas、Text、菜单和 ttk 的文字入口。当前 Linux 的 uv Tk 9.0.4 较强地符合传统 X core 字体路径；系统已安装的 Noto Sans CJK SC 与 DejaVu Sans 在 Tk 中不可见。源码把 named font `TkDefaultFont` 用作 family，实测回退到 `fixed`，正确读取或复制 named font 则得到 `nimbus sans l`。应用随窗口尺寸重新计算字号并重建文字。

优先验证原生 Tk 运行时的抗锯齿能力与字体选择语义，再决定字体交付策略。Windows 的字体平滑、DPI 感知，以及原乱码字符对应的实际字形仍需真实环境验证。字体资产注册和更换渲染后端分别涉及资源与架构取舍，由后续人工决策处理。

研究资产：[界面文字清晰度与乱码技术研究](../../../docs/05_预研/界面文字清晰度与乱码/2026-10-11/字体与渲染技术研究.md)。报告保存结论、官方来源、验证边界与候选路线；原始核验输出保留在 Git 外。
