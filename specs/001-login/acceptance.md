# 001 登录：验收证据与用户清单

状态：2026-10-14，用户反馈手机旧地址打不开；已定位电脑换网且 8002 仍绑定旧 IP，刷新到当前 WLAN 地址并通过针对性检查，等待用户手机新地址复验及整体反馈。T007/T008 未完成；新增工作流未推送，远端 CI、Linux Gunicorn 和临时 PostgreSQL 的本轮运行结果待 PR 实际验证。

依据：[已确认规范](spec.md)、[计划](plan.md)、[任务](tasks.md)。本文件记录证据，不改变 A001–A013 的行为条件。用户目前明确反馈的是「两个账号均可正常登录」；没有据此推断其他操作均已验收。

## 本轮实际检查

- SQLite：运行与 CI 一致的 `python manage.py test core.tests --noinput`，**51 项通过**；配置检查与迁移一致性通过。
- 工作流：两条 job 均加入认证/会话测试；PostgreSQL job 继续用原有 `postgres:17` 临时服务，增加配置和迁移一致性检查。`actionlint` v1.7.12 检查通过；工具从官方固定版本下载并核对校验和，仅放本机忽略目录。
- 正式配置：Windows WSGI 真实请求检查通过，包括原首页、哈希静态文件、HTTPS、域名限制，以及新增登录表单、未登录工作台跳转、禁止缓存和 GET 退出 405。使用占位数据库，未连接 PostgreSQL；本机没有可用 Linux/PostgreSQL 环境，相关真实运行留待 T008 CI。
- Edge：1440px、390px、320px 本机页面，以及局域网地址的 390px，共四组完整流程通过；有必填、错误/不存在账号、用户名保留/密码清空、A/B 独立身份、刷新/新标签页、固定跳转、POST 退出、多标签页与旧 Cookie 拒绝。无横向溢出、操作控件高度至少 44px、无页面脚本错误；已查看桌面错误页和局域网窄屏工作台截图。
- T005 原证据：五项可控时间测试本轮再次通过；已保存的真实进程重启与正常关闭重开 Edge 结果仍有效，本轮没有重复重启用户服务。

SQLite/部署命令检查前后用户数据库、密钥和账号资料未变；实际浏览器检查正常写入会话/last_login 并清除自己的会话。无密码重置或线上写入。结果/截图在忽略的 `.tools/qa/t007-browser/`，不进入公开仓库。

## A001–A013 覆盖

| 条件 | 自动检查与 Agent 实际浏览器证据 | 用户实际状态 |
|---|---|---|
| A001 公开首页与登录入口 | [test_login.py](../../core/tests/test_login.py) 的公开首页测试；四组浏览器公开入口 | 本轮未登录入口待反馈 |
| A002 登录字段与范围 | [test_forms.py](../../core/tests/test_forms.py)、[test_login.py](../../core/tests/test_login.py) 的表单渲染；正式配置和四组浏览器 | 本轮表单体验待反馈 |
| A003 登录后本人身份和退出按钮 | [test_login.py](../../core/tests/test_login.py) 的正确登录；[test_logout.py](../../core/tests/test_logout.py) 的 POST 按钮；四组浏览器 | 两个账号正常登录已确认；退出入口细项待本轮反馈 |
| A004 统一错误、保留用户名、清空密码 | [test_forms.py](../../core/tests/test_forms.py) 和 [test_login.py](../../core/tests/test_login.py) 的错误/不存在/停用账号；四组浏览器错误与不存在账号 | 待实际提示反馈 |
| A005 必填不建立身份 | [test_login.py](../../core/tests/test_login.py) 的空字段组合；四组浏览器空提交 | 待实际提示反馈 |
| A006 未登录不能取个人页 | [test_login.py](../../core/tests/test_login.py) 的显式登录路由；正式配置和四组浏览器跳转 | 待用户直接访问反馈 |
| A007 未过期持久性 | [test_sessions.py](../../core/tests/test_sessions.py)；T005 实际服务/浏览器重启；本轮刷新和新标签页 | 刷新/新标签页待反馈；无需重复重启服务 |
| A008 独立会话各自身份 | [test_login.py](../../core/tests/test_login.py)、[test_sessions.py](../../core/tests/test_sessions.py)；四组独立 A/B；T005 重启保留两者 | 分别登录已确认；电脑/手机同时保持待反馈 |
| A009 退出与旧会话失效 | [test_logout.py](../../core/tests/test_logout.py) 的 POST/CSRF、服务记录删除/旧 Cookie 拒绝；四组退出/多标签页/独立 B 保留 | 待用户退出和另一标签页刷新反馈 |
| A010 已登录访问登录页进工作台 | [test_login.py](../../core/tests/test_login.py) 的已登录重定向；四组浏览器 | 可与新标签页一起验收 |
| A011 固定目的地 | [test_login.py](../../core/tests/test_login.py)、[test_logout.py](../../core/tests/test_logout.py) 的 GET/POST next；四组外部 next 不生效 | Agent 已检查，无需用户访问外站 |
| A012 固定七天与到期拒绝 | [test_sessions.py](../../core/tests/test_sessions.py)：第六天读/写、截止前一秒/截止时/之后、旧 Cookie 重放、新登录和独立期限 | 采用自动时间验证，不要求实等七天 |
| A013 手机核心流程 | 四组中的 390px/320px 和局域网 390px 无溢出、控件可用；电脑本机能访问手机测试地址 | 实际手机访问、输入、提示、退出与布局待反馈 |

