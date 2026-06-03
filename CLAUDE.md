# OMS 项目接管文档 (CLAUDE.md)

> 信息化软件项目运维管理系统 —— 已上线存量系统

---

## 项目概述

本系统是一个多角色、多端的运维任务管理平台，支持：
- PC 端 Web（React 18 + Ant Design）
- 微信小程序
- Django REST API 后端

四种用户角色：
| 角色 | 说明 |
|------|------|
| `user`（使用方） | 提交工单、确认完成 |
| `admin`（管理方） | 审核工单、分配任务 |
| `manager`（承建方-项目经理） | 指派工程师 |
| `employee`（承建方-员工） | 处理工单 |

---

## 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | Django 4.2 + DRF 3.14 |
| 数据库 | MySQL 8.0（连接用 Unix socket `/data/mysql/mysqld.sock`） |
| 缓存 | Redis 6.0 |
| 认证 | JWT（simplejwt），Access 60分钟，Refresh 24小时 |
| SSO | Bspplus 单点登录（有本地鉴权兜底） |
| 前端 PC | React 18 + Vite 5 + Ant Design 5 + Zustand |
| 前端移动 | 微信小程序 |
| 生产服务器 | Gunicorn + Nginx |
| 依赖管理 | python-decouple（从 `.env` 读取配置） |

---

## 目录结构

```
/app/OMS/
├── backend/                    # Django 后端
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env                    # 敏感配置（不进 git）
│   ├── oms_backend/
│   │   ├── settings.py         # 核心配置
│   │   ├── urls.py             # 主路由
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── accounts/           # 用户管理、认证、SSO
│   │   ├── tasks/              # 工单核心模块
│   │   ├── workflow/           # 流程日志、通知、短信
│   │   └── maintenance/        # 运维记录模块
│   ├── scripts/                # 运维脚本（诊断/修复账号等）
│   └── staticfiles/            # collectstatic 输出
├── frontend-pc/                # React PC 前端
│   ├── src/
│   │   ├── App.jsx             # 路由配置（含角色路由守卫）
│   │   ├── api/                # Axios 请求封装
│   │   ├── store/authStore.js  # JWT + 用户信息状态
│   │   ├── pages/              # 页面组件
│   │   └── components/         # 公共组件
│   ├── vite.config.js          # 开发代理：/api -> localhost:8000
│   ├── .env.local              # 生产环境 API 地址
│   └── dist/                   # 构建输出（Nginx 静态文件目录）
├── frontend-miniprogram/       # 微信小程序
└── docs/                       # 部署文档、Nginx 配置示例、排查手册
```

---

## 启动命令

### 后端（开发环境）

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 确保 .env 文件存在并配置正确
python manage.py migrate
python manage.py runserver
# 访问 http://localhost:8000
# Django Admin: http://localhost:8000/admin
```

### 前端 PC（开发环境）

```bash
cd frontend-pc
npm install
npm run dev
# 访问 http://localhost:3000（代理 /api 到 localhost:8000）
```

### 前端构建（生产）

```bash
cd frontend-pc
npm run build
# 输出到 dist/，由 Nginx 托管
```

---

## 数据库相关

- 引擎：MySQL 8.0，字符集 utf8mb4
- **生产环境使用 Unix socket 连接**：`/data/mysql/mysqld.sock`（在 `settings.py` 硬编码）
- 若本地开发无该 socket，需在 settings.py `DATABASES.OPTIONS` 中注释掉 `unix_socket` 行

```bash
# 常用 migration 命令
python manage.py makemigrations
python manage.py migrate

