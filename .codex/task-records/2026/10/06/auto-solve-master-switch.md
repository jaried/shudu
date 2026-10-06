# 自动求解总开关

- 日期：2026-10-06。
- 请求：增加全局自动求解开关；开启时仅执行已勾选算法，关闭时即使全部勾选也停止自动求解。
- 范围：Game 自动执行入口、设置菜单、偏好存储与重启/截图继承、相关测试、README、ADR-005 和本记录。
- 目录：`skills_mode=global_only`，`task_intent=use_skill_in_project`；实际写入仓库为 `D:/Tony/Documents/invest2026/projects/shudu`，目标父目录无 junction 或 symlink。
- 基线：`main`，HEAD `a88de20c49d77683d38de6e1594fae27f7879c7d`；工作树与暂存区干净。
- 设计：总开关独立保留为 `auto_solve`，默认开启以兼容当前行为，与逐项算法勾选联合保存。切换只修改配置；统一通过 Game 自动入口控制实际执行。Hint 固定使用全算法及现有笔记；总开关关闭时自动笔记仍计算基础候选。
- ADR：沿用 ADR-002 的只读全算法提示和 ADR-005 的配置 owner，在后者补充总开关合同。
- 测试先行：新增验证首次执行为 5 项失败、1 项通过，确认缺少统一入口控制、总开关 setter 和偏好字段；关闭总开关时旧代码仍自动填写 R1C9。
- 环境：`uv sync` 成功；项目 `.venv/Scripts/python.exe`，Windows Python 3.12.9；复用项目 Ruff 0.16.10。
- 功能验证：完整 `python -m pytest -q` 返回 0，232 项通过，最终耗时 21.03 秒；覆盖总开关关闭后的显式自动执行、自动笔记、正确填数与旧入口，开启时按勾选集合执行，以及无勾选时保持盘面。
- 偏好与 GUI：真实 Tk 菜单显示总开关，切换保留所有算法选择并保存；后续改单个算法保留总开关 False；重开关卡、截图导入及两种启动方式都保留关闭状态。旧 JSON 缺少总开关时按 True 读取。
- 提示验证：关闭总开关前后的 Hint 相同，保留全算法和现有笔记契约。
- 静态检查：本次 7 个 Python 文件的 `ruff check --no-cache` 与 `git diff --check` 通过；限定范围内处理导入排序、类型标注来源和无效末尾 return，类型错误采用 TypeError，沿用既有损坏配置处理。
- 帮助说明：设置总开关、算法勾选、提示独立性和基础自动笔记均同步到操作说明与 README；最终入口 `python sudoku_gui.py --help` 成功。
- 独立评审：无阻塞项；六组独立内存断言通过，覆盖 solver 前置停止、实际 GUI 回调、重开、截图转换和两条启动分支；评审未修改文件或运行真实 GUI。
- 状态：实现、验证与独立评审完成，按精确集合本地提交；尚未进行用户验收。

## 提交遗留

- 需要优化 Rust 或 TypeScript 代码：本次 `auto-commit` prepare 返回 `control_plane_runtime_blob_mismatch`。全局 `skills/auto-commit/scripts/commit-task-files.ts` 绑定 blob 为 `dc273233374c2d18817951c264dfe9f5521240d0`，实际 blob 为 `d46ee666c552036a0071e4e1cf9b59e98846d0c6`。
- 影响：确定性入口未生成 candidate 和 RemoteSync intent；本次项目功能与验证已完成。
- 处理：在当前项目内按同一授权文件集合手工等效完成本地提交，读回 parent、消息、实际提交路径、暂存区和工作树；全局 Runtime 保持当前内容。本请求没有正式 Issue，真实错误保存在本任务记录中。
- 建议：在全局 Runtime 所属仓库核对绑定 snapshot、源码和构建版本，恢复确定性提交及 RemoteSync。