本表的技术证据目前是本地 SQLite 与 Windows/Edge 结果，不能写成 PostgreSQL 测试通过或本轮远端 CI 已成功。

## 你现在做的五步（约 5–10 分钟）

电脑使用 http://127.0.0.1:8001/。手机与电脑保持同一网络，使用 Agent 提供的局域网地址、独立端口 8002；实际地址保存在本机 `.tools/qa/t007-lan-server.json`，恢复时重新核对。手机上的 127.0.0.1 指向手机自身，不能用电脑的回环地址。

密码沿用本机 `.tools/qa/local-test-accounts.json`，不需要新建账号或操作终端。

1. **电脑：先退出，再直接打开 `/workspace/`。** 应先去登录；空提交提示「请输入用户名」「请输入密码」。
2. **电脑：用 learner_a 试错误密码，再正确登录。** 错误时统一提示、用户名保留、密码清空；正确时看到「你好，learner_a」和退出按钮。刷新后仍为 A，新标签页打开 `/login/` 应直接进入 A 工作台。保留这两个工作台标签页。
3. **手机：打开局域网首页，进入登录，用 learner_b 登录。** 先试一次空/错误输入，再正确登录；提示、输入、按钮均可用，竖屏不需要左右拖动才能操作。电脑刷新仍为 A，手机显示 B。
4. **电脑：在一个工作台标签页退出，刷新另一页。** 退出回公开首页，另一页先去登录；手机刷新仍显示 B。
5. **手机：退出，再打开 `/workspace/`。** 应回首页，个人页面需再次登录。

可复制的**聊天反馈**：

> 电脑：必填/错误提示、A 登录刷新、双标签退出均正常；手机：B 登录与提示、布局、退出均正常；同时使用时各自显示本人。

有问题只需反馈哪一步和实际现象。手机地址打不开时，记录为手机访问待解决，先根据实际错误排查网络；不将本机对局域网地址的访问当成手机已通过，不自动改防火墙、代理或开公网访问。

2026-10-14 实际反馈为手机旧地址打不开。实时网卡与监听确认换网后 IP 已改变，原 8001 正常；Agent 仅刷新自有 8002 的局域网绑定与元数据，新地址 HTTP/390px 登录到退出流程通过。用户须用新核对的链接再试，不沿用昨日地址；实际手机结果仍待反馈，A013 不记为通过。

## 保存与下一步

本课在 `feat/001-login` 保存工作流、部署检查和验收说明的本地提交，运行工具、数据库和凭据仍忽略。T007 等用户整体反馈后才完成；T008 才推送、创建 PR、读取实际 CI、独立 Agent 审查及发布核对。存在核心验收问题时先解决，不提前合并。

官方依据：[Django 测试与独立数据库](https://docs.djangoproject.com/en/5.2/topics/testing/overview/)、[GitHub 临时 PostgreSQL 服务](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers)、[actionlint 固定版本](https://github.com/rhysd/actionlint/releases/tag/v1.7.12)。
