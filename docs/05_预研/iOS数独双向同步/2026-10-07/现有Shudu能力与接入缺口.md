# Shudu 现有能力与 iOS 接入缺口

调查日期：2026-10-07。范围为当前源码、测试定义及已接受 ADR；本次采用只读调查证据，未执行测试、GUI 或设备命令。本文记录现状，外部状态接入的范围与新接口由后续业务决定。

Shudu 已具备独立于 GUI 的题面解析、逻辑求解、笔记和游戏状态能力。现有能力可以承担电脑端计算；实际 iOS App 的观察、点击及状态同步仍需验证。

## 可复用能力

- 手动填数通过 `Game.select(row,col)` 后 `enter(digit)`；`toggle_notes()` 切换笔记，重复输入取消该候选，`erase()` 和 `undo()` 支持擦除与撤销。领域坐标为从 0 开始的 `(行,列)`。[源码：sudoku_game.py:132、163、175、302、313](../../../../shudu/sudoku_game.py#L132)
- 指定算法使用公共 `solve_auto(board,names,proven_eliminations)`，按传入集合推进到固定点，返回完整 `board`、`notes`、落子数量及删除候选。它消费正式棋盘与已证明删除；手工笔记属于另一种状态。[公开入口:39](../../../../shudu/logic_solver/__init__.py#L39)、[结果合同:38](../../../../shudu/logic_solver/_results.py#L38)。Game 配置 setter 只修改配置，显式自动命令或正确手动落子才触发求解。[Game:209、222、260](../../../../shudu/sudoku_game.py#L209)
- `Game.auto_notes()` 在自动关闭时生成基础候选；开启且已选择技巧时执行自动求解并同步笔记，可能填写大数字。[Game:351](../../../../shudu/sudoku_game.py#L351)
- `next_hint_step(board,notes)` 返回第一步 `LogicStep`：技巧、填数/删除动作、来源格、单位、候选快照。动作是 `(row,col,digit)` 三元组。非空笔记逐格投影到候选，其余空格保留基础候选；Hint 使用全部十种技巧，独立于自动偏好，提示本身只读。[入口:16](../../../../shudu/logic_solver/__init__.py#L16)、[投影:7](../../../../shudu/logic_solver/_single.py#L7)、[动作合同:16](../../../../shudu/logic_solver/_results.py#L16)
- `Puzzle` 和 `puzzle_from_text()` 可接收外部九行题面。[sudoku_puzzles.py:11、53](../../../../shudu/sudoku_puzzles.py#L11)

## 截图与状态边界

`load_screenshot_game(path)` 可在脚本中直接调用，依赖 OpenCV/NumPy，返回 `ScreenshotGameInput(puzzle,notes)`；`note_map()` 转为候选字典。正式大数字按模板识别，小数字按单格 3×3 槽位解释。[sudoku_screenshot.py:32、43、192](../../../../shudu/sudoku_screenshot.py#L32)

全部大数字合入 Puzzle，Game 构造时全部成为 `givens`，因此当前导入无法区分 iOS 原始线索与玩家已填数字。`givens` 为不可变副本，`board` 为可变当前值，`notes` 为 `dict[(row,col),set[int]]`。[Game:57–69](../../../../shudu/sudoku_game.py#L57)

截图入口通过 `Puzzle.grid()` 校验形状与字符；Game 初始化还调用共享回溯取得答案。题面有效性与设备落子成功属于两个验证环节。若玩家已填数字有误，整张截图构造 Game 可能在答案加载时失败，无法据此证明已恢复可纠错的进行中棋局。[Game:31](../../../../shudu/sudoku_game.py#L31)

截图内部定位棋盘后裁剪并缩放为 900×900；公开结果只含 Puzzle 与 notes，没有原图棋盘边界、格子点击坐标或逐格置信度。领域坐标不能直接作为 iOS 屏幕坐标。[截图定位:67](../../../../shudu/sudoku_screenshot.py#L67)

Game 以 `Snapshot` 保存内存撤销状态，未见完整棋局落盘/恢复或外部同步事件接口。`UserSettingsStore.load/save` 只持久化自动偏好。设备动作是否成功及操作后的真实状态，目前没有对应公开入口。[Snapshot:40、169、313](../../../../shudu/sudoku_game.py#L40)、[UserSettings:25、58](../../../../shudu/user_settings.py#L25)

## 已接受 ADR 约束

- [ADR-001:18](../../../../docs/02_架构决策记录/ADR-001-共享回溯兜底求解器.md#L18)：复用共享回溯求解器。
- [ADR-002:13–22](../../../../docs/02_架构决策记录/ADR-002-共享规则内核与求解器公共接口.md#L13)：能力按需调用，Hint 基于现有笔记，自动只消费正式棋盘与已证明删除。
- [ADR-003:13–20](../../../../docs/02_架构决策记录/ADR-003-Numba位掩码逻辑核心.md#L13)：保持位掩码内核和候选转换执行面。
- [ADR-004:19–42、92–96](../../../../docs/02_架构决策记录/ADR-004-截图输入深模块.md#L19)：截图公开合同为 Puzzle+notes，识别知识归模块内部；字体与 3×3 笔记布局有适用边界。
- [ADR-005:14–20](../../../../docs/02_架构决策记录/ADR-005-本地自动算法偏好与完成动画.md#L14)：配置操作零求解，偏好存储生命周期归 GUI。

ADR-002 的新增 IO/子进程/远端调用为零，描述当次架构优化范围；未来设备能力的执行面需另行确定。

## 验证依据与未知

[截图测试:76、93](../../../../tests/test_sudoku_screenshot.py#L76) 使用合成截图，并验证大数字成为 given；[自动结果测试:48、182](../../../../tests/test_auto_result.py#L48) 定义结果与门禁；[Hint 测试:145、200](../../../../tests/test_sudoku_hints.py#L145) 定义现有笔记和单步调用；[架构测试:211、242](../../../../tests/test_architecture.py#L211) 定义截图与设置 IO 的依赖边界。这些是测试定义，不代表本次运行通过。目标 iOS App 的字体、颜色、笔记布局及真实操作效果仍待设备证据。
