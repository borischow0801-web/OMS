# Bspplus用户体系调整说明

## 概述
本次调整将OMS应用的用户登录认证改为调用Bspplus通用用户登录接口，并根据接口返回值同步用户信息到本地数据库。

## 主要改动

### 1. 登录逻辑调整
- **原逻辑**：使用Django自带的用户认证系统
- **新逻辑**：调用Bspplus通用用户登录接口进行认证
- **判断条件**：接口返回`"flag": true`且`status=200`时允许登录
- **错误处理**：如返回`"msg": "账号或密码错误"`，则弹出相应提示

### 2. 角色映射
根据Bspplus接口返回的`role`值进行角色映射：
- `AUDITOR` → `auditor` (审核方)
- `PM` → `pm` (项目经理)
- `REQUESTER` → `requester` (提出方)
- `STAFF` → `staff` (员工)

### 3. 用户信息同步
- 保留系统本身的用户管理体系和数据
- 每次登录后根据Bspplus接口返回值更新用户信息
- 更新字段：手机号(phone)、姓名(name)、部门(organName)、区划名称(regionName)
- 更新操作在后台异步执行，不影响前台登录响应

### 4. 新增字段
- 在User模型中新增`region_name`字段，对应Bspplus接口返回的`regionName`

## 修改的文件清单

### 后端文件

1. **`backend/apps/accounts/models.py`**
   - 添加`region_name`字段
   - 更新角色选择项，添加新的角色映射
   - 添加新角色的属性判断方法

2. **`backend/apps/accounts/views.py`**
   - 修改`CustomTokenObtainPairSerializer.validate()`方法
   - 改为调用Bspplus登录接口
   - 实现用户信息同步逻辑（同步+异步双重保障）

3. **`backend/apps/accounts/serializers.py`**
   - `UserSerializer`：添加`region_name`字段
   - `UserUpdateSerializer`：添加`region_name`字段

4. **`backend/apps/accounts/bspplus_service.py`** (新建)
   - `BspplusService`类：实现Bspplus接口调用
   - `login()`方法：调用Bspplus登录接口
   - `sync_user_from_bspplus()`方法：同步用户信息到本地数据库

5. **`backend/oms_backend/settings.py`**
   - 添加Bspplus接口配置：
     - `BSPPLUS_API_ROOT`：Bspplus接口根地址（可配置）
     - `BSPPLUS_APP_CODE`：应用编码（可配置）

6. **`backend/apps/accounts/admin.py`**
   - 修复`list_filter`，移除`is_staff`（避免系统检查错误）

7. **`backend/apps/accounts/migrations/0002_user_region_name.py`** (新建)
   - 数据库迁移文件：添加`region_name`字段

## 配置说明

### 环境变量配置
在`.env`文件中需要添加以下配置：

```env
# Bspplus接口配置
BSPPLUS_API_ROOT=http://your-bspplus-api-root
BSPPLUS_APP_CODE=your_app_code
```

**注意**：
- `BSPPLUS_API_ROOT`：Bspplus接口的根地址，例如：`http://localhost:8080`
- `BSPPLUS_APP_CODE`：应用编码，例如：`app_test1`

### 密码加密说明
根据Bspplus接口文档，`password`字段需要加密（MD5）。当前实现中：
- 如果前端已经对密码进行MD5加密，则直接使用
- 如果前端未加密，需要在后端`BspplusService.login()`方法中添加MD5加密逻辑

**建议**：根据实际Bspplus接口要求，确认密码加密方式，如需后端处理，可在`bspplus_service.py`的`login()`方法中添加加密逻辑。

## 部署步骤

### 1. 更新代码
将以下文件同步到生产环境：
- `backend/apps/accounts/models.py`
- `backend/apps/accounts/views.py`
- `backend/apps/accounts/serializers.py`
- `backend/apps/accounts/bspplus_service.py` (新建)
- `backend/oms_backend/settings.py`
- `backend/apps/accounts/admin.py`
- `backend/apps/accounts/migrations/0002_user_region_name.py` (新建)

### 2. 安装依赖
确保已安装`requests`库（用于调用Bspplus接口）：
```bash
pip install requests
```

### 3. 配置环境变量
在生产环境的`.env`文件中添加Bspplus接口配置：
```env
BSPPLUS_API_ROOT=http://your-bspplus-api-root
BSPPLUS_APP_CODE=your_app_code
```

### 4. 执行数据库迁移
```bash
cd /path/to/OMS/backend
source venv/bin/activate
python manage.py migrate accounts
```

### 5. 重启服务
重启Django应用服务，使配置生效。

## 测试要点

1. **登录测试**
   - 使用正确的账号密码登录，应能成功
   - 使用错误的账号密码登录，应显示"账号或密码错误"提示
   - 检查JWT token是否正常生成

2. **用户信息同步测试**
   - 登录后检查本地数据库，用户信息是否正确同步
   - 检查`region_name`字段是否正确填充
   - 检查角色映射是否正确

3. **角色映射测试**
   - 测试不同角色的用户登录，检查角色是否正确映射
   - 验证角色权限是否正常工作

4. **接口配置测试**
   - 验证Bspplus接口地址配置是否正确
   - 验证应用编码配置是否正确

## 注意事项

1. **密码加密**：根据实际Bspplus接口要求，确认密码是否需要MD5加密，如需后端处理，请修改`bspplus_service.py`

2. **接口地址**：确保Bspplus接口地址可访问，且网络连通

3. **用户唯一性**：系统以`username`作为唯一标识，确保Bspplus返回的用户名唯一

4. **后台同步**：用户信息更新在后台异步执行，首次登录时可能信息还未完全同步，但不会影响登录流程

5. **退出登录**：退出登录逻辑保持不变，仍使用原有实现

## 回滚方案

如需回滚到原有登录逻辑：
1. 恢复`backend/apps/accounts/views.py`中的`CustomTokenObtainPairSerializer.validate()`方法
2. 移除或注释掉Bspplus相关配置
3. 重启服务

## 文件路径总结

### 修改的文件
- `/app/OMS/backend/apps/accounts/models.py`
- `/app/OMS/backend/apps/accounts/views.py`
- `/app/OMS/backend/apps/accounts/serializers.py`
- `/app/OMS/backend/oms_backend/settings.py`
- `/app/OMS/backend/apps/accounts/admin.py`

### 新建的文件
- `/app/OMS/backend/apps/accounts/bspplus_service.py`
- `/app/OMS/backend/apps/accounts/migrations/0002_user_region_name.py`

### 文档文件
- `/app/OMS/docs/Bspplus用户体系调整说明.md` (本文件)
