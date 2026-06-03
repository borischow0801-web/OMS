#!/usr/bin/env python
"""
重置oms_admin用户密码脚本
用于解决密码验证失败问题
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
import getpass

def main():
    username = 'oms_admin'
    
    print("=" * 60)
    print("重置oms_admin用户密码脚本")
    print("=" * 60)
    print()
    
    try:
        # 检查用户是否存在
        try:
            admin_user = User.objects.get(username=username)
            print(f"✅ 找到用户: {username}")
        except User.DoesNotExist:
            print(f"❌ 用户 {username} 不存在")
            sys.exit(1)
        
        print()
        print("-" * 60)
        print("当前用户状态:")
        print("-" * 60)
        print(f"用户名: {admin_user.username}")
        print(f"邮箱: {admin_user.email or '(未设置)'}")
        print(f"是否有可用密码: {'✅ 是' if admin_user.has_usable_password() else '❌ 否'}")
        
        # 使用原始SQL读取数据库字段
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
        
        print()
        print("-" * 60)
        print("重置密码")
        print("-" * 60)
        print("请输入新密码（输入时不会显示字符）:")
        password = getpass.getpass("新密码: ")
        password_confirm = getpass.getpass("确认密码: ")
        
        if password != password_confirm:
            print("❌ 两次密码输入不一致")
            sys.exit(1)
        
        if not password:
            print("❌ 密码不能为空")
            sys.exit(1)
        
        # 使用Django的set_password方法设置密码
        # 这会自动进行密码哈希
        admin_user.set_password(password)
        admin_user.save()
        
        print()
        print("✅ 密码已重置")
        
        # 验证密码
        print()
        print("-" * 60)
        print("验证密码:")
        print("-" * 60)
        test_user = User.objects.get(username=username)
        if test_user.check_password(password):
            print("✅ 密码验证成功")
        else:
            print("❌ 密码验证失败（这不应该发生）")
        
        # 确保权限正确
        print()
        print("-" * 60)
        print("检查并修复权限:")
        print("-" * 60)
        
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT is_staff, is_superuser, is_active FROM users WHERE username = %s",
                [username]
            )
            row = cursor.fetchone()
            if row:
                current_is_staff = bool(row[0])
                current_is_superuser = bool(row[1])
                current_is_active = bool(row[2])
                
                updates = []
                params = []
                
                if not current_is_staff:
                    updates.append("is_staff = %s")
                    params.append(True)
                    print("✅ 已设置 is_staff=True")
                
                if not current_is_superuser:
                    updates.append("is_superuser = %s")
                    params.append(True)
                    print("✅ 已设置 is_superuser=True")
                
                if not current_is_active:
                    updates.append("is_active = %s")
                    params.append(True)
                    print("✅ 已设置 is_active=True")
                
                if updates:
                    params.append(username)
                    sql = f"UPDATE users SET {', '.join(updates)} WHERE username = %s"
                    cursor.execute(sql, params)
                    print("✅ 权限已更新")
                else:
                    print("✅ 权限配置正常")
        
        print()
        print("=" * 60)
        print("✅ 密码重置完成！")
        print("=" * 60)
        print()
        print("现在可以使用以下信息登录后台:")
        print(f"  地址: http://59.224.25.175:2080/admin/login/")
        print(f"  用户名: {username}")
        print(f"  密码: (刚才设置的新密码)")
        print()
        print("如果仍然无法登录，请检查:")
        print("  1. 确认用户名和密码输入正确（区分大小写）")
        print("  2. 清除浏览器Cookie后重试")
        print("  3. 使用无痕模式访问")
        print()
        
    except KeyboardInterrupt:
        print("\n\n已取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
