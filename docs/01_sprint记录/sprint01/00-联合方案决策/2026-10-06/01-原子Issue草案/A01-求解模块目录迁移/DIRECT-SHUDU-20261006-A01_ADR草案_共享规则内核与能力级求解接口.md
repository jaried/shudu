# ADR-002: 共享规则内核与能力级求解接口

## 状态与来源

批准前修订草案；现行ADR-002保持接受状态及原内容。本草案由architecture-design在approval_draft范围形成，承接A01，关联[联合方案](../../架构优化联合方案决策草案.md)及[本票](方案决策草案.md)。实际HOST请求见[ADR草案请求](ADR草案请求.json)，最终批准定位为空。

## 背景

拓扑、逻辑候选和算法证据已有唯一实现；根项目入口仍组装步骤事实，Game同时读取自动结果和可变solver。迁移到一个求解目录后，调用方可只请求当前业务需要的capability，内部实现仍共用既有状态与finder。

## 决策

1. `shudu/sudoku_rules.py`继续拥有拓扑、坐标和基础候选，保持纯领域规则。
2. `shudu/logic_solver/`是逻辑求解deep Module，一个公共入口`__init__.py`，engine、project、results、single、evidence、auto、diff为其internal知识划分。
3. Hint调用`next_hint_step(board, notes)`；Game在原自动gate后调用`solve_auto(board,names,proven_eliminations)`。两种能力分别执行，内部共享不改变调用范围。
4. 根`shudu_solver.py`继续是项目CLI/历史导入seam，其`ShuduSolver.next_step()`返回完整LogicStep并保持现有实例推进语义；根legacy入口保持其不同Single顺序和公开helpers。
5. LogicStep的动作、来源、单位、快照及明确技巧身份由执行算法的Module产生；Hint只适配中文和视觉语义。项目Hidden Single解释单位保持宫→行→列，来源在执行前计算。
6. Game.notes与算法候选分属不同owner：Hint只对既有非空notes的空格投影，其余空格保持基础候选；只请求一次next_step，找到第一步即返回。自动能力只消费正式棋盘和已证明删除。
7. Hint固定使用当前全部十种算法，不读自动偏好；自动能力只执行传入的勾选集合到固定点。
8. Hint View消费Hint并复用View公开绘制能力；Game门禁、撤回和状态应用保持Game所有权；规则/kernel不反向依赖这些调用方。
9. 根目录保留现有五个可执行入口；其他本次迁移实现归Module目录，直接引用与有效测试同步迁移。
10. 执行面以相同输入的实际调用和规模验证：错误提示/禁用自动零solver，提示一次单步，自动只选集合，候选转换和扫描不增加，产品新增IO/子进程/远端调用为零。

## 取舍与影响

保留有实际CLI和导入消费者的根入口Adapter；生产Game/Hint改依赖capability。原子A01只做目标态迁移，A02/A03分别使调用方依赖收缩，避免一票承担跨业务的统筹。现有Numba finder、共享规则、回溯、截图和store保持各自真源。

新的自动完整结果转交单一所有权，Hint步骤快照沿用不可变语义；类型入口统一不等于执行统一。每个capability按需导入其internal，无初始化solver或全部能力预热。

## 验证与生效

目录/依赖与公共产物检查、原项目/legacy优先级、输入只读、notes语义、完整自动结果、执行面计数均要求真实测试。新测试保障原行为后迁移相应位置断言。正式生效只由用户对完整方案及本修订的明确批准触发；由HOST取得批准、版本和readback后，architecture-design修订现行ADR。当前状态为草案。
