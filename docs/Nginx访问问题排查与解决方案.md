# Nginx 访问问题排查与解决方案

## 问题描述

访问 `http://localhost` 或 `http://服务器IP` 时，显示的是 Nginx 欢迎页面，而不是应用前端页面。

## 问题原因

Nginx 默认配置文件还在生效，优先级高于我们的自定义配置。需要禁用或删除默认配置。

## 解决方案

### 方案一：禁用默认配置（推荐）

#### Ubuntu/Debian 系统

```bash
# 1. 查看已启用的配置
ls -la /etc/nginx/sites-enabled/

# 2. 删除默认配置的符号链接
sudo rm /etc/nginx/sites-enabled/default

# 3. 测试配置
sudo nginx -t

# 4. 重载 Nginx
sudo systemctl reload nginx
```

#### CentOS/RHEL/麒麟系统

```bash
# 1. 查看默认配置文件
ls -la /etc/nginx/conf.d/

# 2. 重命名或删除默认配置文件
sudo mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak
# 或者直接删除
# sudo rm /etc/nginx/conf.d/default.conf

# 3. 测试配置
sudo nginx -t

# 4. 重载 Nginx
sudo systemctl reload nginx
```

### 方案二：确保自定义配置优先级更高

如果不想删除默认配置，可以修改自定义配置的监听端口或使用不同的 server_name。

## 完整排查步骤

### 步骤 1：检查当前生效的配置

```bash
# 查看所有 Nginx 配置
sudo nginx -T

# 查看配置测试结果
sudo nginx -t

# 查看正在运行的配置
ps aux | grep nginx
```

### 步骤 2：检查配置文件位置

#### Ubuntu/Debian 系统

```bash
# 查看 sites-enabled 目录（已启用的配置）
ls -la /etc/nginx/sites-enabled/

# 查看 sites-available 目录（所有可用配置）
ls -la /etc/nginx/sites-available/

# 查看主配置文件
cat /etc/nginx/nginx.conf
```

#### CentOS/RHEL/麒麟系统

```bash
# 查看 conf.d 目录（所有配置）
ls -la /etc/nginx/conf.d/

# 查看主配置文件
cat /etc/nginx/nginx.conf
```

### 步骤 3：确认自定义配置文件存在且正确

```bash
# 检查自定义配置文件是否存在
ls -la /etc/nginx/conf.d/oms.conf  # CentOS/RHEL/麒麟
# 或
ls -la /etc/nginx/sites-available/oms  # Ubuntu/Debian

# 查看配置文件内容
cat /etc/nginx/conf.d/oms.conf
```

### 步骤 4：禁用默认配置

根据你的系统类型选择对应的方法（见上方方案一）。

### 步骤 5：验证配置

```bash
# 测试配置语法
sudo nginx -t

# 如果测试通过，重载配置
sudo systemctl reload nginx

# 检查 Nginx 状态
sudo systemctl status nginx

# 查看错误日志（如果有问题）
sudo tail -f /var/log/nginx/error.log
```

### 步骤 6：测试访问

```bash
# 在服务器上测试
curl http://localhost

# 或通过浏览器访问
# http://你的服务器IP
```

## 访问地址说明

### 通过 Nginx 代理后的访问地址

假设你的生产环境 IP 地址是 `172.29.91.61`：

#### 前端访问地址

```
http://172.29.91.61
```

或者如果有域名：
```
http://你的域名
```

#### 后端 API 访问地址

```
http://172.29.91.61/api
```

**注意**：
- 后端 API 通过 `/api` 路径访问，由 Nginx 代理到后端服务
- 不需要直接访问 `http://172.29.91.61:8000`（该端口只在内网监听）

### 完整的访问地址列表

| 服务类型 | 访问地址 | 说明 |
|---------|---------|------|
| **前端页面** | `http://172.29.91.61` | 通过 Nginx 访问前端静态文件 |
| **后端 API** | `http://172.29.91.61/api` | 通过 Nginx 代理访问后端 API |
| **后端静态文件** | `http://172.29.91.61/static/...` | Django 静态文件 |
| **媒体文件** | `http://172.29.91.61/media/...` | 上传的附件等媒体文件 |
| **后端直接访问** | `http://127.0.0.1:8000` | 仅服务器本地访问（不对外） |

### 示例 API 请求

