# Bspplus用户同步流程排查指南

## 完整流程概览

```
前端登录请求 
  ↓
后端API入口 (POST /api/accounts/login/)
  ↓
CustomTokenObtainPairSerializer.validate()
  ↓
BspplusService.login() - 调用Bspplus接口
  ↓
BspplusService.sync_user_from_bspplus() - 同步用户信息
  ↓
_parse_role() - 解析角色
  ↓
数据库操作 (创建或更新用户)
  ↓
返回登录结果（包含用户信息和Token）
```

---

## 详细流程步骤

### 步骤1：前端登录请求

**API端点**：`POST /api/accounts/login/`

**请求体**：
```json
{
  "username": "zhouxiangyu",
  "password": "用户输入的密码"
}
```

**排查点**：
- [ ] 检查前端是否正确发送请求到 `/api/accounts/login/`
- [ ] 检查请求体是否包含 `username` 和 `password` 字段
- [ ] 检查网络请求是否成功（HTTP状态码）

---

### 步骤2：后端API入口

**文件**：`backend/apps/accounts/views.py`
**类**：`CustomTokenObtainPairSerializer`
**方法**：`validate(self, attrs)`

**代码位置**：第28-125行

**关键代码**：
```python
def validate(self, attrs):
    username = attrs.get('username')
    password = attrs.get('password')
    
    # 调用Bspplus登录接口
    bspplus_result = BspplusService.login(username, password)
```

**排查点**：
- [ ] 检查 `username` 和 `password` 是否正确获取
- [ ] 检查是否调用了 `BspplusService.login()`
- [ ] 检查 `bspplus_result` 的返回值结构

---

### 步骤3：调用Bspplus登录接口

**文件**：`backend/apps/accounts/bspplus_service.py`
**类**：`BspplusService`
**方法**：`login(cls, username, password)`

**代码位置**：第84-177行

**关键步骤**：

#### 3.1 构建请求参数
```python
api_root = settings.BSPPLUS_API_ROOT  # 从settings获取，如：http://172.29.91.36:9099
app_code = settings.BSPPLUS_APP_CODE  # 从settings获取
login_url = f"{api_root}/user/login"  # 完整URL：http://172.29.91.36:9099/user/login
```

**排查点**：
- [ ] 检查 `BSPPLUS_API_ROOT` 配置是否正确（检查 `.env` 文件或 `settings.py`）
- [ ] 检查 `BSPPLUS_APP_CODE` 配置是否正确
- [ ] 检查 `login_url` 是否正确拼接（应该类似：`http://172.29.91.36:9099/user/login`）

#### 3.2 密码加密
```python
# 如果密码已经是32位MD5字符串，则不重复加密
# 否则进行MD5加密
encrypted_password = hashlib.md5(password.encode('utf-8')).hexdigest()
```

**排查点**：
- [ ] 检查密码是否被正确加密（32位MD5字符串）
- [ ] 如果前端已经发送MD5加密的密码，检查是否重复加密

#### 3.3 发送HTTP请求
```python
payload = {
    'username': username,
    'password': encrypted_password,
    'appCode': app_code,
}

response = requests.post(
    login_url,
    json=payload,
    timeout=10,
    headers={'Content-Type': 'application/json'}
)
```

**排查点**：
- [ ] 检查请求URL是否可访问（可以手动测试：`curl -X POST http://172.29.91.36:9099/user/login -H "Content-Type: application/json" -d '{"username":"xxx","password":"xxx","appCode":"xxx"}'`）
- [ ] 检查请求是否超时（timeout=10秒）
- [ ] 检查网络连接是否正常
- [ ] 检查请求payload格式是否正确（JSON格式）

#### 3.4 解析响应
```python
result = response.json()

# 检查返回状态
if result.get('status') == 200 and result.get('data', {}).get('flag') is True:
    return {
        'success': True,
        'flag': True,
        'user': result.get('data', {}).get('user', {}),  # 用户信息在这里
        ...
    }
```

