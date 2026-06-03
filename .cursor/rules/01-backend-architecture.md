# 后端架构规则（Django + DRF）

后端是典型的业务系统，而非内容网站。

规则：
- 使用 Django App 进行业务边界划分
- 业务逻辑放在 service 层，而非 view
- serializer 只做数据校验与序列化
- view 只负责请求编排

接口设计：
- REST 风格
- 使用明确的 HTTP 状态码
- 返回结构保持一致（code / message / data）

禁止：
- 在 view 中直接写复杂业务逻辑
- serializer 中操作数据库