# 创建初始管理员
python manage.py createsuperuser
```

**数据库名**：`oms_db`  
**数据库用户**：`oms_user`（密码在 `.env` 中）

---

## 环境变量说明（backend/.env）

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `DEBUG` | 调试模式，**生产必须为 False** | `True` |
| `SECRET_KEY` | Django 密钥，**生产必须更换** | `ha3cg=y0du)...` |
| `ALLOWED_HOSTS` | 允许访问的主机，逗号分隔 | `localhost,10.217.19.22` |
| `DATABASE_NAME` | 数据库名 | `oms_db` |
| `DATABASE_USER` | 数据库用户 | `oms_user` |
| `DATABASE_PASSWORD` | 数据库密码 | `Oms_789*zxY` |
| `DATABASE_HOST` | 数据库主机 | `localhost` |
| `DATABASE_PORT` | 数据库端口 | `3306` |
| `REDIS_HOST` | Redis 主机 | `localhost` |
| `REDIS_PORT` | Redis 端口 | `6379` |
| `REDIS_DB` | Redis DB 编号 | `0` |
| `JWT_ACCESS_TOKEN_LIFETIME` | Access Token 有效期（分钟） | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME` | Refresh Token 有效期（分钟） | `1440` |
| `CORS_ALLOWED_ORIGINS` | 允许跨域的前端域名，逗号分隔 | `http://10.217.19.22:3000` |
| `BSPPLUS_API_ROOT` | Bspplus SSO API 地址 | `http://localhost:8080` |
| `BSPPLUS_APP_CODE` | Bspplus 应用代码 | `app_test1` |

前端配置（`frontend-pc/.env.local`）：
| 变量名 | 说明 |
|--------|------|
| `VITE_API_BASE_URL` | 后端 API 地址，如 `http://10.217.19.22:8000/api` |

---

## 核心模块与职责

### 1. `apps/accounts` — 用户与认证
- 自定义用户模型（继承 AbstractUser），扩展角色、手机、部门、地区字段
- 登录：先走 Bspplus SSO，失败兜底到本地 Django 认证
- Bspplus 角色映射：`AUDITOR→admin`，`PM→manager`，`REQUESTER→user`，`STAFF→employee`
- 支持 Excel 批量导入用户（`import_service.py`）
- 关键文件：`views.py`, `bspplus_service.py`, `models.py`, `serializers.py`

### 2. `apps/tasks` — 工单核心（最重要）
- 工单全生命周期管理，状态机：
  `draft → pending_review → reviewed → assigned → in_progress → completed → confirmed → closed`
- 支持评论、附件上传（`DateBasedFileStorage` 按日期归档，存在 `/app/OMS/docs/`）
- 角色权限严格，每个状态转换只有特定角色可操作
- 关键文件：`views.py`（781行，核心逻辑），`models.py`，`serializers.py`，`storage.py`

### 3. `apps/workflow` — 流程日志与通知
- `WorkflowLog`：记录每次状态变更（审计链）
- `Notification`：站内通知
- `SmsService`：异步发短信（用 threading），有防重发逻辑，支持多种模板
- 关键文件：`sms_service.py`，`models.py`

### 4. `apps/maintenance` — 运维记录
- 独立于工单的运维记录（11种问题类型、优先级、地区、处理人）
- 支持筛选、统计报表
- 关键文件：`views.py`，`models.py`

---

## 主要 API 路由

```
POST   /api/auth/login/                      登录（获取 JWT）
POST   /api/auth/refresh/                    刷新 Token

GET    /api/accounts/users/                  用户列表
GET    /api/accounts/users/me/               当前用户信息
POST   /api/accounts/users/change_password/  修改密码

GET    /api/tasks/tasks/                     工单列表
POST   /api/tasks/tasks/                     创建工单
GET    /api/tasks/tasks/{id}/                工单详情
POST   /api/tasks/tasks/{id}/review/         审核
POST   /api/tasks/tasks/{id}/assign/         分配
POST   /api/tasks/tasks/{id}/handle/         处理
POST   /api/tasks/tasks/{id}/confirm/        确认完成
POST   /api/tasks/tasks/{id}/add_comment/    添加评论
POST   /api/tasks/tasks/{id}/upload_attachment/  上传附件
POST   /api/tasks/tasks/{id}/download_attachment/ 下载附件

GET    /api/workflow/notifications/           通知列表
POST   /api/workflow/notifications/{id}/mark_read/ 标为已读

GET    /api/maintenance/records/             运维记录列表
POST   /api/maintenance/records/            创建运维记录
```

---

## 部署方式（生产）

参考详细文档：`docs/部署说明.md`