**排查点**：
- [ ] 检查HTTP响应状态码（应该是200）
- [ ] 检查响应JSON结构是否正确
- [ ] 检查 `result.get('status')` 是否等于 200
- [ ] 检查 `result.get('data', {}).get('flag')` 是否为 `True`
- [ ] **重点**：检查 `result.get('data', {}).get('user', {})` 是否包含用户信息

**预期的用户信息结构**（参考 `/home/zxy_8581/接口正常返回.txt`）：
```json
{
  "role": "ROLE_MAINTEN,PM,ROLE_SYSTEM",
  "name": "周翔宇",
  "username": "zhouxiangyu",
  "mobile": "15650114963",
  "organName": "威海市项目组",
  "regionName": "威海市",
  "email": "borischow0801@gmail.com",
  ...
}
```

---

### 步骤4：同步用户信息到数据库

**文件**：`backend/apps/accounts/views.py`
**代码位置**：第86-89行

**关键代码**：
```python
# 登录成功，获取Bspplus返回的用户信息
bspplus_user_data = bspplus_result.get('user', {})

# 获取或创建本地用户（同步执行，确保用户存在）
user = BspplusService.sync_user_from_bspplus(bspplus_user_data)
```

**排查点**：
- [ ] 检查 `bspplus_user_data` 是否包含完整的用户信息
- [ ] 检查 `bspplus_user_data` 是否包含 `username` 字段
- [ ] 检查 `bspplus_user_data` 是否包含 `role` 字段（格式：`"ROLE_MAINTEN,PM,ROLE_SYSTEM"`）
- [ ] 检查 `bspplus_user_data` 是否包含 `mobile` 字段（不是 `phone`）
- [ ] 检查 `bspplus_user_data` 是否包含 `name`、`organName`、`regionName`、`email` 字段

**快速验证脚本**：

使用Django管理命令快速验证Bspplus接口返回的用户信息：

```bash
# 进入项目backend目录
cd /opt/OMS/backend  # 或你的实际项目路径

# 激活虚拟环境（如果使用虚拟环境）
source venv/bin/activate

# 运行测试脚本
python manage.py test_bspplus_login <用户名> <密码>

# 示例：
python manage.py test_bspplus_login zhouxiangyu your_password

# 显示详细信息（包括完整的用户信息JSON）
python manage.py test_bspplus_login zhouxiangyu your_password --verbose
```

**脚本功能**：
- ✅ 检查Bspplus接口配置（BSPPLUS_API_ROOT、BSPPLUS_APP_CODE）
- ✅ 调用Bspplus登录接口
- ✅ 检查登录结果（success、flag）
- ✅ 检查用户信息中的所有关键字段
- ✅ **重点检查role字段是否存在**
- ✅ 测试角色解析逻辑
- ✅ 显示详细的测试报告

**脚本输出示例**：
```
================================================================================
Bspplus登录接口测试
================================================================================

步骤1：检查配置信息
  BSPPLUS_API_ROOT: http://172.29.91.36:9099
  BSPPLUS_APP_CODE: INSPUR-DZZW-ZHYW

步骤2：调用Bspplus登录接口
  用户名: zhouxiangyu
  密码: ******** (已隐藏)
  接口地址: http://172.29.91.36:9099/user/login

步骤3：检查登录结果
  ✅ 接口调用成功
  ✅ 登录成功 (flag=True)

步骤4：检查返回的用户信息
  ✅ 用户信息存在，包含 15 个字段

步骤5：检查关键字段
  ✅ username: zhouxiangyu
  ✅ name: 周翔宇
  ✅ mobile: 15650114963
  ⚠️  phone: 缺失或为空
  ✅ organName: 威海市项目组
  ✅ regionName: 威海市
  ✅ email: borischow0801@gmail.com

  🔍 重点检查：role字段
  ✅ role字段存在
  ✅ role值: ROLE_MAINTEN,PM,ROLE_SYSTEM
  ✅ role类型: str
  ✅ role长度: 24 字符
  ✅ 包含PM角色

步骤6：测试角色解析
  输入role值: ROLE_MAINTEN,PM,ROLE_SYSTEM
  解析后角色: manager
  角色显示名: 承建方-项目经理
  ✅ 角色解析成功

================================================================================
测试总结
================================================================================
✅ role字段存在，值为: ROLE_MAINTEN,PM,ROLE_SYSTEM
✅ 角色解析结果: manager
```

