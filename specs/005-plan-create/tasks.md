# Tasks: 创建自己的学习计划

**Input**: [已确认规范](spec.md)、[技术计划](plan.md)、[调研](research.md)、[数据模型](data-model.md)、[请求契约](contracts/web.md)、[未来验收指南](quickstart.md)。

**状态**：2026-10-14 完成任务设计；以下 8 项均未实施。真实 Git 分支为 feat/005-plan-create，活动规范为 specs/005-plan-create。

**分工**：Agent 执行代码、Git、环境准备与检查；用户决定需求、反馈理解、在浏览器实际验收。每次只推进指定任务。预计实现任务一课约 60–90 分钟，综合验收与交付可分多课，不能为赶课跳过检查。

**测试依据**：既定项目路线和 constitution 要求关键行为测试及真实 CI；测试融入相关任务，不另设重复测试任务，不要求用户执行命令。生成清单不代表任何检查已通过。

## Phase 1：Setup — 建立业务数据结构

- [ ] T001 在 core/models.py 定义 LearningPlan，生成 core/migrations/0001_initial.py，并在 core/tests/test_learning_plans.py 验证结构、关系、独立身份和排序。

  前置：确认 spec/plan 与本机活动规范一致，工作区修改属于本任务；现有账号模型和迁移机制可复用，无须重新初始化项目或增加依赖。

  按 data-model 原文落实约束：owner「必填；由服务端设置」；title「必填；标题无唯一约束；创建输入去首尾空白后为 1–100 字符」；description「选填、数据库非 NULL；空输入保存 ""；创建输入去首尾空白后最多 1000 字符，内部空格/换行保留」；target_date「选填；空输入为 None；创建时不能早于提交时北京时间当天」；created_at「服务端生成，用户不填写或修改，用于新建在前」。创建输入的去空白/动态日期校验属于 T002，不写到全局 save/日期约束。

  类型固定为 BigAutoField 主键、owner 外键（settings.AUTH_USER_MODEL/CASCADE/learning_plans）、CharField(max_length=100)、TextField(blank=True,max_length=1000,validators=[MaxLengthValidator(1000)])、DateField(blank=True,null=True)、DateTimeField(auto_now_add=True)。Meta 默认排序 -created_at/-pk；迁移有 swappable_dependency；不加状态、进度、唯一标题或额外索引。

  结果/验收：迁移文件存在，临时测试数据库可建表；full_clean 的长度边界、空值、同名不同主键、相同创建时间的稳定排序和账号关系符合设计。显式说明普通 save 不自动 full_clean，输入规则尚待表单。

  Agent 生成迁移并运行相关测试/迁移一致性检查，只使用临时测试库；**不对原本地 SQLite 执行 migrate，不接通页面，不改生产**。用户无需浏览器验收，可选练习：解释「两份同名计划为什么不是同一份」。课程记录写入 docs/LEARNING_LOG.md。

## Phase 2：Foundational — 创建输入的统一校验

- [ ] T002 在 core/forms.py 增加 LearningPlanCreateForm，并在 core/tests/test_plan_forms.py 验证文本、日期和字段白名单。

  前置：T001 完成；原登录表单保留。

  结果：Meta.fields 仅 title/description/target_date；先 strip 再校验 title 1–100、description 0–1000，空说明为 ""，内部空格/换行保留；日期空值 None，当天/未来有效，过去/非法日期使用 spec 的精确中文提示。每次校验显式按 Asia/Shanghai 的提交日判断，不缓存今天、不在模型拒绝历史日期。

  验收：0/100/101、0/1000/1001、首尾空白加满额正文、仅空白说明、说明内部换行；空/当天/未来/过去/非法日期；北京时间午夜前后；页面打开后跨午夜以 POST 日校验。表单不暴露 owner/id/created_at，不因伪造额外字段改变模型归属。

  Agent 完成组件和测试；移除自动 maxlength 属性，日期为 ISO date 控件，中文标签/required 信息明确；HTML 表单 novalidate 在 T003 模板落实。本任务不新增路由或写原数据库。用户可选练习：判断「100 字正文加首尾空格」是否应通过。课程记录写入 docs/LEARNING_LOG.md。

