# 创建学习计划：调研与决策

日期：2026-10-14。依据已确认 spec、现有代码、Django 5.2 官方文档和本机 5.2.17 源码。
另一位 Agent 按 speckit-plan 的调研流程只读核对，未访问数据库、私有资料或生产，未运行业务测试。
以下是设计依据，不能作为功能运行结果；没有未解决的技术选择。

## 1. 一个模型与一个表单

决策：在已有 core 增加 LearningPlan 和 LearningPlanCreateForm，不拆新服务或前后端。
模型负责字段/关系，创建表单负责输入。Meta.fields 明确只有 title、description、target_date。
保存前先取得未写入实例，服务端赋 owner=request.user，再写入；不绑定客户端指定的旧实例。
工作台先过滤当前 owner，再按创建顺序倒序读取。

理由：复用 Django 能力，避免客户端控制归属或把创建变成更新旧记录。
替代：隐藏 owner 字段、fields="__all__"、JSON API、通用服务层，本轮均无必要。
来源：[字段白名单](https://docs.djangoproject.com/en/5.2/topics/forms/modelforms/#selecting-the-fields-to-use)、[延迟保存](https://docs.djangoproject.com/en/5.2/topics/forms/modelforms/#the-save-method)。

## 2. 文本长度和日期

决策：表单先 strip，再校验 title 的 100 与 description 的 1000 字符上限。
说明模型同时声明 MaxLengthValidator(1000)；TextField 的 max_length 单独使用不等于模型/数据库强制长度。
ORM save 不自动执行 full_clean，所有用户创建必须经过该表单。
去掉输入控件自动生成的原始 maxlength，防止阻挡「100 个有效字符＋首尾空白」这种有效输入。
表单 novalidate，中文错误由服务器统一产生，日期控件仍为 date。

日期的今天/未来限制只放创建表单，在每次 POST 校验时以 Asia/Shanghai 取得当天；
不在模块导入时算今天，不用 UTC 日期或浏览器时钟，也不放全局模型 clean/动态数据库约束。
这样历史目标自然过期后仍能保存/展示，空日期保持 None。
替代：浏览器 maxlength/min 单独把关、模型永久禁止过去日期，均与已确认边界不符。
来源：[表单 CharField](https://docs.djangoproject.com/en/5.2/ref/forms/fields/#charfield)、[TextField](https://docs.djangoproject.com/en/5.2/ref/models/fields/#textfield)、[模型验证](https://docs.djangoproject.com/en/5.2/ref/models/instances/#validating-objects)、[localdate](https://docs.djangoproject.com/en/5.2/ref/utils/#django.utils.timezone.localdate)。

## 3. 明确失败与成功消息

决策：实际写入用 transaction.atomic，DatabaseError 在整个 block 外捕获。
正常退出 block 后再加成功消息、重定向；失败在原绑定表单加已确认的非字段错误，不伪造卡片。
错误诊断不输出连接串、异常对象或账号凭据，日志不记录用户提交内容；
正常绑定表单与本人卡片按规范保留/展示并自动转义，不用宽泛 except Exception 隐藏程序错误。
回滚后内存实例可能仍有 pk，不能以它判断保存成功；连接中断结果未知时不自动重试。

现有配置没有 ATOMIC_REQUESTS，没有外层请求事务，本轮不需要 on_commit 增加复杂性。
如果以后引入外层事务，重新核对消息/提交时机。
来源：[atomic 与异常边界](https://docs.djangoproject.com/en/5.2/topics/db/transactions/#controlling-transactions-explicitly)、[消息](https://docs.djangoproject.com/en/5.2/ref/contrib/messages/#adding-a-message)。

## 4. 检查、持久性与任务顺序

决策：按项目已确认路线补有意义的模型/表单/HTTP 测试，融入每项实现，不强制新增 TDD 审批。
CSRF 测试启用 enforce_csrf_checks；失败测试在真实 INSERT 后抛出明确数据库异常，核对回滚、无成功提示和输入保留。
原 M1 登录/会话测试保留；仅有页面文案断言需按新空状态更新时，保持原认证目的。

新 Client、refresh_from_db 和重登都不是进程重启。后续用 QA 忽略目录的独立文件 SQLite、
临时账号及自有服务通过 HTTP 创建，再停止/重启同一测试服务核对记录；不停止用户 8001 或使用生产数据库。
手机测试用的局域网地址届时重新核对，不引用已停止的旧 8002 地址。
来源：[测试客户端](https://docs.djangoproject.com/en/5.2/topics/testing/tools/#the-test-client)、[隔离测试数据库](https://docs.djangoproject.com/en/5.2/topics/testing/overview/#the-test-database)。

## 5. 迁移与发布

core 目前没有业务模型，下一文件为 core/migrations/0001_initial.py，使用已有用户的可替换依赖。
T001 只生成结构和迁移、在临时测试库验证；接通页面前单独准备本地迁移，不写生产。
现有两条 CI 自动发现 core.tests 新测试，具体远端结果等完整功能 PR；不得提前记为通过。
未来发布使用已有生产配置与构建脚本，读取实际迁移/部署结果；新建表已承载数据后不以回退代码为理由删表。
