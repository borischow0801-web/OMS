# 认证与安全规则

认证方式：
- JWT（Simple JWT）

规则：
- access token 只用于短期访问
- refresh token 只用于刷新，不参与业务请求
- 权限校验必须在后端完成

禁止：
- 只依赖前端控制权限
- 在 token 中存放敏感信息