---

### 步骤5：解析角色

**文件**：`backend/apps/accounts/bspplus_service.py`
**方法**：`sync_user_from_bspplus(cls, bspplus_user_data)`
**代码位置**：第210-215行

**关键代码**：
```python
bspplus_role = bspplus_user_data.get('role', '')  # 例如："ROLE_MAINTEN,PM,ROLE_SYSTEM"
system_role = cls._parse_role(bspplus_role)       # 调用角色解析方法
```

**排查点**：
- [ ] 检查 `bspplus_role` 的值是什么（例如：`"ROLE_MAINTEN,PM,ROLE_SYSTEM"`）
- [ ] 检查 `_parse_role()` 方法是否被调用
- [ ] 检查 `system_role` 的返回值是什么（应该是：`'user'`、`'admin'`、`'manager'`、`'employee'` 之一）

#### 5.1 角色解析详细流程

**文件**：`backend/apps/accounts/bspplus_service.py`
**方法**：`_parse_role(cls, role_str)`
**代码位置**：第32-81行

**关键步骤**：

1. **输入检查**
   ```python
   if not role_str:
       return 'user'  # 如果为空，返回默认角色'user'
   ```

2. **转换为大写**
   ```python
   role_str_upper = role_str.upper()  # "ROLE_MAINTEN,PM,ROLE_SYSTEM" -> "ROLE_MAINTEN,PM,ROLE_SYSTEM"
   ```

3. **优先顺序匹配**
   ```python
   priority_roles = ['AUDITOR', 'PM', 'REQUESTER', 'STAFF']
   
   for priority_role in priority_roles:
       if priority_role == 'PM':
           # PM需要精确匹配（使用正则表达式）
           pm_pattern = r'(^|[,;])PM([,;]|$)'
           if re.search(pm_pattern, role_str_upper):
               return 'manager'  # PM -> manager
       else:
           # 其他角色关键词匹配
           if priority_role in role_str_upper:
               if priority_role == 'AUDITOR':
                   return 'admin'
               elif priority_role == 'REQUESTER':
                   return 'user'
               elif priority_role == 'STAFF':
                   return 'employee'
   ```

4. **默认值**
   ```python
   return 'user'  # 如果都不匹配，返回默认角色'user'
   ```

**排查点**：
- [ ] 检查 `role_str` 输入值（例如：`"ROLE_MAINTEN,PM,ROLE_SYSTEM"`）
- [ ] 检查 `role_str_upper` 的值（应该转换为大写）
- [ ] 检查是否匹配到 `PM`（使用正则表达式 `r'(^|[,;])PM([,;]|$)'`）
- [ ] 检查正则表达式匹配结果（应该匹配到 `,PM,`）
- [ ] 检查返回的角色值（对于 `PM`，应该返回 `'manager'`）

**角色映射关系**：
- `AUDITOR` → `admin`（管理方）
- `PM` → `manager`（承建方-项目经理）
- `REQUESTER` → `user`（使用方）
- `STAFF` → `employee`（承建方-员工）
- 都不匹配 → `user`（默认，使用方）

---

### 步骤6：数据库操作（创建或更新用户）

**文件**：`backend/apps/accounts/bspplus_service.py`
**方法**：`sync_user_from_bspplus(cls, bspplus_user_data)`
**代码位置**：第217-293行

**关键步骤**：

#### 6.1 获取或创建用户
```python
user, created = User.objects.get_or_create(
    username=username,
    defaults={
        'first_name': bspplus_user_data.get('name', ''),           # 姓名
        'phone': bspplus_user_data.get('mobile', '') or bspplus_user_data.get('phone', ''),  # 手机号（优先使用mobile）
        'department': bspplus_user_data.get('organName', ''),      # 部门
        'region_name': bspplus_user_data.get('regionName', ''),    # 区划名称
        'email': bspplus_user_data.get('email', ''),               # 邮箱
        'role': system_role,                                       # 角色（已解析）
        'is_active': True,
    }
)
```

