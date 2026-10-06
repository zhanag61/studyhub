# Git 与 GitHub：每项小功能怎样保存和交付

Git 保存本地版本；GitHub 保存远端仓库，并提供 Issue、PR 和自动检查。分支让一项修改有自己的工作范围；PR 让改动可以比较和审查。

## 当前状态

Agent 已为起步交付准备 main 初始化基线。你从 M0-L01 的文案修改开始，在短期分支上完成自己的第一次提交；用 git log --oneline 查看当前版本。

GitHub 连接已核实，账号为 `zhanag61`。查询 `zhanag61/studyhub` 返回 404，尚不能认为远端仓库已经存在。GitHub CLI 未安装；课程使用网页与 Git Credential Manager，当前无需先装 gh。

## M0-L02：提交文案修改

先确认课程编号与分支，不直接复制后执行未知文件修改。

```powershell
Set-Location 'D:\developer\studyhub'
git status
git diff -- core/views.py
git add core/views.py
git diff --cached
git commit -m "feat: personalize the welcome message"
```

- `diff` 看尚未暂存的内容。
- `add` 选定本次提交的文件。
- `diff --cached` 检查真正准备提交的差异。
- `commit` 保存一个可解释的版本。

提交后检查 `git status` 和 `git log --oneline -3`。如果还有课程日志修改，先确认其归属，再用明确文件名暂存。

## M0-L03：建立远端与第一次 PR

在 GitHub 网页创建公开仓库，名称 `studyhub`。由于本地已经有文件，新仓库不勾选自动生成 README、.gitignore 或许可证。若仓库已存在，先由 Agent 检查，不覆盖。

确认仓库创建成功后，输入 PowerShell：

```powershell
git remote add origin https://github.com/zhanag61/studyhub.git
git push -u origin main
git push -u origin feat/m0-welcome-message
```

按 Git Credential Manager 的浏览器登录流程认证；不用把密码或 token 贴到聊天。若 origin 已存在，先读 `git remote -v` 核实，不能重复添加。

网页上先创建文案修改 Issue，写清问题和验收结果。再创建 PR：base 为 main，compare 为 feat/m0-welcome-message。

使用仓库模板补全实际验证结果，关联真实 Issue 编号。查看 Files changed，学习逐行比较；查看 Actions 的真实检查结果。

由 Agent 审查、你亲手验收后，在网页选择 **Squash and merge**。合并后：

```powershell
git switch main
git pull --ff-only origin main
git status
```

确认远端合并已在本地 main 中，并且工作区干净。再删除已经完成的功能分支；如果 Git 对 squash 合并后的分支删除提出提示，交给 Agent 核对提交内容，不盲目强制删除。

## 后续功能的循环

Issue → 从最新 main 建分支 → 写规范、计划、任务 → 小步实现 → 验收与提交 → 推送 → PR → 审查和修复 → 合并 → 同步 main。

例如创建学习计划时：

```powershell
git status
git switch main
git pull --ff-only origin main
git switch -c feat/002-plan-create
```

只有工作区状态和上一个功能处理完毕后才进入这组操作。一次提交可以小于一项功能，但应当描述一个清楚的结果。

## 单人仓库规则

检查实际运行后，再设置 main 必须通过 PR 与 Django 检查。不要设置只有另一个真人才能满足的必需批准人数；Agent 的代码审查与 GitHub 真人批准是不同步骤。

参考：[GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow)。
