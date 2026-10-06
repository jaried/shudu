# grilling 业务事实核验

日期：2026-10-06。来源为当前源码、测试源码和现行ADR；本次核验未修改生产代码，未新增运行通过结论。Git实际读回显示当前生产源码与原基线提交一致。

## 设置动作的执行范围

| 动作 | 当前事实 | 草案收敛 |
| --- | --- | --- |
| 自动求解总开关、技法选择 | `sudoku_gui.py:281-303`调用Game setter、两次completed_units、一次draw、空动画入口和_persist_auto_settings；已有store保存一次，None时返回 | setter和原消息保持；更新已有消息项至多一次；已有store一次保存；扫描/draw/动画/求解为0 |
| 正确填数后，清理关联笔记 | `sudoku_gui.py:306-307`只赋值Game.auto_clean；`shudu/user_settings.py:25-28,58-69`只持久化auto_solve/auto_techniques | 只修改内存与对应勾选标记；message更新、store访问、save、扫描、draw、动画、求解为0 |

## 提示与完成态的可达性

提示画面：`shudu/sudoku_hint_view.py:47-48`仅保留close-hint目标；`shudu/sudoku_view.py:417-421`任意Canvas点击先关闭提示；`sudoku_gui.py:106-108`仅接受close-hint。`tests/test_sudoku_gui.py`的`test_hint_click_any_canvas_position_closes_it`与`test_hint_shows_source_digits_and_correct_focus_box`保障当前行为。保持这项可达范围，关闭后通过正常画面打开设置。

直接调用已有设置函数可绕过用户动作入口。当前总开关/技法setter保持hint_preview，但`SudokuView.draw`销毁并重建提示控件；原提示不重新求解。优化后保留控件identity是新增资源保持保证，其测试沿直接函数路径验证，不把它描述为原先已有的保障。

完成态：页头仍提供设置目标；`shudu/sudoku_view.py:382-389`只显示完成文案和统计，当前设置消息已不可见；按钮只读。空新增完成集合在`animate_completed_units`直接返回，不取消或重启原动画。优化继续保持文案、按钮和动画进度，减少设置路径的扫描和重绘。

## 证据边界

上述结论由源码与既有测试定义直接支持。本次没有运行Hint/won设置组合事件；目标控件identity保持、自动清理零副作用和完成态切换的真实回归证据由A04后续实施取得。现有Tk全量错误仍未解决，原门禁保留。

这次纠正由“现有业务保持、实际执行面不扩大”与现场事实唯一确定，作为事实及推断展示项。用户整体理解确认仍待答；正式登记、ADR接受、canonical发布和实施仍沿后续明确授权。
