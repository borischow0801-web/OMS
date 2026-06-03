# Nginx配置问题分析与修复

## 当前配置分析

查看您提供的 Nginx 配置文件，发现以下**潜在问题**：

### 问题1：缺少CORS头配置
虽然前端和后端通过 Nginx 代理在同一域名下，但在以下情况下仍可能出现跨域问题：
- 浏览器发送 OPTIONS 预检请求时
- 请求包含自定义头（如 `Authorization: Bearer token`）
- 某些浏览器安全策略

### 问题2：缺少OPTIONS请求处理
当浏览器发送预检请求（OPTIONS）时，Nginx 需要正确处理并返回适当的 CORS 头。

### 问题3：缺少必要的头信息转发
虽然配置了基本的代理头，但可能缺少 `Origin` 等头信息的处理。

## 修复后的Nginx配置

以下是修复后的完整配置（`/etc/nginx/conf.d/oms.conf`）：

```nginx
# 后端API服务
upstream oms_backend {
    server 127.0.0.1:8000;
}

# 前端静态文件服务
server {
    listen 80;
    server_name _;  # 使用 _ 表示匹配所有域名，或填写具体域名/IP

    # 增加客户端请求体大小限制（用于文件上传）
    client_max_body_size 100M;

    # 前端静态文件（根据实际路径调整）
    location / {
        root /opt/OMS/frontend-pc/dist;
        try_files $uri $uri/ /index.html;
        
        # 添加CORS头（虽然同域，但为了兼容性）
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
    }

    # Django 管理后台（需要在 /api 之前）
    location /admin {
        proxy_pass http://oms_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # 增加超时时间
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 后端API - 关键修复部分
    location /api {
        # 处理OPTIONS预检请求
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, PATCH, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
            add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
            add_header 'Access-Control-Max-Age' 1728000 always;
            add_header 'Content-Type' 'text/plain; charset=utf-8' always;
            add_header 'Content-Length' 0 always;
            return 204;
        }

        proxy_pass http://oms_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # 重要：转发Origin头，让Django能够正确识别请求来源
        proxy_set_header Origin $http_origin;
        
        # 增加超时时间
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 添加CORS响应头（虽然同域，但为了兼容性）
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, PATCH, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
    }

    # 静态文件缓存（根据实际路径调整）
    location /static {
        alias /opt/OMS/backend/staticfiles;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 媒体文件（根据实际路径调整）
    location /media {
        alias /opt/OMS/backend/media;
        expires 7d;
    }
}
```

## 关键修改说明

### 1. OPTIONS预检请求处理
```nginx
if ($request_method = 'OPTIONS') {
    # 返回CORS头并直接返回204
    return 204;
}
```
这确保浏览器发送的预检请求能够正确响应。

### 2. 转发Origin头
```nginx
proxy_set_header Origin $http_origin;
```
让后端Django能够识别请求的真实来源。

### 3. 添加CORS响应头
虽然前端和后端在同一域名下，但添加CORS头可以：
- 兼容某些浏览器的安全策略
- 处理可能的跨域场景
- 确保所有请求都能正常工作

### 4. 增加必要的代理头
```nginx
proxy_set_header X-Forwarded-Host $host;
proxy_set_header X-Forwarded-Port $server_port;
```
让后端能够正确识别请求的主机和端口。

## 应用修复步骤

### 步骤1：备份现有配置
```bash
sudo cp /etc/nginx/conf.d/oms.conf /etc/nginx/conf.d/oms.conf.backup.$(date +%Y%m%d_%H%M%S)
```

### 步骤2：编辑配置文件
```bash
sudo nano /etc/nginx/conf.d/oms.conf
```

将 `/api` 部分的配置替换为上面提供的修复版本。

### 步骤3：测试配置
```bash
sudo nginx -t
```

如果显示 `syntax is ok` 和 `test is successful`，说明配置正确。

### 步骤4：重新加载Nginx
```bash
sudo systemctl reload nginx
```

或者：
```bash
sudo nginx -s reload
```

## 验证修复

1. **检查Nginx状态**：
```bash
sudo systemctl status nginx
```

2. **测试API请求**：
```bash
# 测试OPTIONS预检请求
curl -X OPTIONS http://59.224.25.175:2080/api/auth/login/ \
  -H "Origin: http://59.224.25.175:2080" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  -v

# 应该返回204状态码和CORS头
```

3. **浏览器测试**：
   - 打开浏览器开发者工具（F12）
   - 切换到 Network 标签页
   - 尝试登录
   - 查看 `/api/auth/login/` 请求：
     - 如果有 OPTIONS 请求，应该返回 204
     - POST 请求应该返回 200 或 401（不是 403）

## 如果仍然无法登录

如果修复 Nginx 配置后仍然无法登录，请同时检查：

1. **后端 `.env` 配置**（必须同时修复）：
```env
ALLOWED_HOSTS=localhost,127.0.0.1,172.29.91.61,59.224.25.175
CORS_ALLOWED_ORIGINS=http://59.224.25.175:2080,http://172.29.91.61:80
```

2. **重启后端服务**：
```bash
sudo systemctl restart gunicorn
# 或
sudo supervisorctl restart oms_backend
```

3. **检查后端日志**：
```bash
# 查看Gunicorn日志
sudo journalctl -u gunicorn -f

# 或查看应用日志
tail -f /opt/OMS/backend/logs/*.log
```

## 注意事项

1. **生产环境安全**：当前配置使用 `Access-Control-Allow-Origin: *`，这在生产环境中可能不够安全。如果只允许特定域名访问，可以改为：
```nginx
add_header 'Access-Control-Allow-Origin' 'http://59.224.25.175:2080' always;
```

2. **路径确认**：确保配置中的路径正确：
   - 前端路径：`/opt/OMS/frontend-pc/dist`
   - 后端静态文件：`/opt/OMS/backend/staticfiles`
   - 媒体文件：`/opt/OMS/backend/media`

3. **端口映射**：如果云中心做了端口映射（内网80端口映射到公网2080端口），确保：
   - Nginx 监听内网80端口（当前配置正确）
   - 后端 `.env` 中的 `CORS_ALLOWED_ORIGINS` 包含公网地址

## 完整修复清单

- [ ] 修改 Nginx 配置，添加 OPTIONS 处理和 CORS 头
- [ ] 测试 Nginx 配置语法
- [ ] 重新加载 Nginx
- [ ] 修改后端 `.env` 文件（ALLOWED_HOSTS 和 CORS_ALLOWED_ORIGINS）
- [ ] 重启后端服务
- [ ] 清除浏览器缓存
- [ ] 测试登录功能

完成以上所有步骤后，登录问题应该能够解决。

