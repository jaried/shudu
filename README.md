# shudu · 数独

本地 Python/Tkinter 数独桌面游戏。支持截图导入、候选笔记、只读逻辑提示、逐项自动算法和 Numba 加速逻辑核心。

## 启动

```bash
uv sync
uv run python sudoku_gui.py
```

Windows 也可以运行 `run_gui.bat`。项目要求 Python 3.12 或更高版本，GUI 环境需要 `tkinter`。

可以直接把游戏截图作为启动输入：

```bash
uv run python sudoku_gui.py "D:\\screenshots\\sudoku.png"
```

运行中也可以从左上角关卡菜单或设置菜单选择 **“从截图导入…”**，同一个窗口可反复导入不同截图。

## 截图导入

`shudu/sudoku_screenshot.py` 是截图输入的深 Module，只暴露“截图路径 → Puzzle + notes”的主要 Interface。内部负责：

- 定位 9×9 棋盘；
- 区分正式大数字与候选小数字；
- 正式大数字做本地模板识别；
- 候选小数字按格内 3×3 位置恢复为 1–9；
- 支持深色高亮格中的浅色正式数字；
- 支持中文文件路径；
- 识别失败明确报错，不静默猜题。

GUI 不接触 OpenCV 阈值、模板或单格识别细节。

## 自动算法

设置 → **自动解决算法** 中，每种算法可以独立勾选：

| 算法 | 默认 |
| --- | --- |
| Hidden Single | ✅ |
| Naked Single | ✅ |
| Naked Pair | ✅ |
| Hidden Pair | ⬜ |
| Naked Triple | ✅ |
| Pointing Pair | ✅ |
| Box-Line Reduction | ⬜ |
| X-Wing | ⬜ |
| XY-Wing | ⬜ |

所有已勾选算法按固定优先级反复执行，直到当前集合全部无法继续。算法候选与用户手工笔记是两份独立状态；自动算法不会把用户手工笔记当作推理前提。

自动算法开启时，同时用 solver 的最终候选状态维护小数字，因此 Naked Pair、Naked Triple、Pointing、X-Wing 等产生的候选删除会直接同步到界面笔记。

自动算法勾选状态会通过 `shudu/user_settings.py` 原子保存到本地配置文件；下一次启动时恢复上次的完整勾选集合。Windows 使用 `%APPDATA%/shudu/settings.json`，其他平台使用对应的用户配置目录。游戏进度仍然不持久化。

## 行、列、宫完成动画

当一次游戏操作让某一行、列或 3×3 宫从“未完成”变为“全部正确完成”时，棋盘会播放参考视频风格的青色扫光：

- 行从左向右扫过；
- 列从上向下扫过；
- 宫按左上到右下的对角波纹扫过；
- 同一步同时完成多个区域时一起播放；
- 当前选中格保留原选中色，动画只改变临时绘制状态；
- 动画不会写入 Game，也不会影响撤回、错误次数或求解状态。

## 提示

点击「提示」或按 `H` 只展示一步，不自动修改棋盘或笔记。

统一提示效果：

- 无关区域压暗；
- 观察的行、列、宫亮起并用蓝框标识；
- 算法依据格用绿色显示；
- 待删除候选用红色和删除线显示；
- 待填入目标格突出显示；
- 下方显示“观察哪里 → 为什么成立 → 可以做什么”的说明；
- 点击任意位置或按 `Esc / 空格 / Enter` 返回。

`ShuduSolver.next_step()` 直接返回 `LogicStep`，其中包含：

- `placements`；
- `eliminations`；
- `sources`；
- `units`；
- 动作前候选快照。

因此 `shudu/sudoku_hints.py` 不再重新扫描候选来识别 Naked Pair、Pointing、X-Wing、XY-Wing 等模式，只负责把 solver 已确定的事实转换成提示文案和视觉语义。

## 常用操作

| 操作 | 行为 |
| --- | --- |
| `1–9` | 正式填数或切换笔记 |
| `N` | 切换笔记模式 |
| `A` | 自动笔记；自动算法开启时使用最终算法候选 |
| `H` | 只读一步提示 |
| `Delete / Backspace / 0` | 擦除 |
| `Ctrl+Z` | 撤回 |
| 方向键 | 移动选中格 |
| 空格 / `Esc` | 暂停/继续；提示中返回 |

挑战完成后保留完整棋盘，不用完成遮罩替换界面。

## 代码结构

仓库根目录只保留可执行入口：

```text
sudoku_gui.py       GUI 入口
shudu_solver.py     项目级逻辑 solver seam / CLI
logical_solver.py   legacy 逻辑入口 / CLI
solver.py           回溯演示入口
techniques.py       技巧演示入口
```

非入口实现统一位于 `shudu/`：

| Module | 职责 |
| --- | --- |
| `shudu/auto_techniques.py` | 自动算法目录、顺序、标签与默认配置真源 |
| `shudu/user_settings.py` | 本地用户偏好路径、校验与原子持久化深 Module |
| `shudu/sudoku_njit_core.py` | Numba 位掩码计算核心和 9 种逻辑 finder |
| `shudu/sudoku_rules.py` | 行、列、宫、peer 和基础候选真源 |
| `shudu/sudoku_backtracking.py` | 公共完整解/校验能力 |
| `shudu/sudoku_logic.py` | solver 状态、技巧编排、日志与算法证据 |
| `shudu/sudoku_step.py` | 不可变 `LogicStep` Interface |
| `shudu/sudoku_hints.py` | `LogicStep → Hint` 语义适配 |
| `shudu/sudoku_game.py` | 游戏状态、笔记、撤回、计时和自动算法 |
| `shudu/sudoku_screenshot.py` | 截图输入深 Module |
| `shudu/sudoku_view.py` | 普通游戏绘制、完成扫光动画和共用绘制 Interface |
| `shudu/sudoku_hint_view.py` | 统一提示效果绘制 |
| `shudu/sudoku_theme.py` | 主题和尺寸常量 |
| `shudu/sudoku_puzzles.py` | 内置题面和自定义题面 |

核心依赖方向：

```text
sudoku_njit_core / sudoku_rules
            ↓
      sudoku_logic
            ↓
      shudu_solver
            ↓
       LogicStep
            ↓
      sudoku_hints
            ↓
          Game
            ↓
      View / GUI
```

截图输入是独立支线：

```text
sudoku_screenshot → Puzzle + notes → GUI/Game
```

详细结构审查见 [`docs/codebase-design-review.md`](docs/codebase-design-review.md)。架构决策见 [`docs/02_架构决策记录/`](docs/02_架构决策记录/)。

## 测试

```bash
uv sync
uv run python -m pytest -q
```

完整 GUI 测试使用 Tk + Xvfb：

```bash
xvfb-run -a -s "-screen 0 1400x1200x24" uv run python -m pytest -q
```

GitHub Actions 在 Python 3.12 下执行完整回归，并包含架构依赖、Numba nopython、GUI、截图导入和提示行为门禁。
