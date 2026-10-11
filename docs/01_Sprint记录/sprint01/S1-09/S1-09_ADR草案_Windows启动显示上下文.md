# ADR-NEW-DISPLAY: Windows启动显示上下文

状态：drafted / approval_draft，Q2 待裁决。日期：2026-10-12。语义 owner：architecture-design。source_issue=S1-09；source_stage=solution-decision；action=create；target_scope=project；target_adr=ADR-NEW-DISPLAY（新增占位）；executor=architecture-design；request_id=S1-09-20261012-window-display-draft；approval_locator 为空。

关联设计：[联合方案草案](../00-联合方案决策/2026-10-12/界面文字联合方案决策草案.md)；Issue 切片 TXT-D03。真实 issue_dir 是仓库内 `docs/01_Sprint记录/sprint01/S1-09`，本文件是此主题唯一 draft_path。标题主题与文件名逐字符一致；正式编号按批准后 ADR 注册表 fresh-read 分配。

## 背景与依据

Windows 历史探针为 DPI unaware、100%，当前生产 GUI 没有显式 DPI 初始化。Windows 整体拉伸与 Tk 字体按窗口尺寸重绘是不同执行面，用户要求的文字清晰度需要明确支持范围和启动顺序。

Windows 显示上下文是进程/GUI 启动能力，独立于文字 family 规则。既有设置菜单工作区、Canvas 命中、Hint Text 和截图错误弹窗继续属于原 owner。主源：[Microsoft DPI 支持范围](https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows)、[SetProcessDpiAwarenessContext 初始化顺序与结果](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setprocessdpiawarenesscontext)。实际宿主高 DPI 结果尚待取得。

## 决策草案：Q2 推荐分支

1. 允许 GUI.main 在首次 Tk 创建以及应用 DPI 查询之前，仅一次调用 `shudu.window_display.prepare()`；其他 CLI、solver、截图预处理与模块导入不调用该能力。
2. 允许 WindowsDisplay 作为能力级 Module，目录 `shudu/window_display/`，`__init__.py` 唯一公开入口，`_prepare.py` 持有一次执行/不可变结果，`_windows.py` 隐藏标准库 ctypes 系统调用。
3. 允许 prepare 返回公开不可变 DisplayState(status,awareness,diagnostic)。非 Windows 为 not_applicable、零 Win32 调用；Windows 请求 SYSTEM_AWARE 并读回实际状态。
4. 允许成功或既存 system-aware 为 ready；既存其他模式为 inherited；API 失败为 failed。保存真实错误，重复调用复用首次结果；初始化失败/继承不支持状态只输出一次启动诊断并保留原 Tk 启动行为，资格按实际状态判定。
5. 允许批准范围为 100/125/150/200% 启动显示比例、窗口尺寸调整、最大化/恢复与同 DPI 显示器移动；显示比例变更后重启验证。不同 DPI 动态跨屏只有用户选定并在批准前完整展开该范围后才能纳入。
6. 允许独立进程测试初始化顺序、幂等、继承/失败/非 Windows，并在真实项目进程/宿主核验四种比例下的字体、菜单、输入、工作区和弹窗。Linux 模拟工作区测试继续在适用 Linux 执行，不替代 Windows 证据。

系统调用不读写 Game、solver、Store、OCR、字体列表或控件资源；既有 Canvas/Text/菜单和设置执行面保留。该新增一次 OS 能力是本草案明确提交批准的范围，不作为重构任意扩展执行面的许可。

## 后果、错误与发布

Python ctypes 符合当前 Tk 宿主与一次 Win32 调用需求；Rust FFI/额外构建与 TypeScript 进程桥增加部署/执行面，当前无新计算热点。目标 Python，migration_status=migrate_now，方案批准后执行。

system-aware 不承诺不同 DPI 实时跨屏的同等清晰度。若 Q2 选择动态范围，先替换本草案为各窗口 DPI 生命周期、字体/尺寸/图片/命中/工作区/原生弹窗的完整合同和原子票，再取得最终批准；只设置 PMv2 不满足该范围。

测试失败保留真实状态，在批准范围修复并复跑全部 required 检查后 Delivery；不以 Legacy 或测试 skip 替代通过。用户完整批准本主题与联合方案后，由 architecture-design 执行 approval_final 正式发布，并写回来源/承接票的相关 ADR 编号。本轮正式 ADR 文件与历史 Issue 状态保持当前值。
