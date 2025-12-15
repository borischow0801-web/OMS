# Nginx 主配置文件问题解决方案

## 问题分析

根据你提供的主配置文件 `/etc/nginx/nginx.conf`，发现了以下问题：

### 问题 1：主配置文件中有默认 server 块

在主配置文件的 **38-54 行**，有一个默认的 server 块：

```nginx
server {
    listen       80;
    listen       [::]:80;
    server_name  _;
    root         /usr/share/nginx/html;  # 这就是显示欢迎页面的原因！

    # Load configuration files for the default server block.
    include /etc/nginx/default.d/*.conf;

    error_page 404 /404.html;
        location = /40x.html {
    }

    error_page 500 502 503 504 /50x.html;
        location = /50x.html {
    }
}
```

**问题说明**：
- 这个默认 server 块监听 80 端口，`server_name` 是 `_`（匹配所有域名）
- `root` 指向 `/usr/share/nginx/html`，这就是 Nginx 欢迎页面所在的位置
- 这个 server 块在主配置文件中，优先级可能高于 `conf.d` 目录中的配置
- 因为没有 `/api` 的 location 配置，所以 `http://localhost/api` 无法访问

### 问题 2：配置加载顺序

- 第 36 行：`include /etc/nginx/conf.d/*.conf;` - 加载 conf.d 目录中的配置
- 但是主配置文件中的 server 块已经在主配置中定义，会优先处理

## 解决方案

### 方案一：注释掉主配置文件中的默认 server 块（推荐）

需要修改 `/etc/nginx/nginx.conf` 文件，注释掉 38-54 行的默认 server 块。

**修改步骤**：

1. **备份原配置文件**（重要！）：
```bash
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak
```

2. **编辑主配置文件**：
```bash
sudo nano /etc/nginx/nginx.conf
```

3. **注释掉默认 server 块**（38-54 行）：

修改前：
```nginx
    include /etc/nginx/conf.d/*.conf;

    server {
        listen       80;
        listen       [::]:80;
        server_name  _;
        root         /usr/share/nginx/html;

        # Load configuration files for the default server block.
        include /etc/nginx/default.d/*.conf;

        error_page 404 /404.html;
            location = /40x.html {
        }

        error_page 500 502 503 504 /50x.html;
            location = /50x.html {
        }
    }
```

修改后：
```nginx
    include /etc/nginx/conf.d/*.conf;

    # 默认 server 块已禁用，使用 conf.d 中的自定义配置
    # server {
    #     listen       80;
    #     listen       [::]:80;
    #     server_name  _;
    #     root         /usr/share/nginx/html;
    #
    #     # Load configuration files for the default server block.
    #     include /etc/nginx/default.d/*.conf;
    #
    #     error_page 404 /404.html;
    #         location = /40x.html {
    #     }
    #
    #     error_page 500 502 503 504 /50x.html;
    #         location = /50x.html {
    #     }
    # }
```

4. **测试配置**：
```bash
sudo nginx -t
```

5. **如果测试通过，重载 Nginx**：
```bash
sudo systemctl reload nginx
```

### 方案二：删除默认 server 块（如果确定不需要）

如果你确定不需要默认配置，可以直接删除这部分内容：

```bash
# 备份
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak

# 编辑文件，删除 38-54 行的 server 块
sudo nano /etc/nginx/nginx.conf
```

## 完整修改后的主配置文件

以下是修改后的 `/etc/nginx/nginx.conf` 应该的样子（关键部分）：

```nginx
http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 4096;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    # Load modular configuration files from the /etc/nginx/conf.d directory.
    # See http://nginx.org/en/docs/ngx_core_module.html#include
    # for more information.
    include /etc/nginx/conf.d/*.conf;

    # 默认 server 块已禁用，使用 conf.d 中的自定义配置
    # 如果需要默认配置，请取消注释下面的 server 块
    # server {
    #     listen       80;
    #     listen       [::]:80;
    #     server_name  _;
    #     root         /usr/share/nginx/html;
    #
    #     include /etc/nginx/default.d/*.conf;
    #
    #     error_page 404 /404.html;
    #         location = /40x.html {
    #     }
    #
    #     error_page 500 502 503 504 /50x.html;
    #         location = /50x.html {
    #     }
    # }

    # Settings for a TLS enabled server.
    # ... (HTTPS 配置保持不变)
}
```

## 确认自定义配置文件存在

修改主配置后，确保自定义配置文件存在且正确：

