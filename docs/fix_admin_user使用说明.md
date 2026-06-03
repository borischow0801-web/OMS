# oms_admin用户一键修复脚本使用说明

## 脚本位置
`backend/scripts/fix_admin_user.py`

## 使用方法

### 方法1：直接执行（推荐）

```bash
cd /opt/OMS/backend  # 或 /home/zxy_8581/OMS/backend（根据实际路径）
source venv/bin/activate
python scripts/fix_admin_user.py
```

### 方法2：使用完整路径

```bash
/path/to/OMS/backend/venv/bin/python /path/to/OMS/backend/scripts/fix_admin_user.py
```

## 脚本功能

1. **检查用户状态**：检查 `oms_admin` 用户是否存在及其当前状态
2. **自动修复**：
   - 如果用户没有密码，会提示设置密码
   - 如果用户缺少 `is_staff` 权限，自动设置
   - 如果用户缺少 `is_superuser` 权限，自动设置
   - 如果用户 `is_active=False`，自动设置为 `True`
3. **创建用户**：如果用户不存在，可以选择创建新用户

## 执行流程

1. 脚本会自动检查 `oms_admin` 用户
2. 显示当前用户状态（密码、权限等）
3. 如果发现问题，会提示是否修复
4. 如果需要设置密码，会提示输入新密码
5. 修复完成后显示最终状态

## 示例输出

### 正常情况（无需修复）
```
============================================================
OMS后台管理员用户修复脚本
============================================================

✅ 找到用户: oms_admin

------------------------------------------------------------
当前用户状态:
------------------------------------------------------------
用户名: oms_admin
邮箱: admin@example.com
是否有可用密码: ✅ 是
is_staff: ✅ True
is_superuser: ✅ True
is_active: ✅ True

✅ 用户配置正常，无需修复

可以正常登录后台: http://59.224.25.175:2080/admin/login/
```

### 需要修复的情况
```
============================================================
OMS后台管理员用户修复脚本
============================================================

✅ 找到用户: oms_admin

------------------------------------------------------------
当前用户状态:
------------------------------------------------------------
用户名: oms_admin
邮箱: (未设置)
是否有可用密码: ❌ 否
is_staff: ❌ False
is_superuser: ❌ False
is_active: ✅ True

⚠️  需要修复: 密码, is_staff权限, is_superuser权限

是否继续修复？(y/n): y

------------------------------------------------------------
开始修复...
------------------------------------------------------------
设置密码...
请输入新密码: 
请确认密码: 
✅ 密码已设置
✅ 已设置 is_staff=True
✅ 已设置 is_superuser=True

============================================================
✅ 修复完成！
============================================================

修复后的用户状态:
  用户名: oms_admin
  有密码: ✅ 是
  is_staff: ✅ True
  is_superuser: ✅ True
  is_active: ✅ True

现在可以使用以下信息登录后台:
  地址: http://59.224.25.175:2080/admin/login/
  用户名: oms_admin
  密码: (刚才设置的密码)
```

## 注意事项

1. **密码输入**：输入密码时不会显示字符（安全考虑）
2. **权限确认**：脚本会显示需要修复的内容，确认后再执行
3. **用户创建**：如果用户不存在，可以选择创建新用户
4. **安全性**：脚本只修复 `oms_admin` 用户，不会影响其他用户

## 故障排查

### 如果脚本无法执行

1. **检查Python环境**：
   ```bash
   which python
   # 或
   which python3
   ```

2. **检查虚拟环境**：
   ```bash
   source venv/bin/activate
   which python
   ```

3. **检查Django设置**：
   ```bash
   python manage.py shell
   # 如果能进入shell，说明Django配置正常
   ```

### 如果修复后仍无法登录

1. **检查用户状态**：
   ```bash
   python manage.py shell
   ```
   ```python
   from apps.accounts.models import User
   user = User.objects.get(username='oms_admin')
   print(f"有密码: {user.has_usable_password()}")
   print(f"is_staff: {user.is_staff}")
   print(f"is_superuser: {user.is_superuser}")
   ```

2. **检查CSRF配置**：
   - 确认浏览器Cookie正常
   - 清除浏览器缓存后重试
   - 检查Django的CSRF中间件配置

3. **查看日志**：
   ```bash
   tail -f /var/log/oms/django.log  # 根据实际日志路径
   ```

## 相关文件

- 脚本文件：`backend/scripts/fix_admin_user.py`
- 说明文档：`docs/fix_admin_user使用说明.md`（本文件）
