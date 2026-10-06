# Sprint01全量Issue编排

当前授权：S1-01、S1-02、S1-03、S1-04按已批准方案，经设计、实施、评审、合并和真实测试推进至待验收。
依赖：保持S1-01→S1-02/S1-03；S1-04独立。上游设计真实完成释放下游设计，上游待验收释放下游实施。
允许target：Sprint01现有根worktree与Skill要求的正式Issue worktree，主Agent/HOST负责跨Issue集成。
职责：每票一个Luna canonical Worker，设计/实施及整改复用；每阶段独立Reviewer，定向复核复用同Reviewer；Worker只负责本票。
调度：所有ready动作及时派发；DAG foreground只读每30秒检查，阶段完成事件即时续派；Leader健康检查300秒。关键路径Top3及依赖满足的未合并尖端更新最久Top3用于重点关注，其余正常调度。
Runtime恢复：保留真实错误、已有副作用和Legacy，按原合同语义执行到阶段完成；共享Skills/Runtime源码保持原状。
测试：所需门禁逐票真实通过；最小固定输入；位置/实现断言随Issue迁移且绑定ADR与本票方案设计；失败按批准保障定位、修复、真实复跑。
实际基线：两次全量237passed/1Tksetup error，隔离1pass仍保留全量失败；S1-04承接真实门禁修复。
已派发：/root/s1_01_worker、/root/s1_04_worker，当前solution-design；02/03等待01设计里程碑。
远端事实：origin git@github.com:jaried/shudu.git 当前读取退出1，Permission denied(publickey)，本地阶段继续，RemoteSync未验证。
原生Goal事实：get_goal返回null；公开cycle返回native_goal_context_required/ensure，现有公开DAG及HOST工具执行同授权阶段合同。
完成判据：四票required检查、独立评审、真实sourceTip进入Sprint、tracker均待验收及Git/readback；用户验收后续由acceptance owner完成。