## Phase 3：US1 — 保存并在工作台看到目标（P1）

**目标**：首次接通安全的创建、读取流程，不依赖任务、详情或编辑页。

**独立验收**：A 创建计划后回工作台，显示成功提示和新卡片；四种说明/日期组合、同名、新建顺序、取消、刷新和重登符合规范。必须同时具备 US3 的归属和登录边界。

- [ ] T003 [US1] 在 core/views.py、core/urls.py、core/templates/core/plan_create.html、core/templates/core/workspace.html 接通创建与本人卡片，在 core/tests/test_plan_views.py 验证正常 HTTP 流程。

  前置：T001/T002 完成。**先核对使用的是原本地 SQLite，再应用 core/migrations/0001_initial.py，确认原用户和会话保留，随后接通路由**；不创建新账号、不重置密码、不使用生产连接。

  结果：/plans/new/（core:plan-create）只接受 GET/POST，login_required/never_cache/CSRF 从第一版即生效。有效 POST 用新实例，owner=request.user，atomic 内保存，正常退出事务后才 messages.success 并 302 回工作台；无效输入返回绑定表单。明确数据库失败在 atomic 外捕获并显示「暂时无法保存，请稍后再试。」；不吞程序错误、不自动重试，错误诊断不输出异常对象或凭据，日志不记录用户提交内容。绑定表单和本人卡片仍按规范保留/展示输入并自动转义。

  工作台每次先按当前 owner 查询、再按 -created_at/-pk 展示，包含完整标题、非空说明、年月日或「未设置目标日期」；空状态为规范原文，保留用户名、退出及创建入口。成功消息在工作台消费。取消只返回，不提交；模板自动转义，表单 novalidate，不新增其他计划端点。

  验收：四种选填组合分别恰好插入一份；去空白内容与卡片一致；同名独立；新卡片在前（含相同时刻）；成功 POST→302→GET，刷新/重登不再插入；取消与 GET 不写入。已有目标日期以后变成过去仍能展示；看似 HTML 的输入作为文字。包含基础 A/B 过滤与伪造 owner 不生效检查，不能把权限等到 T004 才实现。

  Agent 实现并提供可操作的本地创建页；用户用 A 创建「Python 入门」查看卡片、再取消一次。浏览器反馈和本地迁移证据记入 docs/LEARNING_LOG.md；未收到反馈不写用户通过。

## Phase 4：US3 — 独立账号的完整边界（P1）

**目标**：对已内置的归属规则作完整验证，发现偏差则修复。

**独立验收**：两个独立会话各自创建/同名创建，A/B 只读本人；伪造请求、过期或退出均不能获得或写入他人内容。

- [ ] T004 [US3] 在 core/tests/test_plan_views.py 验证账号/会话/请求边界，按发现的问题修正 core/views.py、core/forms.py、core/urls.py 与 core/templates/core/plan_create.html。

  前置：T003 安全的基本流程已完成；不改变原 M1 登录目的地或固定七天期限。

  验收：A/B 独立和同名计划各自可见，A 伪造 B 的 owner/owner_id、旧 id、username 也只能新增 A 的独立计划，不能更新旧记录；匿名/过期/退出后 GET 和合法 POST 均先登录且无写入/个人数据，登录后仍回工作台。启用 enforce_csrf_checks 检查无效令牌 403、有效令牌正常；登录用户非 GET/POST 为 405，创建页/工作台禁止缓存。原 M1 会话/退出测试保持目的；只因空状态变更的文字断言可更新。

  Agent 完成安全验证和必要修复；用户在普通/隐私窗口各创建不同说明的同名目标，再切换账号核对。结果写入 specs/005-plan-create/acceptance.md 与 docs/LEARNING_LOG.md，不读取或输出他人的生产内容。

## Phase 5：US2 — 错误提示与可修改输入（P2）

**目标**：错误不保存、不报成功，用户能在原输入上修正。

**独立验收**：空标题、超长、过去或非法日期给精确中文提示，保留可恢复输入；修正后只新增一份。

