# AGENTS.md

本文件用于给 AI 编码助手、自动化审查工具和后续维护人员提供项目协作约束。内容基于当前仓库代码与文档整理，不代表未验证的生产事实。

## 项目概览

本项目是“信息化软件项目运维管理系统”，用于使用方、管理方、承建方之间协同处理问题反馈、需求任务和运维记录。

当前仓库包含：

- Django 后端：`backend/`
- React PC 前端：`frontend-pc/`
- 微信小程序：`frontend-miniprogram/`
- 部署、排障和功能说明文档：`docs/`

## 协作原则

1. 修改前先阅读相关模块代码，不要只根据 README 判断当前实现。
2. 不要编造业务流程。若代码、文档和生产现状不一致，标记为“待确认”。
3. 业务代码修改应保持小范围、可回滚，避免顺手重构无关模块。
4. 涉及数据库结构时，优先使用 Django migration，不要直接手写生产 SQL。
5. 涉及用户认证、角色权限、短信、附件存储、Nginx 配置时，需要同时核对代码和 docs。
6. 仓库中 `docs/` 同时包含项目文档和部分按日期组织的附件文件，操作时要避免误删或覆盖。

## 不应随意修改的内容

- `backend/.env`、`frontend-pc/.env.local` 中的实际环境配置。
- `docs/2026/` 等日期目录下的附件文件。
- 已生成的前端构建产物目录，如 `frontend-pc/dist-*`，除非任务明确要求处理构建产物。
- 用户上传文件、Excel 模板、生产排障记录。

## 后端注意事项

后端入口：

- 配置：`backend/oms_backend/settings.py`
- 路由：`backend/oms_backend/urls.py`
- 用户与认证：`backend/apps/accounts/`
- 任务流程：`backend/apps/tasks/`
- 工作流、通知、短信：`backend/apps/workflow/`
- 运维记录：`backend/apps/maintenance/`

重要约束：

- 用户模型为自定义 `accounts.User`。
- 业务角色字段为 `role`，取值包括 `user`、`admin`、`manager`、`employee`。
- Django 管理后台权限仍可能依赖 `is_staff` / `is_superuser`。
- 登录逻辑优先调用 Bspplus，网络异常时回退本地认证。
- 附件通过 `DateBasedFileStorage` 写入 `OMS/docs/YYYY/MM/DD/`。
- MySQL 配置中存在硬编码 `unix_socket`，本地或非该路径部署时需特别确认。

## 前端注意事项

PC 前端入口：

- 路由：`frontend-pc/src/App.jsx`
- 全局布局：`frontend-pc/src/components/Layout.jsx`
- API 封装：`frontend-pc/src/api/`
- 登录状态：`frontend-pc/src/store/authStore.js`
- 页面：`frontend-pc/src/pages/`

约束：

- API 默认 baseURL 为 `VITE_API_BASE_URL`，未配置时使用 `/api`。
- Vite 开发服务器端口为 3000，并代理 `/api` 到 `localhost:8000`。
- 页面权限以用户 `role` 判断。
- 任务流程操作集中在任务详情页。
- 运维记录入口仅对 `manager` 和 `employee` 展示。

小程序入口：

- 配置：`frontend-miniprogram/app.json`
- API 地址：`frontend-miniprogram/utils/config.js`
- 登录：`frontend-miniprogram/pages/login/`
- 任务列表：`frontend-miniprogram/pages/tasks/list/`
- 任务详情：`frontend-miniprogram/pages/tasks/detail/`

小程序当前有 TODO 和待验证功能，不要按文档直接假定已完整实现。

## 测试与验证建议

后端常用验证：

```bash
cd backend
python manage.py check
python manage.py migrate --check
python manage.py runserver 0.0.0.0:8000
```

PC 前端常用验证：

```bash
cd frontend-pc
npm run build
npm run dev
```

短信功能可通过管理命令或 Django Admin 验证。具体命令参考 `docs/短信发送功能测试方法.md`。

小程序需使用微信开发者工具验证。生产环境需要合法域名和 HTTPS，具体见 `docs/小程序部署说明.md`。

## 已知风险

- README 和部分 docs 与当前代码存在不完全一致。
- 小程序文档描述的功能多于当前代码实现。
- 短信接口响应字段在文档与代码中存在不一致描述。
- `Notification` 模型枚举未包含代码中使用的 `task_reopened`。
- `docs/` 被用作附件存储目录，文档目录与上传文件混杂。