**排查点**：
- [ ] 检查 `username` 是否从 `bspplus_user_data.get('username')` 正确获取
- [ ] 检查 `created` 的值（`True` 表示新创建，`False` 表示已存在）
- [ ] 检查新创建用户时，`defaults` 字典中的值是否正确：
  - [ ] `first_name` 是否从 `bspplus_user_data.get('name')` 获取
  - [ ] `phone` 是否从 `bspplus_user_data.get('mobile')` 获取（**注意：是mobile，不是phone**）
  - [ ] `department` 是否从 `bspplus_user_data.get('organName')` 获取
  - [ ] `region_name` 是否从 `bspplus_user_data.get('regionName')` 获取
  - [ ] `email` 是否从 `bspplus_user_data.get('email')` 获取
  - [ ] **重点**：`role` 是否使用了 `system_role`（解析后的角色值）

#### 6.2 新用户处理
```python
if created:
    user.set_unusable_password()  # 设置不可用密码（防止通过Django Admin登录）
    user.save()
```

**排查点**：
- [ ] 检查新用户是否调用了 `set_unusable_password()`
- [ ] 检查新用户是否调用了 `save()`

#### 6.3 已存在用户更新
```python
if not created:
    updated = False
    
    # 更新手机号
    new_phone = bspplus_user_data.get('mobile', '') or bspplus_user_data.get('phone', '') or ''
    if current_phone != new_phone:
        user.phone = new_phone
        updated = True
    
    # 更新姓名
    new_name = bspplus_user_data.get('name', '')
    if current_name != new_name:
        user.first_name = new_name
        updated = True
    
    # 更新部门
    new_department = bspplus_user_data.get('organName', '')
    if current_department != new_department:
        user.department = new_department
        updated = True
    
    # 更新区划名称
    new_region_name = bspplus_user_data.get('regionName', '')
    if current_region_name != new_region_name:
        user.region_name = new_region_name
        updated = True
    
    # 更新邮箱
    new_email = bspplus_user_data.get('email', '')
    if current_email != new_email:
        user.email = new_email
        updated = True
    
    # 更新角色
    if user.role != system_role:
        user.role = system_role
        updated = True
    
    if updated:
        user.save()
```

**排查点**：
- [ ] 检查每个字段的更新逻辑是否正确
- [ ] **重点**：检查 `phone` 字段是否从 `mobile` 获取（`bspplus_user_data.get('mobile', '')`）
- [ ] **重点**：检查角色更新逻辑（`if user.role != system_role`）
- [ ] 检查是否有字段被更新（`updated = True`）
- [ ] 检查是否调用了 `user.save()`

---

### 步骤7：返回登录结果

**文件**：`backend/apps/accounts/views.py`
**代码位置**：第113-125行

**关键代码**：
```python
# 生成token
refresh = self.get_token(user)
data = {
    'refresh': str(refresh),
    'access': str(refresh.access_token),
}

# 添加用户信息到响应中
from .serializers import UserSerializer
user_serializer = UserSerializer(user)
data.update(user_serializer.data)

return data
```

**排查点**：
- [ ] 检查Token是否成功生成
- [ ] 检查响应中是否包含用户信息
- [ ] 检查响应中的 `role` 字段是否正确（应该与数据库中的值一致）
- [ ] 检查响应中的 `phone`、`department`、`region_name` 等字段是否正确

---

## 数据库验证

### 检查用户数据是否正确保存

**方法1：使用Django Admin**
1. 访问 Django Admin：`http://your-domain/admin/`
2. 登录管理员账号
3. 进入"用户"页面
4. 查找对应用户（根据username）
5. 检查以下字段：
   - `role`：应该是对应的角色值（`user`、`admin`、`manager`、`employee`）
   - `phone`：应该是 `mobile` 字段的值
   - `first_name`：应该是 `name` 字段的值
   - `department`：应该是 `organName` 字段的值
   - `region_name`：应该是 `regionName` 字段的值
   - `email`：应该是 `email` 字段的值

