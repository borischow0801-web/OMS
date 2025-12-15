# 后端 API 测试方法

## 重要说明

**`/api/` 返回 404 是正常的！** 后端没有定义这个根路径，只有具体的子路径。

## 正确的测试方法

### 1. 测试登录接口（最可靠的测试）

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"你的管理员用户名","password":"你的密码"}'
```

**预期结果判断**：
- ✅ **返回 200 + JSON（包含 access token）** → 后端完全正常
- ✅ **返回 400 或 401（错误信息）** → 后端正常，只是用户名/密码错误或需要参数
- ❌ **返回 404** → 后端路径配置有问题
- ❌ **连接被拒绝** → 后端服务未启动

### 2. 测试管理员后台

```bash
curl http://127.0.0.1:8000/admin/
```

**预期结果**：
- ✅ 返回 HTML 页面（Django 管理后台登录页）→ 后端正常
- ❌ 返回 404 → 后端有问题

### 3. 测试其他接口（需要认证）

```bash
# 先获取 token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"你的用户名","password":"你的密码"}' | \
  grep -o '"access":"[^"]*' | cut -d'"' -f4)

# 测试用户列表接口
curl http://127.0.0.1:8000/api/accounts/users/ \
  -H "Authorization: Bearer $TOKEN"

# 测试任务列表接口
curl http://127.0.0.1:8000/api/tasks/tasks/ \
  -H "Authorization: Bearer $TOKEN"
```

## 完整诊断脚本

在生产环境服务器上运行：

```bash
#!/bin/bash

echo "=== 后端服务诊断 ==="
echo ""

echo "1. 检查后端服务状态："
sudo systemctl status oms-backend | head -5
echo ""

echo "2. 检查端口监听："
netstat -tlnp | grep 8000 || echo "端口 8000 未监听！"
echo ""

echo "3. 测试登录接口："
RESPONSE=$(curl -s -w "\nHTTP状态码: %{http_code}" -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}')
echo "$RESPONSE"
echo ""

echo "4. 测试管理员后台："
ADMIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/admin/)
echo "HTTP状态码: $ADMIN_CODE"
if [ "$ADMIN_CODE" = "200" ]; then
    echo "✅ 管理员后台可访问"
elif [ "$ADMIN_CODE" = "404" ]; then
    echo "❌ 管理员后台返回 404"
else
    echo "⚠️  管理员后台返回: $ADMIN_CODE"
fi
echo ""

echo "5. 查看后端日志（最后 10 行）："
sudo journalctl -u oms-backend.service -n 10 --no-pager
echo ""

echo "6. 查看 Nginx 错误日志（最后 5 行）："
sudo tail -n 5 /var/log/nginx/error.log 2>/dev/null || echo "无法读取 Nginx 错误日志"
```

保存为 `test_backend.sh`，然后运行：

```bash
chmod +x test_backend.sh
./test_backend.sh
```

## 常见错误及解决方案

### 错误 1：连接被拒绝

```
curl: (7) Failed to connect to 127.0.0.1 port 8000: Connection refused
```

**原因**：后端服务未启动

**解决**：
```bash
sudo systemctl start oms-backend
sudo systemctl status oms-backend
```

### 错误 2：404 Not Found

```
{"detail":"Not found."}
```

**原因**：路径不正确或后端路由配置问题

**解决**：
- 检查路径是否正确（注意末尾的斜杠）
- 查看后端日志：`sudo journalctl -u oms-backend.service -n 50`

### 错误 3：500 Internal Server Error

**原因**：后端代码错误或数据库连接问题

**解决**：
```bash
# 查看详细错误日志
sudo journalctl -u oms-backend.service -n 100

# 检查数据库连接
cd /opt/OMS/backend
source venv/bin/activate
python manage.py check --database default
```

## 判断后端是否正常的标准

### ✅ 后端正常的标准

1. **服务状态**：`sudo systemctl status oms-backend` 显示 `active (running)`
2. **端口监听**：`netstat -tlnp | grep 8000` 显示进程在监听
3. **登录接口**：访问 `/api/auth/login/` 返回 400/401（参数错误），而不是 404
4. **管理员后台**：访问 `/admin/` 返回 HTML 页面，不是 404

### ❌ 后端有问题的标志

1. 服务状态不是 `active (running)`
2. 端口 8000 未监听
3. 所有接口都返回 404
4. 连接被拒绝

## 总结

- **`/api/` 返回 404 是正常的**，因为路径未定义
- **应该测试具体端点**，如 `/api/auth/login/` 和 `/admin/`
- **如果具体端点也返回 404**，说明后端有问题
- **如果具体端点返回其他错误（如 401）**，说明后端正常，只是需要认证或参数

## 下一步

如果后端测试正常，问题可能在：
1. Nginx 配置（代理设置）
2. 前端 API 配置（API 地址）
3. CORS 配置（跨域问题）

请继续按照排查文档的其他步骤进行检查。

