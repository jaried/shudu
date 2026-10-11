# Windows 字体与 DPI 核验

日期：2026-10-12。承接[界面文字跨平台清晰度与字符完整性修复路线](../../../../.scratch/font-rendering/map.md)与 S1-09。本文保存核验结果与来源；原始工具输出由会话保管。

## 结论

本机 Windows 的系统字体可满足已检查的文字样本，并已开启 ClearType。两个独立 Python/Tk 运行时均复现了同一问题：把 `TkDefaultFont` 用作 family 得到宋体，正确使用 named font 得到微软雅黑 UI。当前应用首选中文与数字字体均可见，因此本机普通 View 路径具备首选字体，Linux 的回退结果不能直接用于解释 Windows。

项目 `.venv/Scripts/python.exe` 缺失。本轮只运行隐藏 Tk 探针，分别核对已有 Anaconda 和 uv 解释器；项目实际进程、页面观感及高 DPI 效果仍待验证。用户确认原乱码发生在 Linux，具体页面与字符尚待定位。

## 运行环境与验证边界

| 核验对象 | 实际结果 |
| --- | --- |
| Windows | 10.0.19045；一块 2560×1440 显示器；显示缩放 100% |
| 系统字体平滑 | 已开启，类型为 ClearType |
| Anaconda 独立解释器 | `D:\anaconda3\envs\base_python3.12\python.exe`；CPython 3.12.9；Tcl/Tk 8.6.14；DLL 来自该环境的 `Library/bin` |
| uv 已安装独立解释器 | `C:\Users\Tony\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe`；CPython 3.12.9；Tcl/Tk 8.6.12；DLL 来自该解释器的 `DLLs` |
| 两次 Tk 探针 | 均成功退出，窗口系统为 `win32`；创建 Tk 前后 process/thread DPI awareness 均为 unaware |
| 当前 DPI | 窗口 DPI 为 96；Tk `winfo_fpixels('1i')` 约 96.05；`tk scaling` 约 1.334 |
| 项目环境 | `pyvenv.cfg` 指向上述 Anaconda 环境，但缺少 Windows `python.exe`；未运行项目 GUI |

两个独立解释器的结果分别记录。当前显示缩放为 100%，没有验证 125%、150%、200% 或不同 DPI 显示器切换。Microsoft 文档说明，DPI unaware 窗口在高于 96 DPI 的显示缩放下可能被系统整体放大；声明 DPI awareness 后仍需正确处理尺寸变化。[Windows 高 DPI 模式与窗口缩放](https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows)

## 字体选择与字符覆盖

| 检查项 | 结果 |
| --- | --- |
| 系统 named font | 两运行时的 `TkDefaultFont`、`TkTextFont`、`TkMenuFont` 均为 `Microsoft YaHei UI`、9 点 |
| 当前 View 首选字体 | `Microsoft YaHei UI` 和 `Segoe UI Light` 均在 Tk family 集合中 |
| 错误 family 请求 | `family='TkDefaultFont', size=-28` 实际为宋体、21 点；直接 Tcl 元组查询得到同一结果 |
| 正确 named font | 读取或复制 named font 后修改尺寸，实际 family 保持 `Microsoft YaHei UI` |
| family 名称 | 部分中文字体枚举为本地化名称；英文名未被枚举与字体未安装是不同事实。例如直接请求 `Microsoft YaHei` 可解析为微软雅黑 |
| `▶` | 微软雅黑 UI 与 Segoe UI Light 经 Tk 回退到 `Lucida Sans Unicode`；Anaconda 探针的 GDI 字形查询也确认该回退字体提供此字符 |
| 中文 | 微软雅黑 UI 直接绘制已查中文；Segoe UI Light 对已查中文回退到 MiSans |

Anaconda 探针检查了从当前文案选取的 137 个去重字符，包含中文、数字、英文、全角标点与 `▶…·–“”‘’`。该样本及逐字符回退结果支持已检查字符的覆盖情况，完整可达 UI 与真实字形仍需按正式 AC 验证。非零字形度量和字体名称不替代人眼观感。

错误 family 与正确 named font 副本在 18、28、36、72 像素请求下得到不同的行距，说明修正字体选择后需要重新检查布局。Python 官方 Interface 提供 `nametofont()`、`Font.copy()` 和实际属性查询；正字号表示点，负字号表示像素。[Python 字体描述、named font 与尺寸](https://docs.python.org/3.12/library/tkinter.font.html)

## 当前调用面与后续验证

- `shudu/sudoku_view.py` 的 `choose_font()` 按 family 精确名称选择，缺少候选时返回 `TkDefaultFont`；Canvas 随窗口大小重新计算负像素字号并重建文字。
- `shudu/sudoku_hint_view.py` 的长提示通过 `tk.Text` 使用 View 中文 family 与负像素字号；短提示与数字复用 View 绘制。
- `sudoku_gui.py` 的关卡菜单及设置弹层使用 View 中文 family、11 点；设置菜单公共入口和内部默认值为 `('TkDefaultFont', 11)`，省略参数的现有菜单测试会经过该默认值。
- 当前生产 Python 源码未发现 DPI awareness 初始化调用；启动器和 executable manifest 的行为尚未核验。

验证应分别覆盖棋盘正式数字、候选笔记、按钮、菜单、长提示和错误弹窗。先恢复可运行的 Windows 项目环境，再比较正常、放大、最大化与连续缩放后的实际文字、对齐、裁切和输入交互；Linux 另行核验实际 Tk 后端和原乱码位置。支持范围及正式验收组合由后续原型和验收决策确定。

本轮完成只读源码与宿主核验。探针未修改依赖、系统缩放、生产代码或正式 ADR，结果不构成 S1-09 修复完成或验收通过。
