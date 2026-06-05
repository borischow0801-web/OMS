# AI_CONTEXT.md

本文档为 AI 助手快速理解项目上下文使用，内容基于当前仓库真实文件整理。未从生产环境验证的内容标记为“待确认”。

## 项目用途

项目名称：信息化软件项目运维管理系统。

系统用于使用方、管理方、承建方协同处理信息化软件项目中的问题、需求、任务流转和运维记录。

当前主要业务线：

1. 任务管理流程：创建、审核、指派、处理、完成、确认、结单。
2. 运维记录流程：承建方录入运维事件、附件、更新内容，并查看统计报告。
3. 通知与短信：任务流转时生成站内通知，并可按配置发送短信。
4. 用户与认证：本地用户体系叠加 Bspplus 统一认证同步。

## 技术栈

后端：

- Django 4.2.11
- Django REST Framework 3.14.0
- djangorestframework-simplejwt 5.3.1
- MySQL，`mysqlclient`
- Redis，`django-redis`
- Gunicorn
- requests
- openpyxl
- Pillow

PC 前端：

- React 18
- Vite 5
- Ant Design 5
- React Router 6
- Zustand
- Axios
- Ant Design Plots

移动端：

- 微信小程序原生项目

部署：

- Nginx
- Gunicorn
- MySQL
- Redis
- systemd
- HTTPS/合法域名用于小程序生产访问

## 主要模块

### accounts

路径：`backend/apps/accounts/`

功能：

- 自定义用户模型
- JWT 登录接口
- Bspplus 登录和用户同步
- 用户列表、当前用户信息
- 员工/承建方用户查询
- 修改密码
- Django Admin 用户管理
- Excel 批量导入用户

角色：

- `user`：使用方
- `admin`：管理方
- `manager`：承建方-项目经理
- `employee`：承建方-员工

待确认：

- 生产环境中 Bspplus 接口地址和应用编码是否已通过 `.env` 配置。
- 管理方业务角色是否同时拥有 Django `is_staff` 权限。

### tasks

路径：`backend/apps/tasks/`

功能：

- 任务创建和草稿
- 任务审核
- 任务指派和重新指派
- 设置协助员工
- 开始处理、完成、确认、退回修改
- 评论
- 附件上传、下载、删除
- 角色视角下的任务列表过滤

任务状态：

- `draft`：草稿
- `pending_review`：待审核
- `reviewed`：已审核
- `assigned`：已指派
- `in_progress`：处理中
- `completed`：已完成
- `confirmed`：已确认
- `closed`：已结单

任务类型：

- `problem`：问题
- `requirement`：需求

### workflow

路径：`backend/apps/workflow/`

功能：

- 工作流日志
- 站内通知
- 短信配置
- 短信模板
- 短信发送记录
- 短信发送服务

短信触发场景：

- 任务提交
- 审核通过
- 审核不通过
- 任务分配
- 任务完成
- 任务需要修改

待确认：

- 短信供应商实际响应字段。代码当前判断 `code == "200"`，部分文档描述为 `state == "200"`。

### maintenance

路径：`backend/apps/maintenance/`

功能：

- 运维记录增删改查
- 运维记录附件
- 更新内容明细
- 统计报表
- 按区划、问题类型、完成情况、优先级、处理人、日期过滤

权限：

- 仅 `manager` 和 `employee` 可访问运维记录。
- 创建时处理人默认为当前用户。
- 修改、删除和附件上传删除限制为记录创建者。

## 前端现状

### PC 前端

路径：`frontend-pc/`

已实现页面：

- 登录页
- 首页 Dashboard
- 任务列表
- 任务创建
- 任务详情
- 个人中心
- 运维记录列表
- 运维记录创建/编辑
- 运维记录详情
- 运维记录报告

存在但未接入主路由的页面：

- `frontend-pc/src/pages/UserList.jsx`

待确认：

- 用户管理页面是否计划在 PC 前端开放，还是仅通过 Django Admin 管理。

### 微信小程序

路径：`frontend-miniprogram/`

当前代码包含：

- 登录页
- 首页
- 任务列表
- 任务详情
- 附件上传/下载相关代码

未完成或待验证：

- token 有效性校验
- 首页统计 API
- tabBar 图标文件缺失
- 文档中描述的完整流程操作、通知、个人信息等功能未在当前代码中完整体现

## 数据库

数据库结构由 Django migrations 管理，未发现独立 SQL 建表脚本。

主要表：

- `users`
- `tasks`
- `comments`
- `task_attachments`
- `workflow_logs`
- `notifications`
- `sms_configs`
- `sms_templates`
- `sms_records`
- `maintenance_records`
- `maintenance_attachments`
- `maintenance_update_logs`

特殊情况：

- 附件文件通过自定义 storage 存到 `OMS/docs/YYYY/MM/DD/`。
- `MEDIA_ROOT` 仍存在，但任务和运维附件未使用常规 media 根目录。

## 部署摘要

开发环境：

- 后端：`backend` 目录运行 Django dev server，端口 8000。
- PC 前端：`frontend-pc` 目录运行 Vite dev server，端口 3000。
- 小程序：微信开发者工具导入 `frontend-miniprogram`。

生产环境：

- Gunicorn 运行 Django 后端。
- Nginx 托管 PC 前端静态文件。
- Nginx 代理 `/api` 到 Gunicorn。
- systemd 管理后端服务。
- 小程序需配置合法域名，生产建议 HTTPS/443。

待确认：

- 生产部署路径是 `/opt/OMS`、`/home/zxy_8581/OMS` 还是其他路径。
- 生产 Nginx 是否配置了附件目录 `/docs/` 的访问。

## 已知问题

1. README、系统说明和部分 docs 偏早期，不能完全代表当前代码。
2. `backend/oms_backend/settings.py` 中 MySQL `unix_socket` 硬编码，跨环境部署风险较高。
3. Bspplus 配置在当前 `.env` 中未显式出现。
4. 小程序功能仍不完整。
5. 小程序 tabBar 引用的图片目录不存在。
6. `Notification` 类型使用了 `task_reopened`，但模型 choices 未声明该值。
7. 部署文档有些地方用 `/api/` 根路径验证，但该路径 404 在当前项目中可能是正常现象。
8. PC 前端 `MaintenanceReport.jsx` 有调试 `console.log`。
9. 缺少明显自动化测试体系。

