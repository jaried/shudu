# 算法菜单连续选择

- 日期：2026-10-06。
- 请求：修改一个算法后保留菜单，继续选择其他算法；鼠标移到“自动解决算法”自动展开子菜单；沿用旧菜单的“✓”标记。
- 范围：sudoku_gui.py、shudu/settings_popup.py、tests/test_auto_technique_settings.py、README.md 与本记录。
- 目录：沿用已核验的 global_only / use_skill_in_project；逻辑写入目录和真实仓库为 D:/Tony/Documents/invest2026/projects/shudu，目标父目录位于仓库边界内。
- 基线：main，HEAD 82ae2d78632cd1753ab9c4a92560de9d99043dea；本任务开始时工作树和暂存区干净。
- 架构：遵守 ADR-005；Tk 菜单元数据继续复用算法目录、原 BooleanVar 与原回调；SettingsPopup 隐藏展示、悬停、定位、焦点、图标和抓取生命周期。Game、solver 与本地偏好格式沿用现有合同。
- 行为：悬停算法入口自动展开；启用项显示“✓”，未启用项留空；每次选择立即保存，设置列和算法列继续展开。Esc、点击外部、失焦或关闭应用释放抓取并销毁菜单。
- 状态：菜单配置不修改盘面、笔记和撤回历史；总开关与逐项选择仍联合保存。
- 边界整改：使用指针所在 Windows 显示器的工作区，接受负坐标；右侧不足向左展开，定位预留完整算法列高度；隐藏子菜单时移走其焦点；拖出菜单项松开时取消命令；销毁时立即释放图标和控件引用。
- 测试先行：悬停展开入口回归在修复前失败；最终 GUI 回归覆盖连续启用两项、取消、✓状态、Space、隐藏后的焦点、Esc、外部点击、失焦、重开、总开关、拖出取消，以及正/负坐标屏幕底角。
- 环境：项目 .venv/Scripts/python.exe，Windows Python 3.12.9 / Tk 8.6.15；Ruff 0.16.10；无依赖变更。
- 验证通过：按文件隔离 GUI 进程执行全部 238 项测试，160 项非 GUI、34 项算法配置、5 项完成动画、5 项截图菜单、34 项原 GUI 测试全部通过；变更 Python 文件 Ruff 和 git diff --check 通过；独立代码评审通过。
- 单进程验证：完整套件曾返回 236 passed / 2 errors、237 passed / 1 error，错误位于 Tk 根窗口初始化，包含无法读取 init.tcl、icons.tcl、entry.tcl 等启动文件；文件实际存在，失败项单独运行通过。内存加载基线 GUI 运行原 232 项测试通过。完整单进程重跑仍有初始化错误，尚未判定根因。
- 提交准备：首次 Auto Commit prepare 因当前记录缺少 HOST ownership 返回 unresolved_declared_ref。随后实际调用 task-lifecycle 的 updateTaskRecord，记录已写入，但 readAuthorizedTaskContext 抛出 TypeError: journal.findTaskRecordStates is not a function，未返回可消费的 ownership 回执。本任务按全局语义兜底授权执行精确 Git 提交和真实 Git 读回。
- 状态：请求的菜单行为、逐项回归、全部测试分进程执行和独立评审完成；本记录随本次精确提交保存，提交与远端状态由 Git 实际读回确认。

## 遗留

- 需要优化 Rust 或 TypeScript 代码：task-lifecycle 与 auto-commit 的 OperationJournal 接口不一致，readAuthorizedTaskContext 调用缺失的 findTaskRecordStates；影响本任务的 TaskRecordRef 读回及 Auto Commit candidate 准备。已保留实际错误，采用当前五个任务文件的精确人工提交兜底；本任务不扩大至全局 Runtime 仓库写入。
- 本机单进程多 Tk 解释器初始化稳定性尚未定位。原 GUI 文件独立进程通过，全部测试按 GUI 文件隔离进程通过；建议后续专项核查 Tcl/Tk 的解释器与文件读取生命周期。本任务未修改本机 Tcl/Tk 安装及全局 Runtime。
