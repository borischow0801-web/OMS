#!/usr/bin/env python
"""
诊断oms_admin登录问题的脚本
详细检查密码验证和认证流程
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

def main():
    username = 'oms_admin'
    test_password = '123456Aa?'
    
    print("=" * 60)
    print("oms_admin登录问题诊断脚本")
    print("=" * 60)
    print()
    
    try:
        # 1. 检查用户是否存在
        print("-" * 60)
        print("1. 检查用户是否存在:")
        print("-" * 60)
        try:
            admin_user = User.objects.get(username=username)
            print(f"✅ 用户存在: {username}")
            print(f"   ID: {admin_user.id}")
        except User.DoesNotExist:
            print(f"❌ 用户 {username} 不存在")
            # 列出所有用户
            print("\n数据库中的所有用户:")
            all_users = User.objects.all().values_list('username', flat=True)
            for u in all_users:
                print(f"  - {u}")
            sys.exit(1)
        except User.MultipleObjectsReturned:
            print(f"⚠️  找到多个用户名为 {username} 的用户")
            users = User.objects.filter(username=username)
            for u in users:
                print(f"  - ID: {u.id}, is_active: {u.is_active}")
            sys.exit(1)
        
        # 2. 检查密码状态
        print()
        print("-" * 60)
        print("2. 检查密码状态:")
        print("-" * 60)
        has_password = admin_user.has_usable_password()
        print(f"has_usable_password(): {'✅ True' if has_password else '❌ False'}")
        
        if not has_password:
            print("❌ 用户没有可用密码！")
            print("   这可能是被Bspplus同步逻辑设置为不可用密码了")
        
        # 3. 检查密码哈希
        print()
        print("-" * 60)
        print("3. 检查密码哈希:")
        print("-" * 60)
        password_hash = admin_user.password
        if password_hash:
            print(f"密码哈希前20个字符: {password_hash[:20]}...")
            print(f"密码哈希格式: {password_hash.split('$')[0] if '$' in password_hash else '未知格式'}")
        else:
            print("❌ 密码哈希为空")
        
        # 4. 测试密码验证
        print()
        print("-" * 60)
        print("4. 测试密码验证:")
        print("-" * 60)
        print(f"测试密码: {test_password}")
        
        # 方法1：使用check_password
        check_result = admin_user.check_password(test_password)
        print(f"admin_user.check_password('{test_password}'): {'✅ True' if check_result else '❌ False'}")
        
        # 方法2：使用authenticate
        auth_user = authenticate(username=username, password=test_password)
        if auth_user:
            print(f"authenticate(username='{username}', password='...'): ✅ 成功，返回用户ID: {auth_user.id}")
        else:
            print(f"authenticate(username='{username}', password='...'): ❌ 失败，返回None")
        
        # 5. 检查数据库字段
        print()
        print("-" * 60)
        print("5. 检查数据库字段（原始SQL）:")
        print("-" * 60)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, password, is_staff, is_superuser, is_active, email FROM users WHERE username = %s",
                [username]
            )
            row = cursor.fetchone()
            if row:
                db_id, db_username, db_password, db_is_staff, db_is_superuser, db_is_active, db_email = row
                print(f"ID: {db_id}")
                print(f"用户名: {db_username}")
                print(f"密码哈希: {db_password[:30] if db_password else 'NULL'}...")
                print(f"is_staff: {bool(db_is_staff)}")
                print(f"is_superuser: {bool(db_is_superuser)}")
                print(f"is_active: {bool(db_is_active)}")
                print(f"email: {db_email or '(NULL)'}")
                
                # 检查密码是否为空或不可用
                if not db_password or db_password.startswith('!'):
                    print("❌ 数据库中的密码哈希为空或标记为不可用（以!开头）")
        
        # 6. 检查是否有其他同名用户
        print()
        print("-" * 60)
        print("6. 检查是否有其他同名用户:")
        print("-" * 60)
        all_users = User.objects.filter(username=username)
        if all_users.count() > 1:
            print(f"⚠️  找到 {all_users.count()} 个同名用户:")
            for u in all_users:
                print(f"  - ID: {u.id}, is_active: {u.is_active}, has_password: {u.has_usable_password()}")
        else:
            print("✅ 只有一个用户")
        
        # 7. 检查认证后端
        print()
        print("-" * 60)
        print("7. 检查认证后端配置:")
        print("-" * 60)
        from django.conf import settings
        auth_backends = getattr(settings, 'AUTHENTICATION_BACKENDS', None)
        if auth_backends:
            print("AUTHENTICATION_BACKENDS:")
            for backend in auth_backends:
                print(f"  - {backend}")
        else:
            print("AUTHENTICATION_BACKENDS: 未设置（使用默认）")
        
        # 8. 建议修复方案
        print()
        print("=" * 60)
        print("诊断总结和建议:")
        print("=" * 60)
        
        issues = []
        if not has_password:
            issues.append("❌ 用户没有可用密码")
        if not check_result:
            issues.append("❌ 密码验证失败")
        if not auth_user:
            issues.append("❌ authenticate()返回None")
        
        if issues:
            print("\n发现的问题:")
            for issue in issues:
                print(f"  {issue}")
            
            print("\n建议修复步骤:")
            print("  1. 运行 reset_admin_password.py 重新设置密码")
            print("  2. 确保密码设置后立即验证 check_password() 返回True")
            print("  3. 如果密码哈希以'!'开头，说明被标记为不可用，需要重新设置")
            print("  4. 检查是否有多个同名用户，如果有，删除多余的")
            print("  5. 清除浏览器Cookie和缓存后重试")
        else:
            print("\n✅ 所有检查通过，密码验证正常")
            print("\n如果仍然无法登录，可能是以下原因:")
            print("  1. 浏览器Cookie问题 - 清除Cookie后重试")
            print("  2. 会话问题 - 使用无痕模式访问")
            print("  3. 用户名大小写问题 - 确认输入的是 'oms_admin'（全小写）")
            print("  4. 密码输入问题 - 确认没有多余空格")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
