# 学习计划数据模型设计

状态：设计完成，未创建模型、迁移文件或数据库表。依据 [spec.md](spec.md)。

## LearningPlan（位于 core/models.py）

| 字段 | 拟采用类型 | 约束与用途 |
|---|---|---|
| id | Django 默认 BigAutoField 主键 | 每份独立身份，客户端不能指定待更新对象 |
| owner | ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="learning_plans") | 必填；由服务端设置；用户删除的关系清理由已有账号模型处理，本轮无删除账号接口 |
| title | CharField(max_length=100) | 必填；标题无唯一约束；创建输入去首尾空白后为 1–100 字符 |
| description | TextField(blank=True, max_length=1000, validators=[MaxLengthValidator(1000)]) | 选填、数据库非 NULL；空输入保存 ""；创建输入去首尾空白后最多 1000 字符，内部空格/换行保留 |
| target_date | DateField(blank=True, null=True) | 选填；空输入为 None；创建时不能早于提交时北京时间当天 |
| created_at | DateTimeField(auto_now_add=True) | 服务端生成，用户不填写或修改，用于新建在前 |

模型默认排序：-created_at、-pk。时间相同时以主键稳定排序，外键已有索引足够，本轮不加复杂索引。
不新增 status、progress、任务关联或其他业务字段。

## 验证边界

静态模型字段/validators 描述结构；用户创建输入在 ModelForm 验证并归一化。
普通 ORM save 不自动 full_clean，不能把模型声明当成任意写入都自动校验；本轮无绕过表单的用户写入接口。
说明 MaxLengthValidator 提供显式模型验证能力，SQLite 与 PostgreSQL 均依创建表单执行输入规则。

日期的动态限制只在创建表单 clean_target_date 运行；读取历史记录不重验“今天或未来”，
模型没有永久日期限制。首尾去空白与精确中文提示由创建表单处理，模型不重写全局 save。

owner/id/created_at 不在表单白名单。创建处理器永远新建实例，不能因同名、传入 id 或 owner 而更新他人记录。
每次工作台查询都按 request.user 过滤，日期/标题等信息在过滤后才交给模板。

## 迁移与生命周期

新增 core/migrations/0001_initial.py，依赖 migrations.swappable_dependency(settings.AUTH_USER_MODEL)。
先在临时测试库运行迁移与关系验证；T003 接通页面前在已确认本地 SQLite 应用该迁移。
本课只写设计；生产迁移留完整功能 PR 与发布核对。

只有“创建→持久保存→只读展示”生命周期；无更新/删除状态迁移。
同名记录不会合并，刷新/读取不插入；过了目标日期也不自动更改或删除。
未来代码回退保留该表与记录，删除表、逆向迁移或账号删除不作为本轮回退步骤。
