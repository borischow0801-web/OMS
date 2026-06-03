# 数据库与迁移规则（MySQL）

规则：
- 所有表必须有：
  - created_at
  - updated_at
- 字段命名清晰表达业务含义
- 使用 Django migration 管理变更

任何变更必须说明：
- 是否影响历史数据
- 是否需要数据修复脚本
- 是否支持回滚

