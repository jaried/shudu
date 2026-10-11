# Linux 回归测试

任务状态：回归检查与兼容性定位完成；遗留布局问题待修复。提交状态以实际 Git 对象与本文件状态读回为准。

授权范围：建立项目专用 .venv-linux，同步锁定依赖，运行当前工作树测试，记录结果，提交本任务摘要。源码、测试、依赖声明及 Windows .venv 保留现状。

步骤：
- completed：准备 Linux 环境；同步返回 0，解释器、Tk Menu/Text 与依赖导入验证通过。
- completed：完整回归；291 项用例执行完成，289 通过、2 失败、0 跳过，退出码 1，耗时 40.23 秒。
- completed：定位兼容问题；完成原生崩溃最小复现、运行时对比、高 DPI 菜单尺寸和多屏范围验证。
- completed：记录结果；本摘要已由 TaskLifecycle writer 写入并读回，当前提交范围限定为本文件；原始证据位于仓库外。

## Linux 环境与使用

项目 .venv-linux 使用 Python 3.12.15、Tk/Tcl 9.0.4、X11；解释器位于 /home/tony/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu，环境入口为 .venv-linux/bin/python。锁定依赖：numpy 2.5.3、numba 0.67.0、opencv-python-headless 4.14.0.94、pytest 9.1.1。原 Windows .venv 与当前用户未提交修改均保留；.venv-linux 由既有全局 Git 忽略规则覆盖。

后续同步：`UV_PROJECT_ENVIRONMENT=.venv-linux uv sync --locked --python 3.12.15 --link-mode=copy`。

启动：`.venv-linux/bin/python sudoku_gui.py`。

回归：`.venv-linux/bin/python -m pytest -q`。

同步复核 `uv sync --locked --check --python 3.12.15` 返回 0，报告环境无需变更。pyproject.toml 与 uv.lock 未改写。测试使用单独的 Numba 缓存与 pytest 临时目录，避免复用 Windows 缓存。

## 验证结果

完整回归覆盖架构、逻辑求解、Numba、截图输入、偏好保存、GUI 鼠标键盘、设置菜单与提示。Linux 当前没有 xvfb-run，使用真实 DISPLAY=:0 桌面执行，Tk 的 windowing system 为 x11。

失败用例均为 `tests/test_auto_technique_settings.py::test_algorithm_submenu_stays_inside_monitor_at_bottom_right`，参数 bounds0=(0,0,600,400)、bounds1=(-600,-400,0,0)。全量运行时向左越界 98 像素，定向复测向左越界 120 像素；两项独立复测均失败。

## 兼容性问题与建议

1. 旧 uv Python 3.12.9 / Tk 8.6.14 的 Linux 原生崩溃已通过更换运行时解决。创建标准库 tk.Menu 即复现 XCB 的 `!xcb_xlib_unknown_seq_number` 断言，退出码 134；提示中的 tk.Text 也触发同类中止。gdb 显示旧 Python 内静态 X11 与系统 libXcursor/libXrender/libX11 混用；预加载系统 libX11 及 XCURSOR_CORE=1 均未解决。Python 3.12.15 / Tk 9.0.4 的 Menu/Text 最小验证成功，完整套件也完成执行。上游对应问题：https://github.com/astral-sh/python-build-standalone/issues/503 。
2. 高 DPI 设置菜单布局仍有边界问题。旧 Tk 8.6.14 使用约 96 DPI，菜单 407×266；新 Tk 9.0.4 使用约 192 DPI，隔离场景菜单为 720×442，超过测试设定的 600×400 工作区。仅将新 Tk 的诊断进程缩放调为旧值后，菜单变为 411×288，可放入边界。代码 `_place()` 向左展开时减去子菜单宽度，缺少整个弹层的最终尺寸约束。后续修复应明确高 DPI、小工作区与子菜单的可见范围，并在实际缩放下回归；本次保持产品布局现状。
3. Linux 多显示器定位存在覆盖缺口。实际为两个 5120×2880 显示器；`monitor_bounds(root,5500,200)` 返回整个虚拟桌面 (0,0,10240,2880)，尚未返回所属单屏的工作区，也未扣除系统面板。现有边界测试替换了 monitor_bounds，未验证真实 Linux 单屏定位。后续应补齐实际显示器工作区能力及对应回归。

## 本地保留与工作流遗留

日志、XML、诊断脚本和 journal 保存在 /tmp/shudu-linux-regression-20261011-MqceDC，逻辑与真实路径相同，owner 为本任务；保留用于复查。完整结果为 full-31215.log/full-31215.xml。原始证据均未提交 Git。

本次创建的旧环境完整移至 /mnt/d/temp/shudu-linux-regression-20261011-MqceDC/venv-python3129，移动前目标不存在且与项目同一文件系统，无删除。其旧 Python 对比使用完整版本路径 /home/tony/.local/share/uv/python/cpython-3.12.9-linux-x86_64-gnu/bin/python3.12 及原 site-packages；minor 版本别名随 uv 安装更新，不作为旧运行时证据。

需要优化 TypeScript 代码：TaskLifecycle 的 createTaskRecord/updateTaskRecord 默认 sourceLocator 在 create/update 间变化，reader 同链校验报 ownership_ref_conflict；正文写入完成但返回失败。恢复使用同一任务绑定、独立 journal 和稳定 sourceLocator，经原 writer 完成写入与读回；原 journal 保留。工具源码保持原状。

工具限制：当前无 update_plan，步骤由请求记录维护；ponytail Skill 未找到。当前固定表达与证据 Skill、项目 ADR、codebase-design、python-runtime 与验证合同已执行。
