# 004 部署任务

| 任务 | 前置条件 | 可验证结果 | 执行者 |
|---|---|---|---|
| T001 核对官方限制、工具连接与现有状态 | M0-L03 技术交付完成 | 记录账号连接、免费限制与实际主分支 | Agent |
| T002 配置正式服务器、静态资源和 PostgreSQL | T001、规范明确 | 关闭 DEBUG 的配置完整，缺少关键配置时失败 | Agent |
| T003 编写部署配置与脚本 | T002 | Render Free 配置可用，凭据不在源码 | Agent |
| T004 验证开发和正式请求，加入 CI | T002–T003 | 首页/静态文件/HTTPS/域名检查，Linux Gunicorn CI 通过 | Agent |
| T005 PR、独立审查、修复与合并 | T004 | 有真实 PR、检查证据，main 已同步 | Agent |
| T006 创建免费资源并部署 | T005、Render/Neon 连接和套餐确认 | 真实上线 URL、数据库迁移与静态文件成功 | Agent；必要登录由用户 |
| U001 普通网络与手机验收 | T006 | 用户实际打开页面，反馈访问和样式 | 用户 |
| T007 更新日志和下一步 | 实际结果 | 区分准备、上线、用户反馈，不误记完成 | Agent |

## 当前进度

- [x] T001 官方限制与 main=4ecf1e1 已核对；用户反馈已连接，工具可用。资源位置待确认。
- [x] T002 正式配置，本地检查通过。
- [x] T003 部署脚本与 Free 定义已编写。
- [x] T004 本地请求通过；Linux CI run 37739376003 的真实 Gunicorn、临时 PostgreSQL 迁移与查询通过。
- [x] T005 PR #4 通过 CI 和独立审查后 squash 合并；main=2b0efbf，本地与 origin/main 一致。
- [x] T006 用户创建 Neon Free 项目后，Agent 创建 Render Free 服务；部署 live，真实首页/资源/HTTPS/健康检查与 Neon 18 项迁移核对通过。
- [x] U001 用户反馈电脑和手机均可打开，约 5 秒；未将其记作闲置冷启动实测。
- [x] T007 已记录本轮准备、检查与合并；实际上线和用户反馈到达后继续追加记录。

用户已确认 Render My Workspace 并提供 Neon 项目网址；实际套餐分别为 Free 与 free_v3。PR #4 的最终 CI run 37739647375 通过，独立 Agent 审查无实质问题，已合并为 2b0efbf。公开网址为 https://studyhub-pt86.onrender.com/，上线与 Agent 验证完成，用户反馈电脑和手机均可打开、约 5 秒，本课目标完成。实际 Render 健康检查为默认 TCP；/health/ 端点可用，HTTP 检查路径设置留作后续改进，不宣称 Blueprint 的全部字段已实际应用。
