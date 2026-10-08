# 部署与费用记录

## 当前状态

M0-L04 已实际上线：[StudyHub 首页](https://studyhub-pt86.onrender.com/)。2026-10-08 14:54（北京时间）首次 Render 部署状态为 live，运行版本为 main 的 2b0efbf。Agent 已从本机实际请求验证首页、两个散列静态文件、健康检查和 HTTP → HTTPS。用户明确反馈「电脑手机均可打开，打开时间约5秒」，本课访问目标完成；该时间不是经过闲置休眠后的冷启动测量。

Render 使用用户确认的 My Workspace，服务为 studyhub，Singapore、Free：[服务控制台](https://dashboard.render.com/web/srv-db3jrsl9fdbs73e4a5c0)。Neon 使用用户创建的 [studyhub 项目](https://console.neon.tech/app/projects/green-fire-18526792/branches/br-sparkling-tree-b35byzmm)，AWS Singapore，实际订阅为 free_v3，PostgreSQL 18，默认分支 production，数据库 neondb。没有新购付费套餐或域名。

M0-L03 已建立[公开 GitHub 源码仓库](https://github.com/zhanag61/studyhub)并推送，首页修改通过 [PR #2](https://github.com/zhanag61/studyhub/pull/2) 交付，GitHub CI 实际运行通过。建仓与 Git 操作已由 Agent 使用现有登录执行；用户主要确认需求并验收。源码公开与网站上线分别记录。

## M0-L04：空站访问验证

仅发布没有真实用户数据的欢迎页。当前运行配置：Python 3.13.14、Django 5.2.17、Gunicorn、WhiteNoise、psycopg。生产模式要求 `DJANGO_SECRET_KEY` 和 PostgreSQL `DATABASE_URL`，自动允许 Render 提供的实际主机名并信任其 HTTPS 代理头；缺少关键配置即拒绝启动。

`render.yaml` 保存可复现的 Free 服务定义，不包含数据库凭据。单个服务可由连接工具直接创建；工具创建不会自动应用整个 Blueprint。构建命令为 `bash scripts/render-build.sh`，启动命令为 `bash scripts/render-start.sh`，分支为 GitHub main，地区建议 Singapore。脚本固定依赖、收集静态文件、执行 Django 内置迁移，再以 Gunicorn 绑定 Render 的 `PORT`。

部署前检查是否已有同名资源，避免重复创建。Neon 项目必须是已确认的 Free 项目；数据库初始化使用**直接连接**，主机名不带 `-pooler`。当前仅两名 Gunicorn worker，连接在请求结束时释放，先复用直接连接；后续业务需要连接池时，另配直接迁移连接，不把迁移送往池化连接。线上数据库要求 TLS；CI 的一次性本机 PostgreSQL 单独关闭 TLS。

直接创建服务时在环境配置注入 `PYTHON_VERSION=3.13.14`、`DJANGO_DEBUG=false`、随机持久密钥和数据库连接串。已有服务更新环境变量必须合并，不覆盖其他变量。Blueprint 定义 `/health/` 检查路径；实际连接工具创建不支持该字段，服务的 healthCheckPath 为空，当前使用平台默认 TCP 检查。`/health/` 已公开验证返回 200 和进程状态；后续可在服务设置改为 HTTP 检查，M4 再规划数据库就绪检查。

记录真实部署地址、时间、使用套餐、费用和国内普通网络访问结果。分别测试首次打开、刷新、页面样式和手机打开。若失败，记录错误证据并调整这一部署步骤；不能把有代码写成已上线。

## 当前验证与免费限制

本地开发配置、迁移一致性和依赖检查通过。Windows 正式 WSGI 请求检查通过：首页、散列 CSS/图标、内部健康检查、HTTPS 转发与错误域名；缺少密钥/数据库或配置错误时按预期失败。该项使用占位数据库。[PR #4](https://github.com/zhanag61/studyhub/pull/4) 的初次 CI run 37739376003 和[最终 CI run 37739647375](https://github.com/zhanag61/studyhub/actions/runs/37739647375) 均实际通过 Linux Gunicorn 启动、正式请求、临时 PostgreSQL 迁移和查询。独立 Agent 审查未发现实质问题，PR 已 squash 合并为 main 的 2b0efbf，本地已同步。

真实部署 dep-db3jrtl9fdbs73e4a91g 已成功：构建日志记录内置迁移和静态文件收集成功；运行日志确认 Gunicorn gthread、两名 worker、0.0.0.0:10000；Neon 的只读查询核对 django_migrations 有 18 行。公开首页返回 200，两个标题正确；styles.7444a497f306.css 与 favicon.c363266dcd27.svg 均返回 200 及正确类型，安全响应头、/health/ JSON、公开 HTTP 跳 HTTPS 均通过。用户另行反馈电脑和手机可打开、约 5 秒；用户未逐项描述布局细节，也未实测闲置冷启动，这些不记录为完整验证。

2026-10-08 核对官方说明：Render Free 闲置约 15 分钟会休眠，冷启动约一分钟，工作区每月 750 免费实例小时；文件系统不持久。本项目不使用 30 天到期的 Render Free PostgreSQL。Neon 官方 2026-10-02 公告列出 Free 每项目 1 GB、每月 100 CU-hours；实际选定账号套餐还需核对。[Render 免费限制](https://render.com/docs/free)、[Neon Free 公告](https://neon.com/blog/neon-free-plan-1-gb-per-project)。

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

官方参考：[Render 免费服务](https://render.com/docs/free)、[Neon 免费额度](https://neon.com/blog/neon-free-plan-1-gb-per-project)。
