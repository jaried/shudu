# ADR-NEW-TEXT: 文字角色与系统字体能力

状态：drafted / approval_draft，待完整方案批准。日期：2026-10-12。语义 owner：architecture-design。source_issue=S1-09；source_stage=solution-decision；action=create；target_scope=project；target_adr=ADR-NEW-TEXT（新增占位）；executor=architecture-design；request_id=S1-09-20261012-text-fonts-draft；approval_locator 为空。

关联设计：[联合方案草案](../00-联合方案决策/2026-10-12/界面文字联合方案决策草案.md)；Issue 切片 TXT-D01。已核验 issue_dir 为真实仓库内 `docs/01_Sprint记录/sprint01/S1-09`；本文件为唯一此主题 draft_path。正式编号由批准后 fresh-read ADR 注册表确定，本轮不创建正式 ADR 文件。

## 背景与依据

当前 View 角色选择、Hint Text、GUI 菜单与 settings_menu 默认字体共享呈现知识，但分散持有 family 名单/默认值。当前 TkDefaultFont 回退进入 family 元组，Windows/Linux 研究均显示它与合法 named font 的实际 family 不同。用户已确定原生 Tk、系统字体、首选缺失显示名称并继续游戏。既有 ADR-002 的 Hint→View 与 ADR-005 的增量设置/消息约束要求环境提示有独立呈现 owner。

新增 ADR 的理由是确立长期文字角色知识、公开能力、资源与执行边界；该决定独立于 Windows 的进程显示初始化。既有 ADR-001～005 的业务、求解、截图和偏好 owner 继续成立。

主源：[Tk 字体描述、family/named font 和正负字号](https://raw.githubusercontent.com/tcltk/tk/core-8-6-14/doc/font.n)、[Python tkinter.font](https://docs.python.org/3.14/library/tkinter.font.html)、[Tk Xft 逐字符回退](https://raw.githubusercontent.com/tcltk/tk/core-8-6-14/unix/tkUnixRFont.c)。文档支持接口合法性，实际字形与清晰度由项目宿主回归决定。

## 决策草案

1. 允许呈现层 TextFonts 独占 ui/number 的平台候选、实际 family、首选缺失状态。`shudu/text_fonts/` 单目录，`__init__.py` 唯一公开入口，`_selection.py` 与 `_specs.py` 隐藏匹配/默认解析。调用方只请求角色、原有 signed_size 与 normal/bold。
2. 允许公开 TextFonts.spec、只读 missing_preferred 和 standalone system_font；每 Window 的 View 拥有唯一 TextFonts，生命周期随 root，初始化 family 枚举一次，逐帧/计时/设置枚举 0。
3. 允许按平台候选闭集匹配实际 Tk family；缺失首选显示确切名称。系统 fallback 解析 TkDefaultFont 的实际 family 后构造元组；Canvas/Hint 负像素与菜单 +11 点单位保持原行为。Tk 继续负责逐字符回退。
4. 允许 Window 在最终 Q3 选择的独立控件中显示缺失信息。推荐主窗口可关闭非模态提示条；不借用 Game.message、不获取 grab、不新增持久化和业务计算；真实几何变化走原 Configure 绘制。
5. 允许 standalone open_settings 在默认 font 缺省时一次解析系统 named font family，保持零 family 枚举；显式 font 路径保持零查询。Popup 只消费入口已解析的值。
6. 允许 TXT-D01 在全部调用者迁移、新测试通过后物理删除旧 choose_font、旧角色直接消费者/分散候选与错误默认元组；以实际引用闭包为完成判据。
7. 允许资格工具与测试执行逐字符 actual/measure 和真实画面核验；生产字体能力的范围仅为两角色选择与原控件渲染，不增加字体文件 IO、扫描、注册、网络或探测子进程，不进入 Game/solver/Store/OCR。

候选顺序、合法参数、提示生命周期与测试矩阵由联合方案及 TXT-D01 精确规定，批准后成为 canonical 同一内容，调用方不自行扩大能力。

## 结果、迁移与测试

调用方依赖由 family 选择/回退知识缩为 role/size/weight；能力内部保留必要 Tk 复杂度。选择 Python 直接使用当前 Tk 宿主，不引入 Rust FFI 或 TypeScript 进程链。migration_status=migrate_now，实施动作在方案批准之后。

测试通过公开 TextFonts、View/Hint/Menu 和 Window 的行为验证合法字体、缺失继续、原尺寸、资源、枚举预算、原设置/消息/计时执行面。原 resize Text 重建、命中、只读滚动、截图/完成/偏好等断言保留；无旧字体专项时先补旧错误路径基线。TXT-D04 取得两平台清晰度与原乱码实际画面，不能凭 role 字符串判定完成。

本轮只产草案；Q3 非推荐选择先一致改写控件/生命周期/测试再批准。用户批准本主题及完整方案后，由 architecture-design 以 approval_final 发布正式 ADR，并把编号写回新票与来源 S1-09。
