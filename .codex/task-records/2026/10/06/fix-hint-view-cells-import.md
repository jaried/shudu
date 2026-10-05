# 修复提示绘图的 CELLS 导入错误

- 日期：2026-10-06
- 用户请求：修复运行 `sudoku_gui.py` 时出现的 `ImportError: cannot import name 'CELLS' from 'shudu.sudoku_hints'`。
- 补充请求：运行所有测试并修复发现的问题。
- 模式：定位并修复现有启动行为。
- 写入范围：`shudu/sudoku_hint_view.py` 与本请求记录；提交按全局规则附带 `.codex/task-records/` 当前变化。
- 目录归属：`skills_mode=global_only`，`task_intent=use_skill_in_project`；代码与记录均写入真实仓库 `D:/Tony/Documents/invest2026/projects/shudu`。
- 基线：`main`，HEAD `58290f274eafe31eb7f0a646c6732e526752e012`；已有暂存记录 `solution-decision-s3-80-82.md` 保留原文。
- 复现：用户指定的 `base_python3.12` 导入 `shudu.sudoku_view` 失败；项目 `.venv` 执行 `pytest tests/test_sudoku_gui.py -q` 在加载 conftest 时因同一导入失败。
- 根因：提交 `eae0992` 移除了提示模块不再使用的 `CELLS` 导入，绘图模块仍依赖该间接导出。
- 修复：`Hint` 从提示模块导入，`CELLS` 直接从 ADR-002 规定的共享规则模块导入。
- 环境：`uv sync` 返回 0；项目解释器为 `.venv/Scripts/python.exe`，Windows Python 3.12.9。
- 已验证：GUI 与架构相关测试 49 项通过；用户原解释器执行入口 `--help` 返回 0；真实 Tk 窗口绘制、81 格提示和返回棋盘验证通过。
- 调用修正：首次隐藏窗口验证尚未触发 Configure 绘制，断言失败；改为主动调用公开 `view.draw()` 后通过，生产代码无需额外修改。
- 完整测试：`.venv/Scripts/python.exe -B -m pytest -q` 返回 0，200 项通过，耗时 13.59 秒；未出现失败或跳过。
- 静态检查限制：项目环境未安装 Ruff，执行 `python -m ruff check --no-cache shudu/sudoku_hint_view.py` 返回 1（`No module named ruff`）；`git diff --check` 通过。

## 遗留与提交处理

- 需要优化 Rust 或 TypeScript 代码：自动提交入口 prepare 返回 `control_plane_runtime_blob_mismatch`，报告 `skills/auto-commit/scripts/commit-task-files.ts` 与绑定 Git tip 的 snapshot blob 不一致。
- 影响：确定性提交入口未生成 candidate；自动 RemoteSync intent 未生成。
- 处理：保留全局 Runtime 的当前内容，在本仓库按同一授权文件集合手工等效提交，并核对提交 parent、消息、文件集合和工作树；本任务没有正式 Issue，遗留保存在当前请求记录中。
- 后续建议：在全局 Runtime 所属仓库单独核对源码、绑定 snapshot 与构建版本，再恢复确定性提交入口。
