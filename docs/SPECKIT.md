# StudyHub 的 Spec Kit 使用说明

2026-10-14，M2-L01 工具准备完成。依据 [官方 v1.2.0](https://github.com/github/spec-kit/releases/tag/v1.2.0)、[安装指南](https://github.github.io/spec-kit/installation.html) 和[已有项目接入指南](https://github.github.io/spec-kit/guides/existing-projects.html)，锁定 specify-cli 1.2.0，源码 commit 为 `4ca46a0706a662b1edc07086ef16f021820c2db0`，实际 CLI 与安装元数据相符。

## 它怎样接上已学的流程

Spec Kit 提供模板、固定提示与路径脚本，Agent 据此生成文档；你仍决定需求、确认规范和实际使用验收。

| 已学步骤 | Codex 聊天里的技能 | 结果或用途 |
|---|---|---|
| 项目共用规则 | `$speckit-constitution` | .specify/memory/constitution.md |
| 写本课需求 | `$speckit-specify` | 新 feature 目录中的 spec.md |
| 问清行为 | `$speckit-clarify` | 解决规范中的关键歧义 |
| 制定技术方案 | `$speckit-plan` | plan.md 与必要设计资料 |
| 检查需求质量 | `$speckit-checklist` | 检查需求是否明确，不代表代码完成 |
| 拆小任务 | `$speckit-tasks` | 可按用户故事实施的 tasks.md |
| 核对文档一致性 | `$speckit-analyze` | 对照规范、计划、任务，报告缺口 |
| 只实现已授权任务 | `$speckit-implement` | 依当前范围修改应用并验证 |
| 核对实现完整性 | `$speckit-converge` | 有缺口时记录剩余任务，未授权部分不直接实现 |

这些是**聊天指令**，不是 PowerShell 命令。Codex 集成将它们安装在 `.agents/skills/speckit-*/SKILL.md`；调用拼写以本次安装文件为准，不照抄其他 Agent 的 `/speckit.*`。[官方集成说明](https://github.github.io/spec-kit/reference/integrations.html)

当前聊天可直接要求 Agent 读取项目里的对应 SKILL.md 并执行，无需依赖技能菜单刷新。CLI 和脚本已验证；桌面菜单是否自动刷新尚未实测，不将文件安装写成 UI 已验证。

## 安装与复现

- 工具环境：.tools/speckit/venv，被 Git 忽略，不改变网站 .venv 或运行依赖。
- 来源与平台：[installation.json](../tools/speckit/installation.json)；Windows AMD64、Python 3.13.14、Codex、PowerShell。
- 完整依赖锁：[requirements-windows.txt](../tools/speckit/requirements-windows.txt)，固定源码 commit 与实际依赖；其他平台未验证。
- 调用入口：[speckit.ps1](../scripts/speckit.ps1)，始终使用项目环境，并从项目根执行。
- 复现安装：[setup-speckit.ps1](../scripts/setup-speckit.ps1)，先按 README 准备网站 .venv，再安装独立工具；它不执行初始化。

下面供选学或其他电脑复现，输入 **PowerShell**；当前电脑已经由 Agent 执行，无需重复输入：

```powershell
Set-Location 'D:\developer\studyhub'
.\scripts\setup-speckit.ps1
.\scripts\speckit.ps1 --version
.\scripts\speckit.ps1 integration status --json
```

首次安装使用官方标签，metadata 核对实际源码 commit；复现锁固定该 commit，不使用移动的 latest/main。specify version 只报告版本，来源另从 direct_url.json 验证。升级另建任务，阅读说明并验证，不自动替换。

## 初始化与实际验证

先在 .tools/qa/m2l01-smoke 隔离初始化，再检查生成路径没有冲突。正式项目从干净 main=9b8baf3 建 feat/m2-speckit-setup，执行了：

```powershell
.\scripts\speckit.ps1 init --here --force --integration codex --script ps --non-interactive
```

这是**首次接入记录，不是日常启动命令**。--force 允许在非空项目合并受管理文件；本次先查路径并比较原文件，未覆盖应用、已有规范、课程说明、数据库、密钥或账号资料。以后不重复 init，需要刷新模板时另行审查。

隔离目录实际执行创建临时规范、setup-plan、setup-tasks 和 check-prerequisites。setup-tasks 只返回模板，Agent 写入隔离示例后，要求 spec/plan/tasks 的检查通过；模板示例不是业务需求。正式集成报告 status=ok，缺失/修改/非法受管理文件均为 0。只读 DryRun 成功；当前已有 004-deployment，下一编号候选为 005，本课未创建该业务目录。

采用 [speckit-constitution](../.agents/skills/speckit-constitution/SKILL.md) 整理 [项目规则](../.specify/memory/constitution.md) 为 1.0.0。先解析实际模板，再只修改 constitution；原模板和技能未改。规则来自已确认路线与 AGENTS，初次成文不是新的产品决定。同步影响报告已核对并在提交前移除，无待补占位符、扩展 hook 或延后治理决定。

CLI、依赖、集成状态、安装脚本与 PowerShell 流程实际通过。本课没有应用行为变化，不为可逆工具准备新增重复业务测试；PR 读取现有真实 CI，并按仓库约定安排独立审查。

仓库固定 PowerShell 与 .specify 文件使用 LF 行尾，避免 Windows 检出时改变受管理文件的哈希；22 个受管理文件的工作区与暂存内容均与安装 manifest 相符。仅课程文档的 128 个相对链接通过，通用模板中的占位链接按模板用途保留。

## Git 与活动规范分开核对

Git 分支保存历史；.specify/feature.json 指向本机活动规范，官方将它列为不提交的每次检出状态。**切换 Git 分支不会自动切换活动规范**，每次继续工作都核对二者，不静默采用历史登录目录。

正式项目当前没有 feature.json，也没有新业务规范；001-login、000-bootstrap、004-deployment 原样保留。先确认需求，再创建下一份规范；Agent 记录真实目录、分支与本机指针，换电脑时按课程日志恢复。

本课未启用可选 Git 扩展，Agent 沿用现有 feat/... 与 Issue/PR 流程；核心工具负责文档路径。未安装 GitHub 扩展或调用已弃用的 taskstoissues 技能。

## 下一课聊天指令

> 开始 M2-L01 规范续课。读取课程日志、项目规则与 speckit-specify 技能，核对 Git 和活动规范。围绕「创建自己的学习计划」问清会影响行为的需求，再生成第一份工具规范并用具体例子让我确认。Git 和文件操作由你完成，暂不写业务代码或技术计划。