- [ ] T005 [US2] 在 core/tests/test_plan_views.py、core/tests/test_plan_forms.py 补齐错误与回滚证据，按必要差异修正 core/forms.py、core/views.py、core/templates/core/plan_create.html。

  前置：T003/T004 完成；基础错误处理已存在，不能依赖本任务才阻止非法写入。

  验收：逐条核对 spec 的五类字段提示，HTTP 无效提交返回 200、无 INSERT、无成功消息、绑定文本及可识别日期保留；非法 date 控件不能显示原值时仍保留标题/说明及明确错误。浏览器可输入「100 字正文＋首尾空白」，服务器判断 strip 后长度，不被 raw maxlength 拦截。

  在隔离测试库**实际 INSERT 后**触发明确 DatabaseError，验证事务回滚、原记录数量不变、非字段提示和输入保留、没有成功消息/伪造卡片；用合适事务测试隔离而非仅在 save 前抛异常。连接中断导致提交结果未知与明确回滚分开记录，不承诺自动去重/自动重试。只读数据库异常不能伪装成本人的空工作台。

  Agent 完成测试、浏览器错误检查与修复；用户尝试空标题和过去日期，再修正成功。不得故意破坏原本地/生产数据库来演示故障。证据记入 specs/005-plan-create/acceptance.md 与 docs/LEARNING_LOG.md。

## Phase 6：Polish & Cross-Cutting — 手机、综合验收与交付

- [ ] T006 在 static/core/styles.css、core/templates/core/plan_create.html、core/templates/core/workspace.html 完成表单/卡片的窄屏布局和可访问提示。

  前置：T003–T005 完成。结果：label、错误关联、必填/选填说明可理解，核心控件便于触摸；完整长标题不截断，说明 pre-wrap 保留换行，长文本 overflow-wrap 不撑出手机页面；保留退出入口。

  Agent 实际检查 1440/390/320px 的正常/错误创建页、空/多卡片和长文本工作台；无横向溢出、核心控件至少 44px、无页面脚本错误。修改后重验相关行为，不加前端构建或业务功能。用户可反馈文案和使用感受；实际手机结论留 T007。证据写入 specs/005-plan-create/acceptance.md 与 docs/LEARNING_LOG.md。

- [ ] T007 对照 specs/005-plan-create/quickstart.md 完成综合检查、隔离真实进程重启及用户电脑/手机验收，汇总到 specs/005-plan-create/acceptance.md、docs/LEARNING_LOG.md。

  前置：T001–T006 完成。Agent 执行 Django check、makemigrations --check --dry-run、collectstatic、完整 core.tests；确认 .github/workflows/checks.yml 的两条 job 会发现新测试，不把本地 SQLite 或旧 CI 记成当前 PostgreSQL 通过。

  在忽略的 .tools/qa/ 中使用独立文件 SQLite/临时账号/自有临时服务，通过 HTTP 创建后正常停止并重启同一数据库的服务，核对内容/归属/数量；不停止原 8001、不打印密码或 Cookie。重新 Client/refresh_from_db 不算重启证据。

  用户在电脑和实际手机验收创建、错误修正、取消、同名、刷新/重登及 A/B 独立身份。Agent 按实时网络准备地址，记录每项 FR/SC 的自动、进程、浏览器、用户结果，未执行项保持待办；发现问题先修复并重验，再标完成。本任务可分检查课与反馈课。

- [ ] T008 围绕 specs/005-plan-create/acceptance.md、specs/005-plan-create/tasks.md、docs/LEARNING_LOG.md 和 docs/DEPLOYMENT.md 完成分支推送、关联 Issue #11 的 PR、真实 CI、独立 Agent 审查、修复与交付核对。

  前置：T007 的必需检查和用户验收完成。Agent 根据最终差异写 PR，读取实际 SQLite/PostgreSQL、迁移一致性与 Linux 正式请求结果；必要时完善 scripts/check_deployment.py 和 .github/workflows/checks.yml，不以配置存在推断运行通过。

  按既定路线安排另一位 Agent 只读审查，报告复现/影响；修复后按实际变化重验。核对审查、CI 与用户证据后按已授权交付操作完成 Squash merge、本地 main 同步。生产发布仍先核对现有配置/资源/版本与发布授权，记录实际 migrate、部署 commit 和公开请求结果，不创建生产测试账号或提前邀请用户。

  验收：PR/CI/审查/合并引用可追溯，本地 main 与远端一致；源码可用、已合并、已上线分别记载。代码回退保留新增表与数据，不执行删除表或逆向迁移。Issue 仅在完整交付条件完成后关闭，受外部条件限制的上线项明确保留。用户实际线上反馈不能用匿名自动检查替代。

