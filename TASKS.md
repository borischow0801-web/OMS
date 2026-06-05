# TASKS.md

本文件记录基于当前项目审查发现的待办事项。内容不代表已经排期，优先级为建议值。

## P0 生产风险

### 1. 确认 MySQL 连接方式

现状：

- `backend/oms_backend/settings.py` 中 `DATABASES.OPTIONS.unix_socket` 固定为 `/data/mysql/mysqld.sock`。

风险：

- 若部署环境没有该 socket，或使用远程 MySQL，数据库连接会失败。

建议：

- 改为通过环境变量控制是否启用 socket。
- 待确认生产 MySQL 实际连接方式。

状态：待确认。

### 2. 确认生产安全配置

现状：

- `DEBUG` 默认值为 True。
- `SECRET_KEY` 有默认不安全值。
- `ALLOWED_HOSTS` 默认仅 localhost/127.0.0.1。

建议：

- 确认生产 `.env` 中是否显式覆盖。
- 部署文档中补充生产检查清单。

状态：待确认。

### 3. 确认 Bspplus 生产配置

现状：

- 代码支持 `BSPPLUS_API_ROOT` 和 `BSPPLUS_APP_CODE`。
- 当前本地 `backend/.env` 未看到这两个变量名。

风险：

- 未配置时会使用默认 `http://localhost:8080` 和 `app_test1`。

状态：待确认。

## P1 功能一致性

### 4. 修正文档中的 Bspplus 角色映射说明

现状：

- 文档写 `AUDITOR -> auditor`、`PM -> pm` 等。
- 当前代码实际映射为 `admin`、`manager`、`user`、`employee`。

建议：

- 更新 `docs/Bspplus用户体系调整说明.md`。

状态：待处理。

### 5. 统一短信接口成功响应字段说明

现状：

- 代码判断 `code == "200"`。
- 部分文档描述 `state == "200"` 且 `error` 为空。

建议：

- 根据真实短信接口响应确认规则。
- 同步更新代码或文档。

状态：待确认。

### 6. 补充 `task_reopened` 通知类型

现状：

- 任务退回修改时创建 `notification_type='task_reopened'`。
- `Notification.NOTIFICATION_TYPE_CHOICES` 未声明该值。

建议：

- 若该类型是正式业务事件，应补充 choices 和迁移。
- 若不是正式事件，应改用已有通知类型。

状态：待确认。

### 7. 梳理用户管理入口

现状：

- 后端提供用户管理接口和 Django Admin。
- PC 前端存在 `UserList.jsx`，但未接入主路由。

建议：

- 确认用户管理是否只在 Django Admin 中使用。
- 若要在 PC 端使用，补充路由、菜单和权限。

状态：待确认。

## P2 前端与小程序

### 8. 完善小程序登录态校验

现状：

- `frontend-miniprogram/app.js` 中 `checkToken` 为 TODO。
- 首页依赖 `globalData.userInfo`，应用重启后可能丢失。

建议：

- 使用 storage 中 token 请求当前用户接口。
- token 失效时跳转登录。

状态：待处理。

### 9. 补齐小程序 tabBar 图标

现状：

- `app.json` 引用 `images/home.png`、`images/home-active.png`、`images/task.png`、`images/task-active.png`。
- 当前未发现 `frontend-miniprogram/images` 目录。

状态：待处理。

### 10. 实现或删减小程序文档中的未落地功能

现状：

- 文档称小程序支持完整任务流程、通知、个人信息等。
- 当前代码只体现登录、任务列表、详情和附件相关能力。

建议：

- 若计划实现，拆分小程序任务流程操作页面。
- 若不计划实现，修正文档描述。

状态：待确认。

### 11. 清理 PC 前端调试日志

现状：

- `frontend-pc/src/pages/MaintenanceReport.jsx` 有多处 `console.log`。

建议：

- 生产构建前删除或按环境控制。

状态：待处理。

## P3 文档与工程质量

### 12. 统一部署验证命令

现状：

- 部署文档部分位置建议 `curl /api/`。
- 排障文档说明 `/api/` 根路径 404 正常。

建议：

- 统一改为验证具体接口，例如 `/api/auth/login/` 或 `/admin/`。

状态：待处理。

### 13. 梳理附件存储路径

现状：

- 附件存入 `docs/YYYY/MM/DD/`。
- `docs/` 同时存放项目文档。

建议：

- 待确认是否继续使用当前设计。
- 如迁移到独立目录，需考虑历史附件兼容和 Nginx 配置。

状态：待确认。

### 14. 增加自动化测试

现状：

- 未发现明显后端单元测试、接口测试或前端测试体系。

建议：

- 优先覆盖任务流程状态流转。
- 覆盖角色权限。
- 覆盖运维记录创建/更新/附件。
- 覆盖 Bspplus 登录回退逻辑。

状态：待处理。

### 15. 更新 README 和系统说明

现状：

- README 和 `系统说明.md` 未完整体现运维记录、短信、Bspplus、附件等当前实现。

建议：

- 基于真实代码补充当前功能。
- 将小程序未完成部分标记为开发中。

状态：待处理。

