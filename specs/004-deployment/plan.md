# 004 技术计划

## 请求与部署流程

浏览器 HTTPS → Render 的 TLS 代理 → Gunicorn → Django URL/视图/模板；WhiteNoise 返回 collectstatic 收集并带版本散列的 CSS 与图标。服务端使用 Render 提供的实际主机名，不允许任意域名。

本地仍默认 DEBUG=True 和 SQLite。Render 默认关闭 DEBUG，生产模式要求持久环境密钥和 PostgreSQL DATABASE_URL，使用 psycopg 与 dj-database-url 接入 Neon。仅在 Render 或明确设置的代理测试模式信任 HTTPS 转发头；安全 Cookie 随生产模式启用。

## 文件和职责

- config/settings.py：开发/生产配置、域名、HTTPS、PostgreSQL 和静态文件。
- core/views.py、core/urls.py：不含数据库访问的进程健康检查。
- requirements.txt、.python-version：固定运行环境和依赖。
- render.yaml、scripts/render-build.sh、scripts/render-start.sh：Free 服务定义与构建/启动命令，数据库凭据从服务配置注入。
- scripts/check_deployment.py：生产配置下的真实 HTTP 检查，Linux 使用 Gunicorn；Windows 使用标准 WSGI 服务检查应用与中间件，明确区分两种证据。
- .github/workflows/checks.yml：继续配置/迁移检查，并在 Linux 执行正式启动烟雾检查。
- docs/lessons/M0-L04.md、DEPLOYMENT.md、LEARNING_LOG.md：教学指令、实际状态、服务限制与回退。

## 验证与上线

先验证本地开发仍正常，再模拟正式环境检查首页、散列资源、HTTPS/域名限制和配置缺失失败。通过 PR、CI 与独立 Agent 审查后合并。Render/Neon 连接完成时才创建 Free 资源并执行部署，最后请求公开 URL，并等待用户实际网络与手机验收。

本课没有业务模型变更，只应用 Django 内置迁移。构建失败时不替换正常运行的部署；回退优先使用已验证的上个部署，不在本课执行数据库回退或删除。
