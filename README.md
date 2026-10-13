# StudyHub · 学习与知识工作台

一个用来学习、也准备逐步投入真实使用的 Django 项目。

**当前阶段：本地登录与工作台已接通，提前补齐 T006 退出按钮；等待用户复验“退出 A → 登录 B”，T005、T007、T008 待办。** [打开本地工作台](http://127.0.0.1:8001/workspace/)，或查看 [GitHub 源码仓库](https://github.com/zhanag61/studyhub)。[线上首页](https://studyhub-pt86.onrender.com/)使用 Render Free + Neon Free PostgreSQL，真实检查与限制见[部署记录](docs/DEPLOYMENT.md)。本课仅保存本地改动，线上登录未发布。

教学默认通过聊天指挥 Agent：你提出需求、确认规范并在浏览器验收；Agent 执行代码、Git、排错与检查，再解释结果。下面的终端命令供选学，不要求每条亲手输入。恢复课程时先看课程日志。

## 先从哪里开始

- 第一课：[亲手启动首页](docs/lessons/M0-L01.md)
- GitHub 课程：[通过 PR 交付改动](docs/lessons/M0-L03.md)
- 部署课程：[把首页放到线上](docs/lessons/M0-L04.md)
- 登录规范：[已确认的使用行为](specs/001-login/spec.md)
- 配置课程：[稳定本地密钥与会话默认值（T001）](docs/lessons/M1-L03.md)
- 表单课程：[中文登录表单与模板（T002）](docs/lessons/M1-L03-T002.md)
- 账号准备：[普通本地验收账号（T003）](docs/lessons/M1-L03-T003.md)
- 登录课程：[接通登录与我的工作台（T004）](docs/lessons/M1-L03-T004.md)
- 当前课程：[补齐退出与账号切换（T006 提前）](docs/lessons/M1-L03-T006.md)
- 完整课程：[M0–M8 课程表](docs/CURRICULUM.md)
- 可复制指令：[如何让 Agent 配合开发](docs/PROMPTS.md)
- 当前状态：[课程日志](docs/LEARNING_LOG.md)
- Git 与 GitHub：[分支、提交、Issue 和 PR](docs/GIT_WORKFLOW.md)
- SDD：[规范驱动开发与 Spec Kit](docs/SDD.md)
- 上线：[部署阶段与费用记录](docs/DEPLOYMENT.md)

## 在这台电脑启动

以下命令输入 **PowerShell**。已经准备好 `.venv` 和依赖，无须重复安装：

```powershell
Set-Location 'D:\developer\studyhub'
.\.venv\Scripts\python.exe manage.py runserver
```

保持这个终端运行，在浏览器打开 <http://127.0.0.1:8000/>。按 `Ctrl+C` 停止服务器。

明确指定 `.venv` 内的 Python，可以避免误用别的项目环境，也不需要调整 PowerShell 脚本执行策略。

## 换一台电脑复现

先安装 Python 3.13 和 Git，再克隆实际建立的仓库。在项目目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

`requirements.txt` 固定了本次验证使用的依赖版本。项目使用 Django 5.2.17；后续补丁升级通过独立任务验证。

## 理解第一条请求

浏览器访问 `/` → `config/urls.py` → `core/urls.py` → `core/views.py` → HTML 模板 → 浏览器显示页面。

首页文案在 `core/views.py` 的 `WELCOME_MESSAGE` 中。第一课会在功能分支上修改它。

## 当前检查

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

GitHub Actions 已在 [PR #2](https://github.com/zhanag61/studyhub/pull/2) 实际运行并通过上述检查；具体结果可查看 [Actions](https://github.com/zhanag61/studyhub/actions)。M0-L04 新增 Linux Gunicorn、正式静态文件、HTTPS/域名和临时 PostgreSQL 的检查；它们的真实运行结果记录在课程日志。M1 已在本地加入登录行为测试；CI 测试步骤与实际 PR 运行留在 T007/T008，不把本地通过当作远端结果。

## 已确认的产品路线

- 邀请码注册、用户名密码登录，首批 5–20 位测试者。
- 用户只能管理自己的计划、任务、笔记和资料。
- 任务只有未完成和完成两种状态，支持取消完成。
- 进度为完成任务数 / 总任务数；没有任务时为 0%。
- 后续扩展笔记、资料链接、标签、搜索与统计。
- 电脑和手机浏览器均需验收；每周学习 5–8 小时。
- 初期密码恢复由管理员核验测试者后处理；邮件自助找回后置。
- 托管新增费用约每月 50 元以内，先验证免费 Render + Neon。

数据库、虚拟环境、密钥和备份不进入代码仓库。本地 DEBUG 模式优先使用 `DJANGO_SECRET_KEY`；未设置时首次生成被 Git 忽略的 `.local-secret-key`，后续重启复用。T001 的默认配置仅用于本地 DEBUG；T004 已在成功登录时写入固定 7 天截止时间，完整边界与重启验证留在 T005。生产环境仍要求环境密钥和 PostgreSQL，原有设置未改变；公开多用户应用还需完成 M1–M4 的业务和验收。
