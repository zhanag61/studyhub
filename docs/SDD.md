# SDD：先约定行为，再实现与验证

SDD 是规范驱动开发。写文档的目的，是让你与 Agent 对同一件事有一致预期，并能用证据判断是否完成。

## 第一项业务功能手工完成

M1 将登录功能的规范放在 `specs/001-login/`：

| 文档 | 回答的问题 | 写什么 |
|---|---|---|
| spec.md | 用户为什么需要、预期发生什么 | 场景、范围、具体验收例子、不包含内容 |
| plan.md | 在当前项目怎样实现 | 数据流、Django 能力、接口或页面改变、必要错误处理 |
| tasks.md | 先做什么、怎么知道完成 | 前置条件、任务编号、Agent 与用户分工、验证方法 |

先确认 spec，再编写 plan 和 tasks；实现后逐条对照验收。文档与代码在同一分支、同一 PR 中更新。

已交付的手工实例：[登录规范](../specs/001-login/spec.md)、[技术计划](../specs/001-login/plan.md)、[实施任务](../specs/001-login/tasks.md)、[验收证据](../specs/001-login/acceptance.md)、[独立审查](../specs/001-login/review.md)。T001–T008 已完成，PR #7 合并与实际发布已核对；技术证据和用户反馈分别记录。001-login 保留为已交付规范，功能分支 feat/001-login 为历史分支；交付记录合并后从最新 main 恢复。M2-L01 工具准备已完成，当前 [005-plan-create 需求规范](../specs/005-plan-create/spec.md) 已由用户整份确认；[质量清单](../specs/005-plan-create/checklists/requirements.md) 只检查文档，不代表实现完成。

M0 的 `specs/000-bootstrap/` 保存本次用户已确认的起步准备范围，用于区分代码准备和用户亲手练习。

## 一个规范例子

“用户 A 创建一个计划后可以在自己的列表看到它；用户 B 的列表不显示它，直接访问该计划网址也不能读取或修改。”

“完成一个任务后，计划显示已完成数 / 总任务数；取消完成后进度降低；空计划为 0%。”

这些例子比“实现计划模块”和“支持权限”更容易验收。具体字段、提示和页面细节在功能课程确认。

## M2 已引入 Spec Kit

2026-10-14 M2-L01 工具准备已安装并初始化 Spec Kit 1.2.0，源码 commit 与依赖锁已验证；Codex 技能、PowerShell 脚本和集成状态实际通过。工具用独立环境，不混进网站运行依赖，项目规则为 1.0.0；见 [实际安装与调用](SPECKIT.md)、[本课说明](lessons/M2-L01.md)。第一份工具业务规范 005-plan-create 已在规范续课生成；用户已确认整份规范，下一课编写技术计划与任务，实施未开始。

官方同时支持 GitHub release 源码安装与 PyPI 的 `specify-cli`，也支持 Windows PowerShell。初始化现有目录前检查差异，确保不会覆盖课程记录和手工规范。

核对实际版本的 Codex 集成方式，使用实际安装后显示的技能或命令；不要照抄过期的 `--ai` 参数或其他 agent 的 slash 命令。

每课核对两件事：当前 Git 分支、当前活动功能规范。工具的活动上下文与 Git 分支不是同一回事。若版本采用 `.specify/feature.json`，也要核对该文件指向的功能。

工具流程继续遵守：规范 → 澄清 → 技术计划 → 任务 → 实现 → 对照规范检查和修复。生成任务清单不代表实现已经完成。

参考：[安装指南](https://github.github.io/spec-kit/installation.html)、[官方快速入门](https://github.github.io/spec-kit/quickstart.html)。