**方法2：使用数据库命令行**
```sql
-- 连接MySQL
mysql -u oms_user -p oms_db

-- 查询用户信息
SELECT username, role, phone, first_name, department, region_name, email 
FROM users 
WHERE username = 'zhouxiangyu';

-- 应该看到类似结果：
-- username: zhouxiangyu
-- role: manager (如果是PM角色)
-- phone: 15650114963 (从mobile字段获取)
-- first_name: 周翔宇
-- department: 威海市项目组
-- region_name: 威海市
-- email: borischow0801@gmail.com
```

---

## 常见问题排查

### 问题1：角色解析不正确（所有用户都是'user'）

**可能原因**：
1. `bspplus_user_data.get('role')` 返回的值格式不对
2. 角色解析逻辑没有正确匹配

**排查步骤**：
1. 在 `sync_user_from_bspplus` 方法中添加打印语句，查看 `bspplus_role` 的值
2. 检查 `_parse_role` 方法的返回值
3. 手动测试角色解析逻辑：
   ```python
   # 在Django shell中测试
   python manage.py shell
   >>> from apps.accounts.bspplus_service import BspplusService
   >>> BspplusService._parse_role("ROLE_MAINTEN,PM,ROLE_SYSTEM")
   # 应该返回 'manager'
   ```

### 问题2：手机号没有同步

**可能原因**：
1. Bspplus接口返回的是 `mobile` 字段，不是 `phone` 字段
2. 代码中使用了错误的字段名

**排查步骤**：
1. 检查 `bspplus_user_data` 中是否有 `mobile` 字段
2. 检查代码中是否使用了 `bspplus_user_data.get('mobile', '')`（不是 `get('phone', '')`）

### 问题3：用户信息没有更新

**可能原因**：
1. 用户已存在，但更新逻辑没有执行
2. `updated` 标志没有被设置为 `True`
3. `user.save()` 没有被调用

**排查步骤**：
1. 检查数据库中的用户记录是否存在
2. 检查更新逻辑中的条件判断（例如：`if current_phone != new_phone`）
3. 检查是否调用了 `user.save()`

---

## 调试建议

### 1. 添加临时打印语句

在关键位置添加 `print()` 语句，查看变量值：

```python
# 在 sync_user_from_bspplus 方法中
print(f"[DEBUG] bspplus_user_data: {bspplus_user_data}")
print(f"[DEBUG] bspplus_role: {bspplus_role}")
print(f"[DEBUG] system_role: {system_role}")
print(f"[DEBUG] user.role: {user.role}")
```

### 2. 使用Django Shell测试

```bash
python manage.py shell
```

```python
# 测试角色解析
from apps.accounts.bspplus_service import BspplusService

# 测试PM角色
result = BspplusService._parse_role("ROLE_MAINTEN,PM,ROLE_SYSTEM")
print(f"PM角色解析结果: {result}")  # 应该输出: manager

# 测试AUDITOR角色
result = BspplusService._parse_role("AUDITOR,ROLE_ADMIN")
print(f"AUDITOR角色解析结果: {result}")  # 应该输出: admin

# 测试STAFF角色
result = BspplusService._parse_role("STAFF,ROLE_EMPLOYEE")
print(f"STAFF角色解析结果: {result}")  # 应该输出: employee

# 测试REQUESTER角色
result = BspplusService._parse_role("REQUESTER,ROLE_USER")
print(f"REQUESTER角色解析结果: {result}")  # 应该输出: user
```

### 3. 检查数据库中的实际数据

```sql
SELECT username, role, phone, first_name, department, region_name 
FROM users 
ORDER BY updated_at DESC 
LIMIT 10;
```

---

## 总结

按照以上步骤逐一排查，可以定位到问题所在。重点检查：

1. **Bspplus接口返回的数据结构**（特别是 `role` 和 `mobile` 字段）
2. **角色解析逻辑**（`_parse_role` 方法的输入和输出）
3. **数据库更新逻辑**（字段映射和更新条件）
4. **数据库中的实际数据**（验证数据是否正确保存）
