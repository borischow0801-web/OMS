# 前端架构规则（React 18 + Ant Design）

定位：
- 后台管理系统（非 C 端）

规则：
- 页面组件只处理 UI
- 业务逻辑集中在 hooks / services
- Zustand 只存全局状态（用户、权限、配置）
- 路由必须与权限系统绑定

Ant Design 使用原则：
- 不过度定制样式
- 优先使用官方组件
