# settings.py 文件修改对比

## 修改位置

在文件末尾（第167行之后）添加了Bspplus接口配置。

## 详细对比

### 修改前（原文件末尾）

```python
# CORS Settings
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://localhost:5173'
).split(',')

CORS_ALLOW_CREDENTIALS = True
```

### 修改后（当前文件）

```python
# CORS Settings
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://localhost:5173'
).split(',')

CORS_ALLOW_CREDENTIALS = True

# Bspplus接口配置
BSPPLUS_API_ROOT = config('BSPPLUS_API_ROOT', default='http://localhost:8080')
BSPPLUS_APP_CODE = config('BSPPLUS_APP_CODE', default='app_test1')
```

## 新增内容

在文件末尾添加了以下3行：

```python
# Bspplus接口配置
BSPPLUS_API_ROOT = config('BSPPLUS_API_ROOT', default='http://localhost:8080')
BSPPLUS_APP_CODE = config('BSPPLUS_APP_CODE', default='app_test1')
```

## 说明

1. **BSPPLUS_API_ROOT**：Bspplus接口的根地址，可通过环境变量`BSPPLUS_API_ROOT`配置，默认值为`http://localhost:8080`
2. **BSPPLUS_APP_CODE**：应用编码，可通过环境变量`BSPPLUS_APP_CODE`配置，默认值为`app_test1`

这两个配置项用于Bspplus用户登录接口的调用，配置方式与项目中其他配置项保持一致，使用`python-decouple`库从环境变量读取。

## 行号变化

- 原文件：167行
- 修改后：172行
- 新增：3行（注释1行 + 配置2行）
