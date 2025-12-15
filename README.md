# 信息化软件项目运维管理系统

## 项目简介

本系统是一个信息化软件项目运维管理系统，支持使用方、管理方、承建方三类用户协同工作，实现问题反馈、需求管理、任务指派、流程审核等功能。

## 技术栈

### 后端
- Django 4.2 + Django REST Framework
- JWT 认证 (Simple JWT)
- MySQL 数据库
- Redis 缓存

### 前端PC端
- React 18
- Ant Design 5
- Vite
- Zustand (状态管理)
- React Router

### 前端移动端
- 微信小程序

## 项目结构

```
OMS/
├── backend/                 # 后端服务
│   ├── oms_backend/         # Django项目配置
│   ├── apps/                # 应用模块
│   │   ├── accounts/        # 用户账户管理
│   │   ├── tasks/          # 任务管理
│   │   └── workflow/       # 工作流管理
│   ├── manage.py
│   └── requirements.txt
├── frontend-pc/             # PC端前端
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── pages/          # 页面
│   │   ├── api/            # API调用
│   │   ├── store/          # 状态管理
│   │   └── utils/          # 工具函数
│   └── package.json
├── frontend-miniprogram/    # 微信小程序
│   ├── pages/              # 页面
│   ├── utils/              # 工具函数
│   └── app.js             # 小程序入口
├── docs/                   # 文档
│   └── 部署说明.md
├── scripts/                # 部署脚本
└── README.md
```

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Redis 6.0+

### 安装步骤

详细的安装和部署说明请参考 [部署说明文档](docs/部署说明.md)

#### 1. 后端设置

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 文件配置数据库等信息
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

#### 2. 前端PC端设置

```bash
cd frontend-pc
npm install
cp .env.example .env.local
# 编辑 .env.local 配置API地址
npm run dev
```

#### 3. 微信小程序

使用微信开发者工具打开 `frontend-miniprogram` 目录，配置AppID后即可预览。

## 功能模块

### 用户管理
- 支持四种角色：使用方、管理方、承建方-项目经理、承建方-员工
- 用户注册、登录、权限管理
- 个人信息管理

### 任务管理
- **使用方**: 创建问题或需求任务，查看自己创建的任务，确认任务完成情况
- **管理方**: 审核使用方提交的任务，审核通过后提交给承建方，审核不通过可直接结单
- **承建方-项目经理**: 查看已审核通过的任务，分析任务并指派给员工，跟进任务处理进度
- **承建方-员工**: 查看指派给自己的任务，处理任务并提交完成，跟进使用方确认情况

### 工作流管理
- 任务状态流转：待审核 → 已审核 → 已指派 → 处理中 → 已完成 → 已确认 → 已结单
- 工作流日志记录
- 通知消息推送

### 评论沟通
- 任务评论功能
- 实时沟通交流

## API接口

详细的API接口说明请参考 [系统说明文档](系统说明.md)

## 开发说明

### 后端开发

```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

### 前端开发

```bash
cd frontend-pc
npm run dev
```

访问 http://localhost:3000

## 许可证

MIT License

