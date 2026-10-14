# 部署与费用记录

## 当前状态

2026-10-14 M1 登录功能已发布：[线上登录页](https://studyhub-pt86.onrender.com/login/)。Render 部署 dep-db76ef6i0phs738o2k20 的版本精确为 PR #7 的 main=f2248aa，01:16:48（北京时间）live；Agent 的公开匿名请求全部通过。电脑/手机正确登录与退出反馈来自本地服务；learner_a/b 没有同步到线上，生产账号准备仍在 M4。

M0 首次上线为 2026-10-08 14:54（北京时间）的 2b0efbf，用户当时反馈「电脑手机均可打开，打开时间约5秒」；该历史反馈不是新登录版本或休眠冷启动的测量。

Render 使用用户确认的 My Workspace，服务为 studyhub，Singapore、Free：[服务控制台](https://dashboard.render.com/web/srv-db3jrsl9fdbs73e4a5c0)。Neon 使用用户创建的 [studyhub 项目](https://console.neon.tech/app/projects/green-fire-18526792/branches/br-sparkling-tree-b35byzmm)，AWS Singapore，实际订阅为 free_v3，PostgreSQL 18，默认分支 production，数据库 neondb。没有新购付费套餐或域名。

M0-L03 已建立[公开 GitHub 源码仓库](https://github.com/zhanag61/studyhub)并推送，首页修改通过 [PR #2](https://github.com/zhanag61/studyhub/pull/2) 交付，GitHub CI 实际运行通过。建仓与 Git 操作已由 Agent 使用现有登录执行；用户主要确认需求并验收。源码公开与网站上线分别记录。

## M0-L04：空站访问验证

仅发布没有真实用户数据的欢迎页。当前运行配置：Python 3.13.14、Django 5.2.17、Gunicorn、WhiteNoise、psycopg。生产模式要求 `DJANGO_SECRET_KEY` 和 PostgreSQL `DATABASE_URL`，自动允许 Render 提供的实际主机名并信任其 HTTPS 代理头；缺少关键配置即拒绝启动。

`render.yaml` 保存可复现的 Free 服务定义，不包含数据库凭据。单个服务可由连接工具直接创建；工具创建不会自动应用整个 Blueprint。构建命令为 `bash scripts/render-build.sh`，启动命令为 `bash scripts/render-start.sh`，分支为 GitHub main，地区建议 Singapore。脚本固定依赖、收集静态文件、执行 Django 内置迁移，再以 Gunicorn 绑定 Render 的 `PORT`。

部署前检查是否已有同名资源，避免重复创建。Neon 项目必须是已确认的 Free 项目；数据库初始化使用**直接连接**，主机名不带 `-pooler`。当前仅两名 Gunicorn worker，连接在请求结束时释放，先复用直接连接；后续业务需要连接池时，另配直接迁移连接，不把迁移送往池化连接。线上数据库要求 TLS；CI 的一次性本机 PostgreSQL 单独关闭 TLS。

直接创建服务时在环境配置注入 `PYTHON_VERSION=3.13.14`、`DJANGO_DEBUG=false`、随机持久密钥和数据库连接串。已有服务更新环境变量必须合并，不覆盖其他变量。Blueprint 定义 `/health/` 检查路径；实际连接工具创建不支持该字段，服务的 healthCheckPath 为空，当前使用平台默认 TCP 检查。`/health/` 已公开验证返回 200 和进程状态；后续可在服务设置改为 HTTP 检查，M4 再规划数据库就绪检查。

记录真实部署地址、时间、使用套餐、费用和国内普通网络访问结果。分别测试首次打开、刷新、页面样式和手机打开。若失败，记录错误证据并调整这一部署步骤；不能把有代码写成已上线。

## M1-T008：登录版本的实际发布

[PR #7](https://github.com/zhanag61/studyhub/pull/7) 已通过独立审查并 squash 合并为 f2248aa71d8df0f1041095dd85c07ce93ce46a80。修复后 [CI run 38435955339](https://github.com/zhanag61/studyhub/actions/runs/38435955339) 的 SQLite/临时 PostgreSQL 各 51 项、迁移、Linux Gunicorn 与正式请求全部通过。本轮没有新业务模型或迁移文件，生产密钥、数据库连接和套餐保持已有配置，没有创建或重置生产账号。

合并后核对 Render 部署/事件记录，仍只有旧 M0 版本。现有服务通过公开 Git 仓库 URL 创建，虽元数据 autoDeploy=yes，官方明确该方式不支持自动部署；以后不能仅凭该字段认定推送会发布。Agent 在已确认工作区和服务触发一次不清缓存的手动发布，返回 commit=f2248aa；dep-db76ef6i0phs738o2k20 于 2026-10-14 01:16:48（北京时间）live。[Render 发布说明](https://render.com/docs/deploys)、[公开仓库连接说明](https://render.com/docs/web-services)。自动连接 GitHub 账号可另做维护任务，不作为本课交付前置。

本机真实 HTTPS 请求：公开首页 200，新标题「今天，给自己的成长留一点时间。」与登录入口正确；/login/ 200 含用户名/密码/CSRF，Secure/SameSite Cookie 与 no-store；匿名 /workspace/ 302→/login/?next=/workspace/ 且没有个人内容；GET /logout/ 405；/health/ 200/status=ok/no-store；散列 CSS/favicon 200、正确类型与 immutable；HTTP 跳 HTTPS。共 8 项通过，X-Frame-Options=DENY、HSTS max-age=3600。没有记录令牌/Cookie 值或密码，没有尝试本地账号的线上登录。

后续纯文档交付记录可以使 main SHA 领先 Render 的 f2248aa，但运行代码保持完全相同，记录代码版本与文档版本的区别；不为仅教材变化重复发布。未来业务 PR 合并后先核对现有部署是否已覆盖该版本，没有排队/构建且需要发布时才手动触发；等 live 后再核对公开请求。

如该登录版本出现代码故障，可进入 [Render 服务控制台](https://dashboard.render.com/web/srv-db3jrsl9fdbs73e4a5c0) → Manual Deploy → Deploy a specific commit，选此前实际验证的 2b0efbfc01477bc094b1dc475b29510f0bf6ce4a。完成后核对首页、health 和对应 commit；该旧版没有登录入口。本轮未实际执行回退；代码回退不删除数据库/账号/会话，不旋转密钥或逆向迁移，修复仍走新 PR。

## 当前验证与免费限制

本地开发配置、迁移一致性和依赖检查通过。Windows 正式 WSGI 请求检查通过：首页、散列 CSS/图标、内部健康检查、HTTPS 转发与错误域名；缺少密钥/数据库或配置错误时按预期失败。该项使用占位数据库。[PR #4](https://github.com/zhanag61/studyhub/pull/4) 的初次 CI run 37739376003 和[最终 CI run 37739647375](https://github.com/zhanag61/studyhub/actions/runs/37739647375) 均实际通过 Linux Gunicorn 启动、正式请求、临时 PostgreSQL 迁移和查询。独立 Agent 审查未发现实质问题，PR 已 squash 合并为 main 的 2b0efbf，本地已同步。

真实部署 dep-db3jrtl9fdbs73e4a91g 已成功：构建日志记录内置迁移和静态文件收集成功；运行日志确认 Gunicorn gthread、两名 worker、0.0.0.0:10000；Neon 的只读查询核对 django_migrations 有 18 行。公开首页返回 200，两个标题正确；styles.7444a497f306.css 与 favicon.c363266dcd27.svg 均返回 200 及正确类型，安全响应头、/health/ JSON、公开 HTTP 跳 HTTPS 均通过。用户另行反馈电脑和手机可打开、约 5 秒；用户未逐项描述布局细节，也未实测闲置冷启动，这些不记录为完整验证。

2026-10-08 核对官方说明：Render Free 闲置约 15 分钟会休眠，冷启动约一分钟，工作区每月 750 免费实例小时；文件系统不持久。本项目不使用 30 天到期的 Render Free PostgreSQL。Neon 官方 2026-10-02 公告列出 Free 每项目 1 GB、每月 100 CU-hours；实际选定账号已核对为 free_v3，1 GB 大小限制与公告一致。[Render 免费限制](https://render.com/docs/free)、[Neon Free 公告](https://neon.com/blog/neon-free-plan-1-gb-per-project)。

未购买套餐或域名。本次只创建免费资源；构建、流量及计算额度仍需监测，接近限制时先评估，付费必须先核算总费用。默认休眠是测试版已知限制，不承诺全天即时访问。

## M4：公开多用户测试版

上线前使用外部持久 PostgreSQL，并验证迁移、用户数据权限、重启后数据保存、备份恢复和手机核心流程。开发服务器不能用于公开服务。

Render 免费实例会休眠，本地 SQLite 和上传文件不能用来保存测试者数据。不能选用会到期的免费数据库，然后假设它能永久保存数据。

Neon 当前 Free 订阅已通过项目 API 核对；正式邀测前再次核对额度。记录存储与计算使用量，超限前评估是否减少负载或升级；公开测试版接受已说明的冷启动，但必须保持正确的数据保存与权限行为。

预算是每月新增费用约 50 元，域名与其他服务也计入。当前没有购买域名、套餐或 API。付费前先列清总费用与可能超量部分。

## 上线检查与恢复

首次上线没有旧部署可回退：构建失败时保留错误证据并修复，不伪造上线成功。后续发布失败时保留仍正常的旧部署；代码问题可在 Render 选择上一个已验证部署回退，或通过独立修复 PR 恢复版本。数据库迁移与代码版本分别处理，不能擅自执行数据库删除或逆向迁移。

- 真实网址可以在目标网络打开。
- 正确登录、退出、注册及无效邀请场景。
- 两位用户通过列表、直接网址、表单均不能跨用户访问资源。
- 重启或发布之后，数据库中的已保存内容仍在。
- 隔离环境完成一次备份恢复；记录版本、备份和验证结果。
- 代码回退与数据库恢复分别制定步骤，不因回退代码而擅自删除数据。

## 发布记录表

| 日期 | 版本 / commit | 地址 | 托管与套餐 | 数据库 | 实际验收 | 费用 |
|---|---|---|---|---|---|---|
| 2026-10-08 | 2b0efbf / M0 欢迎页 | [公开首页](https://studyhub-pt86.onrender.com/) | Render Free / Singapore | Neon Free / PG18 | Agent 请求和迁移通过；用户电脑/手机均可打开，约 5 秒 | 0 元新增购买，持续监测免费额度 |
| 2026-10-14 | f2248aa / M1 登录 | [登录页](https://studyhub-pt86.onrender.com/login/) | Render Free / Singapore | 既有 Neon Free | Agent 公开匿名 8 项通过；正确凭据流程为本地用户/CI 证据，线上账号后置 | 0 元新增购买，持续监测免费额度 |

官方参考：[Render 免费服务](https://render.com/docs/free)、[Neon 免费额度](https://neon.com/blog/neon-free-plan-1-gb-per-project)。