```bash
# 登录接口
POST http://172.29.91.61/api/accounts/login/

# 获取任务列表
GET http://172.29.91.61/api/tasks/tasks/

# 管理后台（如果有）
GET http://172.29.91.61/api/admin/
```

## 完整配置文件示例（麒麟V10）

确保 `/etc/nginx/conf.d/oms.conf` 内容如下（根据实际路径调整）：

```nginx
# 后端API服务
upstream oms_backend {
    server 127.0.0.1:8000;
}

# 前端静态文件服务
server {
    listen 80;
    server_name _;  # 匹配所有域名/IP

    # 前端静态文件
    location / {
        root /opt/OMS/frontend-pc/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # 后端API
    location /api {
        proxy_pass http://oms_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 增加超时时间（可选）
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件缓存
    location /static {
        alias /opt/OMS/backend/staticfiles;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 媒体文件
    location /media {
        alias /opt/OMS/backend/media;
        expires 7d;
    }
}
```

## 常见问题排查

### Q1: 仍然显示欢迎页面

**排查步骤**：
1. 确认默认配置已禁用：`ls -la /etc/nginx/conf.d/default.conf*`
2. 检查配置文件语法：`sudo nginx -t`
3. 查看所有配置：`sudo nginx -T | grep -A 10 "server {"`
4. 检查是否有多个 server 块监听 80 端口
5. 清除浏览器缓存后重试

### Q2: 显示 404 Not Found

**排查步骤**：
1. 检查前端文件是否存在：`ls -la /opt/OMS/frontend-pc/dist/`
2. 确认是否执行了 `npm run build`
3. 检查文件权限：`sudo -u nginx ls /opt/OMS/frontend-pc/dist`
4. 查看 Nginx 错误日志：`sudo tail -f /var/log/nginx/error.log`

### Q3: 显示 502 Bad Gateway

**排查步骤**：
1. 检查后端服务是否运行：`sudo systemctl status oms-backend`
2. 检查后端是否监听在 8000 端口：`netstat -tlnp | grep 8000`
3. 查看后端日志：`sudo journalctl -u oms-backend.service -n 50`
4. 查看 Nginx 错误日志：`sudo tail -f /var/log/nginx/error.log`

### Q4: 前端可以访问，但 API 请求失败

**排查步骤**：
1. 检查后端服务状态：`sudo systemctl status oms-backend`
2. 直接测试后端 API：`curl http://127.0.0.1:8000/api/`
3. 检查后端日志：`sudo journalctl -u oms-backend.service -f`
4. 检查 CORS 配置（后端 settings.py）
5. 检查 ALLOWED_HOSTS 配置（后端 .env 文件）

## 验证步骤清单

完成配置后，按以下步骤验证：

- [ ] 默认配置文件已禁用或删除
- [ ] 自定义配置文件存在且语法正确
- [ ] `sudo nginx -t` 测试通过
- [ ] Nginx 已重载配置
- [ ] 前端静态文件目录存在且有读取权限
- [ ] 后端服务正在运行
- [ ] 可以访问 `http://172.29.91.61` 看到前端页面
- [ ] 可以访问 `http://172.29.91.61/api/` 看到 API 响应

## 生产环境配置检查清单

### 后端配置检查

1. **检查 .env 文件中的 ALLOWED_HOSTS**：
   ```
   ALLOWED_HOSTS=172.29.91.61,localhost,127.0.0.1
   ```

2. **检查 CORS 配置**：
   ```
   CORS_ALLOWED_ORIGINS=http://172.29.91.61
   ```

3. **检查 DEBUG 设置**：
   ```
   DEBUG=False
   ```

### 前端配置检查

1. **检查 API 基础 URL**：
   前端构建时应该已经配置了正确的 API 地址
   或者前端代码中应该有环境变量配置

### Nginx 配置检查

1. **检查监听端口**：`listen 80;`
2. **检查 server_name**：`server_name _;` 或具体域名/IP
3. **检查文件路径**：确保所有路径都是绝对路径且存在
4. **检查文件权限**：确保 Nginx 用户可以读取文件

## 总结

1. **问题原因**：Nginx 默认配置还在生效
2. **解决方法**：禁用或删除默认配置文件
3. **访问地址**：
   - 前端：`http://172.29.91.61`
   - 后端 API：`http://172.29.91.61/api`
4. **验证方法**：访问 `http://172.29.91.61` 应该看到应用前端页面，而不是 Nginx 欢迎页面