## 依赖与执行顺序

```mermaid
flowchart LR
    T001[模型与迁移文件] --> T002[创建表单]
    T002 --> T003[US1 创建与本人卡片]
    T003 --> T004[US3 账号边界]
    T004 --> T005[US2 错误与回滚]
    T005 --> T006[手机布局]
    T006 --> T007[综合与用户验收]
    T007 --> T008[PR与交付]
```

US1/US3 同为 P1，先把安全归属内置进 US1，再完整验证 US3，最后验证 P2 的错误恢复。
三条故事共用同一创建接口和工作台，各有独立验收场景；它们不是三个可以任意跳过的部署版本。

### 并行机会与逐故事例子

本轮实现任务共用 core/forms.py、core/views.py 和 test_plan_views.py，或依赖前一结果，故**没有标记 [P] 的实施任务**。单个 Agent 按上图执行，不为并行拆出重复文件。

| 故事 | 可以同时准备的独立工作 | 必须等待的工作 |
|---|---|---|
| US1 | Agent 编写代码；用户在聊天准备「标题/说明/日期/预期卡片」例子 | 浏览器保存需等 T003 页面就绪 |
| US3 | Agent 验证伪造请求；用户准备 A/B 不同说明的同名例子 | 账号实际检查需使用已完成的页面 |
| US2 | Agent 验证错误/事务；用户选空标题和过去日期例子 | 真正错误修正验收需等修复完成 |

这些准备不占新增任务编号，也不要求新 Agent；不得一边验收旧页面一边修改同一路径并记为最终通过。

## 最小交付与增量策略

T001 的产物是可验证的数据结构；T002 是可验证输入；T003 是首次可在本地使用的创建与卡片。
**MVP 范围是 US1＋必需的 US3 归属/登录保护，以及基本 US2 校验**，不包含详情、编辑、删除、任务或注册。
完整功能交付仍须 T004–T008 的关键边界、实际验收和 PR，不能仅因正常创建成功就发布。
每任务保存小提交，课堂结束更新真实记录；本课结束后的第一步只做 T001。

## 规范覆盖索引

| 条件 | 对应任务与证据 |
|---|---|
| FR-001 | T003 创建入口、三个字段、创建/取消 |
| FR-002 / FR-004 | T001 结构，T002/T005 去空白和文本边界 |
| FR-003 | T002/T005 日期空值、北京时间与提交日边界 |
| FR-005 | T002/T005 精确提示、输入保留、无写入 |
| FR-006 / FR-007 | T001/T003 独立身份、归属、同名不覆盖 |
| FR-008 / FR-009 | T003 消息、卡片、排序、空状态、身份和退出 |
| FR-010 | T003 刷新/重登，T007 真实进程重启 |
| FR-011 / FR-012 | T003 基础保护，T004 完整账号/请求/会话边界 |
| FR-013 | T003 取消，T005 回滚与无伪造成功 |
| FR-014 | T003 转义，T005 错误，T006/T007 实机布局 |
| SC-001 | T003 四种选填组合与正确保存/展示 |
| SC-002 | T002/T005 所有输入边界与错误 |
| SC-003 | T003/T007 内容和数量的持久性证据 |
| SC-004 | T004 两账号、同名、伪造请求与未登录 |
| SC-005 | T006 Agent 窄屏，T007 用户实际电脑/手机 |

格式统计：共 8 项；Setup/Foundational 2 项，US1/US3/US2 各 1 项，综合阶段 3 项。
所有任务均为未勾选、有顺序 ID 和具体文件路径；故事任务带 [USn]，共享任务无故事标签。
