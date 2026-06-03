#!/usr/bin/env python
"""
测试oms_admin登录的详细脚本
模拟Django Admin的完整登录流程
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
from django.contrib.auth import authenticate
from django.contrib.auth.backends import ModelBackend

def main():
    username = 'oms_admin'
    password = '123456Aa?'
    
    print("=" * 60)
    print("oms_admin登录详细测试脚本")
    print("=" * 60)
    print()
    
    try:
        # 1. 获取用户对象
        print("-" * 60)
        print("1. 获取用户对象:")
        print("-" * 60)
        try:
            user = User.objects.get(username=username)
            print(f"✅ 用户存在: {username} (ID: {user.id})")
        except User.DoesNotExist:
            print(f"❌ 用户不存在")
            sys.exit(1)
        except User.MultipleObjectsReturned:
            print(f"⚠️  多个用户")
            users = User.objects.filter(username=username)
            for u in users:
                print(f"  - ID: {u.id}")
            sys.exit(1)
        
        # 2. 检查密码
        print()
        print("-" * 60)
        print("2. 检查密码:")
        print("-" * 60)
        has_password = user.has_usable_password()
        print(f"has_usable_password(): {has_password}")
        
        if not has_password:
            print("❌ 用户没有可用密码！")
            print("   这可能是被Bspplus同步逻辑设置为不可用密码了")
            print("   需要运行 reset_admin_password.py 重置密码")
            sys.exit(1)
        
        # 3. 测试密码验证（多种方法）
        print()
        print("-" * 60)
        print("3. 测试密码验证:")
        print("-" * 60)
        print(f"测试密码: {password}")
        
        # 方法1：直接check_password
        result1 = user.check_password(password)
        print(f"user.check_password('{password}'): {result1}")
        
        # 方法2：使用authenticate
        auth_user = authenticate(username=username, password=password)
        if auth_user:
            print(f"authenticate(username='{username}', password='...'): ✅ 成功 (ID: {auth_user.id})")
        else:
            print(f"authenticate(username='{username}', password='...'): ❌ 失败")
        
        # 方法3：使用ModelBackend
        backend = ModelBackend()
        backend_user = backend.authenticate(None, username=username, password=password)
        if backend_user:
            print(f"ModelBackend.authenticate(...): ✅ 成功 (ID: {backend_user.id})")
        else:
            print(f"ModelBackend.authenticate(...): ❌ 失败")
        
        # 4. 检查数据库中的实际值
        print()
        print("-" * 60)
        print("4. 检查数据库中的实际值:")
        print("-" * 60)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, password, is_staff, is_superuser, is_active FROM users WHERE username = %s",
                [username]
            )
            row = cursor.fetchone()
            if row:
                db_id, db_username, db_password, db_is_staff, db_is_superuser, db_is_active = row
                print(f"ID: {db_id}")
                print(f"用户名: '{db_username}' (长度: {len(db_username)})")
                print(f"密码哈希: {db_password[:50] if db_password else 'NULL'}...")
                print(f"is_staff: {bool(db_is_staff)}")
                print(f"is_superuser: {bool(db_is_superuser)}")
                print(f"is_active: {bool(db_is_active)}")
                
                # 检查用户名是否有空格或特殊字符
                if db_username != db_username.strip():
                    print(f"⚠️  用户名前后有空格: '{db_username}'")
                if db_username != username:
                    print(f"⚠️  用户名不匹配: 期望 '{username}', 实际 '{db_username}'")
        
        # 5. 测试不同的用户名变体
        print()
        print("-" * 60)
        print("5. 测试不同的用户名变体:")
        print("-" * 60)
        username_variants = [
            username,
            username.upper(),
            username.lower(),
            username.capitalize(),
            ' ' + username,
            username + ' ',
        ]
        for variant in username_variants:
            try:
                test_user = User.objects.get(username=variant)
                test_auth = authenticate(username=variant, password=password)
                print(f"'{variant}': 用户存在={test_user is not None}, 认证={test_auth is not None}")
            except User.DoesNotExist:
                print(f"'{variant}': 用户不存在")
            except Exception as e:
                print(f"'{variant}': 错误 - {e}")
        
        # 6. 检查认证后端配置
        print()
        print("-" * 60)
        print("6. 检查认证后端配置:")
        print("-" * 60)
        from django.conf import settings
        auth_backends = getattr(settings, 'AUTHENTICATION_BACKENDS', None)
        if auth_backends:
            print("AUTHENTICATION_BACKENDS:")
            for backend in auth_backends:
                print(f"  - {backend}")
        else:
            print("AUTHENTICATION_BACKENDS: 未设置（使用默认: django.contrib.auth.backends.ModelBackend）")
        
        # 7. 模拟Django Admin登录视图的认证流程
        print()
        print("-" * 60)
        print("7. 模拟Django Admin登录流程:")
        print("-" * 60)
        from django.contrib.auth.forms import AuthenticationForm
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post('/admin/login/', {
            'username': username,
            'password': password,
        })
        
        form = AuthenticationForm(data={
            'username': username,
            'password': password,
        })
        
        if form.is_valid():
            print("✅ AuthenticationForm.is_valid(): True")
            auth_user = form.get_user()
            print(f"✅ form.get_user(): 成功 (ID: {auth_user.id})")
        else:
            print("❌ AuthenticationForm.is_valid(): False")
            print(f"   错误: {form.errors}")
        
        # 8. 总结和建议
        print()
        print("=" * 60)
        print("测试总结:")
        print("=" * 60)
        
        all_pass = (
            has_password and
            result1 and
            auth_user is not None and
            backend_user is not None and
            form.is_valid()
        )
        
        if all_pass:
            print("✅ 所有测试通过，用户应该可以登录")
            print()
            print("如果仍然无法登录，可能是以下原因:")
            print("  1. 浏览器Cookie/会话问题 - 清除Cookie后重试")
            print("  2. 用户名输入问题 - 确认没有多余空格")
            print("  3. 密码输入问题 - 确认没有多余空格或特殊字符")
            print("  4. 会话过期 - 使用无痕模式访问")
        else:
            print("❌ 部分测试失败")
            print()
            if not result1:
                print("  - check_password()失败，密码可能不正确")
            if auth_user is None:
                print("  - authenticate()失败，可能是用户名或密码错误")
            if not form.is_valid():
                print(f"  - AuthenticationForm验证失败: {form.errors}")
            print()
            print("建议:")
            print("  1. 运行 reset_admin_password.py 重新设置密码")
            print("  2. 确认用户名和密码输入正确（区分大小写，无多余空格）")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
