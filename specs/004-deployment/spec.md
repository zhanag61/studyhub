# 004：M0-L04 公开首页部署

来源：已确认的 StudyHub 路线与用户「进入下一课」指令。关联 Issue #3。

## 目标与范围

将已有欢迎首页部署到 Render Free Web Service，线上使用 Neon Free PostgreSQL。电脑上的 SQLite 开发体验继续可用。本课只验证首页、静态资源、HTTPS 和部署流程，不实现账号或学习业务。

## 可观察行为与验收

1. 线上 HTTPS 首页返回 200，并包含已验收的主标题和工作台标题。
2. DEBUG 关闭时，CSS 与图标由正式服务正确返回；页面不因静态文件缺失失去样式。
3. Render 使用固定 Python 与依赖，从 GitHub main 构建，以 Gunicorn 启动。
4. 线上配置使用 PostgreSQL；缺少密钥或 DATABASE_URL 时，部署明确失败，不使用临时密钥或 SQLite 保存线上数据。
5. Render 的实际主机名被允许，未知主机被拒绝。普通 HTTP 页面访问重定向到 HTTPS，代理后的 HTTPS 不出现重定向循环。
6. 健康检查仅返回进程状态，不展示配置或凭据；内部 HTTP 检查可成功。
7. 凭据通过连接工具或服务环境变量配置，不进入公开仓库、PR 描述或日志。
8. 本地与 CI 验证正式模式的首页、静态文件、域名及 HTTPS 行为；CI 在 Linux 启动实际 Gunicorn。
9. 部署后记录真实 URL、套餐、费用、实际网络访问与限制。用户在国内普通网络和手机浏览器验收；Agent 的请求结果不代替该反馈。

## 费用和前置条件

仅创建已确认的免费资源；不购买付费套餐。Render 与 Neon 的账号连接是实际建服务和数据库的前置条件，连接完成前继续实现与检查，线上验收保持待办。正式多用户邀请前再次核对免费限制和实际访问，仍按每月新增费用约 50 元约束执行。

## 不包含

登录、邀请码注册、真实测试者数据、备份恢复和业务权限；这些按 M1–M4 推进。不开启付费资源、不创建会过期的 Render Free Postgres、不将有配置文件写成已上线。

## 依据

[Render Django 部署](https://render.com/docs/deploy-django)、[Render 免费限制](https://render.com/docs/free)、[WhiteNoise Django 配置](https://whitenoise.readthedocs.io/en/stable/django.html)。Neon 套餐以账号创建时的官方页面再次确认。
