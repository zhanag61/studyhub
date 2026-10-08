# Git 与 GitHub：让 Agent 保存和交付小功能

Git 保存本地版本；GitHub 保存远端仓库，并提供 Issue、PR 和自动检查。分支让一项修改有自己的工作范围；PR 让改动可以比较和审查。

## 默认分工

按 2026-10-08 用户最新要求，你通过聊天提出需求、确认规范和在浏览器验收；Agent 检查分支、实现、测试、提交与准备 PR，再解释结果。Git 命令练习为选学。合并与发布按当前任务授权执行。

账号登录或工具无法执行的网页动作，再由用户完成必要步骤。

## 当前状态

本地有 main 起步基线和 feat/m0-welcome-message 功能分支。个人文案已保存为提交 e9a8665，页面配色与课程调整另存一项提交。M0-L02 完成记录见 [课程日志](LEARNING_LOG.md)。

当前没有配置 Git 远端。起步时核实的 GitHub 账号为 zhanag61，当时 studyhub 仓库查询返回 404；M0-L03 建仓前须重新核对账号和仓库是否存在。

## M0-L02：用聊天指令保存版本

详细说明见 [M0-L02](lessons/M0-L02.md)。你可以这样发指令：

> 检查当前分支和差异，把已验收的本课改动保存为提交。个人文案与页面配色分开保存。由你执行 Git，告诉我提交编号、保存内容、检查结果和工作区状态。

Agent 核对文件、检查差异并提交，不能只交付命令清单。代码、页面和课程记录按实际归属保存，不提交虚拟环境、数据库或密钥。

本项目曾遇到不同 Windows 账户引起的 detected dubious ownership，用户已信任指定项目。修复记录保留在 M0-L02；不要求重复设置。

## M0-L03：建立远端与第一次 PR

发到聊天：

> 开始 StudyHub 的 GitHub 课程。先检查本地状态、当前 GitHub 账号和 studyhub 仓库是否存在，再建立已确认的公开仓库、推送 main 和功能分支、创建 Issue 与 PR。由你执行可用工具和 Git 操作，解释分支与 PR 的作用；我查看页面和差异。需要账号登录或工具无法执行的网页步骤时再指导我。

Agent 应优先用可用工具完成工作。若必须由用户网页建仓，只指导必要步骤：创建公开的 studyhub 仓库；本地已有文件时，新远端不自动生成 README、.gitignore 或许可证。已有同名仓库先检查内容，不能覆盖。

确认远端仓库后，Agent 添加或核实 origin，推送 main 和功能分支。登录通过 Git Credential Manager 或已连接工具完成，不要求用户在聊天中提供密码或 token。

Issue 记录本次目标和验收；PR 的 base 为 main，compare 为 feat/m0-welcome-message。PR 描述使用实际验证结果并关联真实 Issue。推送后查看 GitHub Actions 的真实结果，由另一位 Agent 按规范审查，你在浏览器验收。

完成授权的 Squash and merge 后，Agent 同步本地 main 并验证内容和工作区。删除功能分支前核对合并结果；squash 合并后可能需要进一步确认分支提交内容是否已包含。

## 后续功能的循环

Issue → 从最新 main 建分支 → 写规范、计划、任务 → 小步实现 → 验收与提交 → 推送 → PR → 审查和修复 → 合并 → 同步 main。

你负责描述可见行为和验收条件，Agent 完成机械操作。一项功能可以包含多个小提交，每次保存应有清楚的范围和说明。

命令供选学，以下操作默认由 Agent 检查工作区后执行：

```powershell
git status
git switch main
git pull --ff-only origin main
git switch -c feat/002-plan-create
```

## 单人仓库规则

CI 实际运行后，再设置 main 所需检查。Agent 代码审查与 GitHub 真人批准分别记录；单人项目不设置无法自行满足的真人批准人数。

参考：[GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow)。
