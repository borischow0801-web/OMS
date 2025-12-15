# Nginx 配置问题解答

## 问题 1：sites-available 目录问题

### 问题描述
在麒麟V10系统配置 Nginx 时，发现 `/etc/nginx/sites-available` 目录不存在。

### 原因说明

**不同 Linux 发行版的 Nginx 配置方式不同**：

| 系统类型 | 配置文件位置 | 说明 |
|---------|------------|------|
| **Ubuntu/Debian** | `/etc/nginx/sites-available/`<br>`/etc/nginx/sites-enabled/` | 使用两个目录分离可用配置和已启用配置 |
| **CentOS/RHEL/麒麟** | `/etc/nginx/conf.d/` | 直接在此目录创建配置文件 |

### 解决方案（麒麟V10）

**不要创建 `sites-available` 目录！** 直接使用系统的标准配置目录：

#### 步骤 1：检查配置目录

```bash
# 查看 Nginx 配置目录结构
ls -la /etc/nginx/

# 查看 conf.d 目录
ls -la /etc/nginx/conf.d/
```

#### 步骤 2：创建配置文件

在 `/etc/nginx/conf.d/` 目录下创建配置文件，**文件名必须以 `.conf` 结尾**：

```bash
sudo nano /etc/nginx/conf.d/oms.conf
```

**重要**：
- ✅ **文件名**：`oms.conf`（必须有 `.conf` 扩展名）
- ✅ **路径**：`/etc/nginx/conf.d/oms.conf`
- ❌ **不要**创建 `sites-available` 目录
- ❌ **不要**创建符号链接到 `sites-enabled`

#### 步骤 3：配置文件内容

```nginx
# 后端API服务
upstream oms_backend {
    server 127.0.0.1:8000;
}

# 前端静态文件服务
server {
    listen 80;
    server_name _;  # 见问题2的说明

    # 前端静态文件（根据实际路径调整）
    location / {
        root /opt/OMS/frontend-pc/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端API
    location /api {
        proxy_pass http://oms_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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

#### 步骤 4：测试并启用配置

```bash
# 测试配置文件语法
sudo nginx -t

# 如果测试通过，重载 Nginx 配置
sudo systemctl reload nginx

# 查看 Nginx 状态
sudo systemctl status nginx
```

### Ubuntu/Debian vs CentOS/RHEL/麒麟对比

| 步骤 | Ubuntu/Debian | CentOS/RHEL/麒麟 |
|-----|--------------|-----------------|
| 创建配置文件 | `/etc/nginx/sites-available/oms` | `/etc/nginx/conf.d/oms.conf` |
| 文件名要求 | 无扩展名 | 必须有 `.conf` 扩展名 |
| 启用配置 | 创建符号链接：<br>`sudo ln -s /etc/nginx/sites-available/oms /etc/nginx/sites-enabled/` | 无需额外步骤，直接生效 |
| 测试配置 | `sudo nginx -t` | `sudo nginx -t` |
| 重载配置 | `sudo systemctl reload nginx` | `sudo systemctl reload nginx` |

## 问题 2：server_name 配置

### 问题描述
配置文件中的 `server_name your-domain.com;` 应该改为什么？

### 配置选项说明

`server_name` 用于指定 Nginx 应该响应哪个域名的请求。有以下几种配置方式：

#### 选项 1：匹配所有域名（推荐用于测试/内网）

```nginx
server_name _;
```

**适用场景**：
- ✅ 没有域名，只有 IP 地址访问
- ✅ 内网环境，使用 IP 访问
- ✅ 测试环境
- ✅ 多域名访问（接受任何域名）

**示例**：通过 `http://192.168.1.100` 或 `http://10.211.55.67` 访问

#### 选项 2：使用 IP 地址

```nginx
server_name 192.168.1.100;
```

**适用场景**：
- ✅ 固定 IP 地址访问
- ✅ 内网部署

**示例**：仅通过 `http://192.168.1.100` 访问

#### 选项 3：使用域名

```nginx
server_name oms.example.com;
```

**适用场景**：
- ✅ 有域名并已配置 DNS
- ✅ 生产环境

**示例**：通过 `http://oms.example.com` 访问

#### 选项 4：多个域名

```nginx
server_name oms.example.com www.oms.example.com;
```

**适用场景**：
- ✅ 需要同时支持多个域名

#### 选项 5：本地访问

```nginx
server_name localhost;
```

**适用场景**：
- ✅ 仅本地访问
- ⚠️ 不推荐生产环境使用

### 推荐配置

根据你的实际情况选择：

1. **如果没有域名，只有 IP**：
   ```nginx
   server_name _;
   ```
   然后通过 `http://你的服务器IP` 访问

2. **如果有域名**：
   ```nginx
   server_name oms.yourdomain.com;
   ```
   确保域名 DNS 已指向服务器 IP

3. **如果是内网环境**：
   ```nginx
   server_name _;
   ```
   或使用内网 IP：
   ```nginx
   server_name 10.211.55.67;
   ```

### 完整配置示例（麒麟V10）

假设：
- 项目路径：`/opt/OMS/`
- 服务器 IP：`192.168.1.100`
- 没有域名，使用 IP 访问

配置文件 `/etc/nginx/conf.d/oms.conf`：

```nginx
# 后端API服务
upstream oms_backend {
    server 127.0.0.1:8000;
}

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

## 验证配置

配置完成后，执行以下步骤验证：

```bash
# 1. 测试配置文件语法
sudo nginx -t

# 2. 如果测试通过，重载配置
sudo systemctl reload nginx

# 3. 检查 Nginx 状态
sudo systemctl status nginx

# 4. 查看错误日志（如果有问题）
sudo tail -f /var/log/nginx/error.log

# 5. 测试访问
curl http://localhost
# 或使用浏览器访问：http://你的服务器IP
```

## 常见问题

### Q1: 配置文件创建后不生效？
**A:** 检查：
1. 文件名是否以 `.conf` 结尾
2. 文件是否在 `/etc/nginx/conf.d/` 目录
3. 是否执行了 `sudo nginx -t` 测试
4. 是否执行了 `sudo systemctl reload nginx`

### Q2: 访问时出现 502 Bad Gateway？
**A:** 检查：
1. 后端服务是否正常运行：`sudo systemctl status oms-backend`
2. 后端是否监听在 `127.0.0.1:8000`：`netstat -tlnp | grep 8000`
3. 查看 Nginx 错误日志：`sudo tail -f /var/log/nginx/error.log`

### Q3: 前端页面显示 404？
**A:** 检查：
1. 前端静态文件目录是否存在：`ls -la /opt/OMS/frontend-pc/dist`
2. 是否执行了 `npm run build` 构建前端
3. Nginx 用户是否有读取权限：`sudo -u nginx ls /opt/OMS/frontend-pc/dist`

### Q4: 配置文件路径问题
**A:** 如果你的项目路径不是 `/opt/OMS/`，需要：
1. 查找实际路径：`find / -name "oms_backend" -type d 2>/dev/null`
2. 将配置文件中的所有路径替换为实际路径
3. 确保所有路径都是绝对路径，不能使用相对路径

## 总结

1. **麒麟V10系统**：直接在 `/etc/nginx/conf.d/` 创建 `oms.conf` 文件，不需要 `sites-available` 目录
2. **server_name**：如果只有 IP 访问，使用 `server_name _;`
3. **文件扩展名**：必须是 `.conf`
4. **路径配置**：根据实际项目路径调整所有路径配置