```bash
# 检查配置文件是否存在
ls -la /etc/nginx/conf.d/oms.conf

# 查看配置文件内容
cat /etc/nginx/conf.d/oms.conf
```

配置文件内容应该类似这样：

```nginx
# 后端API服务
upstream oms_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;

    # 前端静态文件
    location / {
        root /opt/OMS/frontend-pc/dist;  # 根据实际路径调整
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
    }

    # 静态文件缓存
    location /static {
        alias /opt/OMS/backend/staticfiles;  # 根据实际路径调整
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 媒体文件
    location /media {
        alias /opt/OMS/backend/media;  # 根据实际路径调整
        expires 7d;
    }
}
```

## 完整操作步骤

在生产环境服务器上执行：

```bash
# 步骤 1：备份主配置文件
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak

# 步骤 2：编辑主配置文件
sudo nano /etc/nginx/nginx.conf

# 步骤 3：注释掉 38-54 行的默认 server 块（按上面的示例修改）

# 步骤 4：保存文件并退出编辑器

# 步骤 5：测试配置语法
sudo nginx -t

# 步骤 6：如果测试通过，重载 Nginx
sudo systemctl reload nginx

# 步骤 7：检查 Nginx 状态
sudo systemctl status nginx

# 步骤 8：测试访问
curl http://localhost
curl http://localhost/api/

# 步骤 9：查看错误日志（如果有问题）
sudo tail -f /var/log/nginx/error.log
```

## 验证步骤

修改完成后，进行以下验证：

1. **检查配置文件语法**：
   ```bash
   sudo nginx -t
   ```
   应该显示：`syntax is ok` 和 `test is successful`

2. **检查生效的配置**：
   ```bash
   sudo nginx -T | grep -A 5 "server {"
   ```
   应该只看到你的自定义配置，没有默认的 server 块

3. **测试访问**：
   ```bash
   # 测试前端页面
   curl http://localhost
   # 应该返回前端 HTML，而不是欢迎页面
   
   # 测试 API
   curl http://localhost/api/
   # 应该返回 API 响应或错误页面，而不是 404
   ```

4. **浏览器访问**：
   - `http://localhost` - 应该看到应用前端页面
   - `http://localhost/api/` - 应该看到 API 响应

## 常见问题排查

### Q1: 修改后仍然显示欢迎页面

**排查步骤**：
1. 确认主配置文件已保存修改
2. 确认已执行 `sudo nginx -t` 测试通过
3. 确认已执行 `sudo systemctl reload nginx`
4. 清除浏览器缓存后重试
5. 检查是否有其他配置文件冲突：
   ```bash
   sudo nginx -T | grep "server_name"
   ```

### Q2: API 仍然无法访问

**排查步骤**：
1. 检查后端服务是否运行：`sudo systemctl status oms-backend`
2. 检查后端是否监听在 8000 端口：`netstat -tlnp | grep 8000`
3. 直接测试后端：`curl http://127.0.0.1:8000/api/`
4. 查看 Nginx 错误日志：`sudo tail -f /var/log/nginx/error.log`
5. 查看后端日志：`sudo journalctl -u oms-backend.service -n 50`

### Q3: 配置测试失败

**如果 `sudo nginx -t` 报错**：
1. 检查语法错误的具体位置
2. 确认注释符号 `#` 正确
3. 确认大括号匹配
4. 查看错误提示中的行号

### Q4: 需要恢复默认配置

**如果修改后出现问题，可以恢复备份**：
```bash
sudo cp /etc/nginx/nginx.conf.bak /etc/nginx/nginx.conf
sudo nginx -t
sudo systemctl reload nginx
```

## 注意事项

1. **备份重要**：修改主配置文件前一定要备份
2. **路径确认**：确保自定义配置中的路径都是正确的绝对路径
3. **权限检查**：确保 Nginx 用户可以读取所有相关文件
4. **服务重启**：修改配置后必须重载或重启 Nginx

## 总结

**根本原因**：
- 主配置文件中的默认 server 块指向了 `/usr/share/nginx/html`（欢迎页面）
- 这个默认配置优先级高，覆盖了自定义配置

**解决方法**：
- 注释掉或删除主配置文件中的默认 server 块（38-54 行）
- 确保 `/etc/nginx/conf.d/oms.conf` 配置文件存在且正确
- 重载 Nginx 配置

**修改后效果**：
- `http://localhost` 显示应用前端页面
- `http://localhost/api` 可以正常访问后端 API

