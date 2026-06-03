#!/usr/bin/env python
"""
检查oms_admin用户后台访问权限的脚本
用于排查403和CSRF问题
"""
import os
import sys

# 获取脚本所在目录的父目录（backend目录）
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)

# 将backend目录添加到Python路径
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oms_backend.settings')

import django
django.setup()

from apps.accounts.models import User
from django.db import connection
from django.conf import settings

def main():
    username = 'oms_admin'
    
    print("=" * 60)
    print("OMS后台访问权限检查脚本")
    print("=" * 60)
    print()
    
    try:
        # 检查用户是否存在
        try:
            admin_user = User.objects.get(username=username)
            print(f"✅ 用户存在: {username}")
        except User.DoesNotExist:
            print(f"❌ 用户 {username} 不存在")
            sys.exit(1)
        
        print()
        print("-" * 60)
        print("1. 用户基本信息:")
        print("-" * 60)
        print(f"用户名: {admin_user.username}")
        print(f"邮箱: {admin_user.email or '(未设置)'}")
        print(f"是否有可用密码: {'✅ 是' if admin_user.has_usable_password() else '❌ 否'}")
        print(f"is_active: {'✅ True' if admin_user.is_active else '❌ False'}")
        
        # 使用原始SQL读取数据库字段
        print()
        print("-" * 60)
        print("2. 数据库字段值（使用原始SQL）:")
        print("-" * 60)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT is_staff, is_superuser, is_active FROM users WHERE username = %s",
                [username]
            )
            row = cursor.fetchone()
            if row:
                db_is_staff = bool(row[0])
                db_is_superuser = bool(row[1])
                db_is_active = bool(row[2])
                print(f"is_staff (数据库): {'✅ True' if db_is_staff else '❌ False'}")
                print(f"is_superuser (数据库): {'✅ True' if db_is_superuser else '❌ False'}")
                print(f"is_active (数据库): {'✅ True' if db_is_active else '❌ False'}")
            else:
                print("❌ 无法从数据库读取用户信息")
        
        # 检查Django属性（可能被@property覆盖）
        print()
        print("-" * 60)
        print("3. Django对象属性（可能被@property覆盖）:")
        print("-" * 60)
        print(f"admin_user.is_staff: {admin_user.is_staff} (可能是@property)")
        print(f"admin_user.is_superuser: {admin_user.is_superuser}")
        print(f"admin_user.is_active: {admin_user.is_active}")
        
        # 检查权限方法
        print()
        print("-" * 60)
        print("4. Django权限检查:")
        print("-" * 60)
        print(f"has_perm('admin'): {admin_user.has_perm('admin')}")
        print(f"has_module_perms('admin'): {admin_user.has_module_perms('admin')}")
        
        # 检查CSRF配置
        print()
        print("-" * 60)
        print("5. CSRF配置检查:")
        print("-" * 60)
        csrf_middleware = 'django.middleware.csrf.CsrfViewMiddleware'
        has_csrf = csrf_middleware in settings.MIDDLEWARE
        print(f"CSRF中间件已启用: {'✅ 是' if has_csrf else '❌ 否'}")
        
        csrf_trusted_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
        print(f"CSRF_TRUSTED_ORIGINS: {csrf_trusted_origins if csrf_trusted_origins else '(未设置)'}")
        
        allowed_hosts = settings.ALLOWED_HOSTS
        print(f"ALLOWED_HOSTS: {allowed_hosts}")
        
        # 检查CORS配置
        print()
        print("-" * 60)
        print("6. CORS配置检查:")
        print("-" * 60)
        cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        print(f"CORS_ALLOWED_ORIGINS: {cors_origins if cors_origins else '(未设置)'}")
        
        # 总结
        print()
        print("=" * 60)
        print("检查总结:")
        print("=" * 60)
        
        issues = []
        if not admin_user.has_usable_password():
            issues.append("❌ 用户没有可用密码")
        if not db_is_staff:
            issues.append("❌ is_staff=False (数据库)")
        if not db_is_superuser:
            issues.append("❌ is_superuser=False (数据库)")
        if not db_is_active:
            issues.append("❌ is_active=False (数据库)")
        if not admin_user.has_module_perms('admin'):
            issues.append("❌ 用户没有admin模块权限")
        
        if issues:
            print("发现以下问题:")
            for issue in issues:
                print(f"  {issue}")
            print()
            print("建议修复:")
            print("  1. 如果is_staff或is_superuser为False，运行fix_admin_user.py修复")
            print("  2. 如果用户没有密码，运行fix_admin_user.py设置密码")
            print("  3. 清除浏览器Cookie和缓存后重试")
            print("  4. 检查CSRF_TRUSTED_ORIGINS配置，确保包含后台访问地址")
        else:
            print("✅ 所有检查通过，用户应该可以访问后台")
            print()
            print("如果仍然无法访问，可能是以下原因:")
            print("  1. 浏览器Cookie问题 - 清除Cookie后重试")
            print("  2. CSRF token问题 - 检查CSRF_TRUSTED_ORIGINS配置")
            print("  3. 会话问题 - 尝试使用无痕模式访问")
            print("  4. 中间件问题 - 检查MIDDLEWARE配置")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
