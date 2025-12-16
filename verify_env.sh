#!/bin/bash
# 快速验证 .env 配置是否生效

# 根据实际路径修改
BACKEND_DIR="/opt/OMS/backend"
# 如果路径不同，取消注释下面这行并修改路径
# BACKEND_DIR="/home/zxy_8581/OMS/backend"

if [ ! -d "$BACKEND_DIR" ]; then
    echo "错误: 后端目录不存在: $BACKEND_DIR"
    echo "请修改脚本中的 BACKEND_DIR 变量"
    exit 1
fi

cd "$BACKEND_DIR"

if [ ! -f "venv/bin/activate" ]; then
    echo "错误: 虚拟环境不存在"
    exit 1
fi

source venv/bin/activate

echo "=========================================="
echo "验证 .env 配置是否生效"
echo "=========================================="
echo ""

python manage.py shell << 'PYTHON_EOF'
from django.conf import settings

print("1. ALLOWED_HOSTS 检查:")
allowed_hosts = settings.ALLOWED_HOSTS
print(f"   当前值: {allowed_hosts}")
has_public_ip = '59.224.25.175' in allowed_hosts
has_private_ip = '172.29.91.61' in allowed_hosts
print(f"   {'✓' if has_public_ip else '✗'} 包含 59.224.25.175: {has_public_ip}")
print(f"   {'✓' if has_private_ip else '✗'} 包含 172.29.91.61: {has_private_ip}")

print("\n2. CORS_ALLOWED_ORIGINS 检查:")
cors_origins = settings.CORS_ALLOWED_ORIGINS
print(f"   当前值: {cors_origins}")
has_cors = 'http://59.224.25.175:2080' in cors_origins
print(f"   {'✓' if has_cors else '✗'} 包含 http://59.224.25.175:2080: {has_cors}")

print("\n3. DEBUG 模式检查:")
debug_mode = settings.DEBUG
print(f"   当前值: {debug_mode}")
print(f"   状态: {'✓ 生产环境（正确）' if not debug_mode else '✗ 开发环境（警告！生产环境应设为False）'}")

print("\n==========================================")
if has_public_ip and has_private_ip and has_cors and not debug_mode:
    print("✓ 所有配置检查通过！")
else:
    print("✗ 部分配置需要检查，请查看上面的详细信息")
print("==========================================")
PYTHON_EOF