```bash
# 后端 Gunicorn
gunicorn oms_backend.wsgi:application \
  --bind unix:/run/oms/gunicorn.sock \
  --workers 3 \
  --error-logfile /var/log/oms/gunicorn-error.log

# 前端静态文件由 Nginx 托管
# Nginx 配置示例见：docs/nginx.conf.修改示例
# 静态文件目录：/opt/OMS/frontend-pc/dist/
# API 反代：/api/ -> Gunicorn socket
```

---

## 风险点与禁止随意改动的区域

### 高风险区域

| 区域 | 风险说明 |
|------|----------|
| `apps/tasks/views.py` | 工单状态机逻辑，状态转换和角色权限强耦合 |
| `apps/accounts/bspplus_service.py` | SSO 角色映射，改错会导致所有用户角色错乱 |
| `apps/workflow/sms_service.py` | 异步短信，threading 模型，需注意线程安全 |
| `backend/oms_backend/settings.py` 中 `DATABASES.OPTIONS` | `unix_socket` 硬编码，本地开发要注释掉，生产不能动 |
| `frontend-pc/src/store/authStore.js` | JWT 存储和刷新逻辑，牵连所有 API 调用 |
| `frontend-pc/src/App.jsx` | 路由守卫和角色权限路由，改错会造成权限穿透 |
| 数据库 migrations | 不能随意删除或回滚，线上有数据 |

### 注意事项

1. **附件存储路径**：附件存在 `ATTACHMENT_ROOT = BASE_DIR.parent/docs`，即 `/app/OMS/docs/`，不是 media 目录，下载接口走自定义路径，不走 Django media。
2. **生产调试模式**：`DEBUG=False` 时，`/docs/` 静态路径不会被注册（见 urls.py）；如果线上附件下载 404，优先检查 Nginx 是否配置了 `/docs/` 的 alias。
3. **CORS**：新增前端域名访问时，必须同时更新 `.env` 的 `CORS_ALLOWED_ORIGINS` 和 `settings.py` 的 `ALLOWED_HOSTS`。
4. **Bspplus 兜底**：Bspplus 不可用时系统会降级到本地认证，但角色信息可能不同步，需监控。
5. **短信防重发**：`SmsService` 有时间窗口内防重发逻辑，不要轻易修改判断条件。
6. **JWT Token 轮换**：`ROTATE_REFRESH_TOKENS=True`，Refresh Token 用一次就换新的，前端 `authStore.js` 有处理，不要改认证逻辑。

---

## 测试命令

```bash
# 后端（无正式测试套件，使用诊断脚本）
cd backend
python scripts/diagnose_login.py      # 诊断登录问题
python scripts/check_admin_access.py  # 检查管理员账号

# 前端（无正式测试套件）
cd frontend-pc
npm run build   # 构建检查是否有编译错误
```

---

## 新增功能时建议优先参考的文件

| 场景 | 参考文件 |
|------|----------|
| 新增 API 接口 | `apps/tasks/views.py`（最完整的 ViewSet 示例） |
| 新增模型/字段 | `apps/tasks/models.py` + 对应 migration |
| 新增角色权限控制 | `apps/tasks/views.py` 中的 permission_classes 和手动校验 |
| 新增前端页面 | `frontend-pc/src/pages/TaskDetail.jsx`（最复杂，含各种交互）|
| 新增 API 调用（前端） | `frontend-pc/src/api/tasks.js` + `api/index.js`（axios 实例） |
| 新增通知/短信 | `apps/workflow/sms_service.py` + `models.py` 中的 SmsTemplate |
| 新增运维统计 | `apps/maintenance/views.py` |

---

## 已知问题与历史记录

- 多份 Nginx 排查文档和登录问题文档（`docs/`）表明上线初期曾有：Nginx 配置错误（`/api/` 路由 404）、Django Admin 管理员访问异常、前端构建路径错误等问题，均已修复。
- 生产服务器 IP：`10.217.19.22`（出现在 `.env` 的 ALLOWED_HOSTS 和 CORS 配置中）。
- `apps/accounts/urls.py` 同时注册到 `/api/auth/` 和 `/api/accounts/`（见主 urls.py），两个前缀均可用。
