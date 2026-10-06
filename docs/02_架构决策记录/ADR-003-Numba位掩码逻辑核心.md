# ADR-003: Numba位掩码核心与按需差分

## 状态与来源

已接受 — 2026-10-06修订。用户已确认完整联合方案并授权发布；批准见[发布批准](../01_sprint记录/sprint01/00-联合方案决策/2026-10-06/发布批准记录.md)。本ADR描述已批准目标，代码迁移及运行验证由承接Issue后续执行。共同规格见[联合方案](../01_sprint记录/sprint01/00-联合方案决策/2026-10-06/联合方案决策.md)。

## 背景

十种技巧和候选传播已经进入Numba nopython，`_masks`是唯一热路径状态。当前自动每次尝试技巧前从掩码转为81格Python set，再冻结候选；失败尝试也付出转换。重组能力时应继续用已有表示计算实际差异，而不是扩大快照或提示事实产生范围。

## 决策

1. `shudu/sudoku_njit_core.py`原位保留基础候选、传播与全部十种finder；Hidden Triple保持Naked Triple之后、现有判定及默认不勾选。
2. 共享Python编排位于`shudu/logic_solver/_engine.py`，项目优先级及兼容方法位于`_project.py`；公共入口遵循ADR-002。
3. 候选热状态继续是9×9 int64位掩码；Python集合只在当前确实请求的结果、兼容读出、日志和Hint快照位置生成。
4. 自动一轮尝试开始时最多复制一份mask；首个成功技巧后由`_diff.py`的`@njit(cache=True)` helper扫描81格及数字位得到真实删除，包括落子传播。失败技巧之间不物化Python候选网格。
5. 固定点只扫描显式已选集合，成功后回到最高优先级；收集本轮首次出现的真实删除，最终完整notes仅在生产自动结果路径生成一次。元数据兼容方法继续只返回原来需要的结果。
6. 项目Hidden Single→Naked Single、legacy Naked Single→Hidden Single维持；共享finder代码与调用次数不增加。
7. 单步证据采集只在next_step动态期启用，自动与legacy路径不为统一返回而创建完整LogicStep或单步候选快照。
8. rules.candidate_grid继续复用同一基础位掩码计算；自动关闭的基础笔记、Hint的现有notes投影和回溯fallback各沿原能力范围执行。
9. 新数值差分优先njit，NumPy承担既有数组组织；文案和资源操作仍在Python。当前业务不引入DataFrame计算。

## 取舍与影响

以整数差分替代原自动Python集合差分，业务输入范围相同。新的helper按自动成功场景请求调用，不在公共入口预编译；首次实际调用仍有Numba编译成本，因此本方案不承诺耗时加速百分比。保留cache=True的已有本地复用机制。

固定点完整结果和Hint一步事实分开，使结果收敛不制造额外全量投影。候选所有权、内核和编排各有唯一真源，控制流仍是当前同步9×9逻辑。

## 验证与生效

全部十种finder和新差分必须有实际nopython签名；差分保留原真实删除/次序保障；项目与legacy顺序、只选集合、失败尝试零Python候选转换、metadata零最终notes与单步采集均由本票实际回归证明。本修订已获明确发布批准，完成PublicIoGovernance校验及实际文本readback；实施与required运行证据由承接Issue后续取得。