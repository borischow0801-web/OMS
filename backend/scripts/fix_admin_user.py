#!/usr/bin/env python
"""
一键修复oms_admin用户脚本
用于修复后台登录问题，确保oms_admin用户可以正常登录Django Admin后台
"""
import os
import sys

# 获取脚本所在目录的父目录（backend目录）
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)  # backend目录

# 将backend目录添加到Python路径
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oms_backend.settings')

# 导入并设置Django
import django
django.setup()

from apps.accounts.models import User
import getpass

def main():
    username = 'oms_admin'
    
    print("=" * 60)
    print("OMS后台管理员用户修复脚本")
    print("=" * 60)
    print()
    
    try:
        # 获取用户
        try:
            admin_user = User.objects.get(username=username)
            print(f"✅ 找到用户: {username}")
        except User.DoesNotExist:
            print(f"❌ 用户 {username} 不存在")
            print()
            print("是否创建新用户？(y/n): ", end='')
            choice = input().strip().lower()
            if choice == 'y':
                print("\n创建新用户...")
                email = input("邮箱 (可选，直接回车跳过): ").strip() or ''
                password = getpass.getpass("密码: ")
                password_confirm = getpass.getpass("确认密码: ")
                
                if password != password_confirm:
                    print("❌ 两次密码输入不一致")
                    sys.exit(1)
                
                # 创建用户
                admin_user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                # 使用原始SQL更新数据库字段，绕过@property
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE users SET is_staff = %s, is_superuser = %s, is_active = %s WHERE username = %s",
                        [True, True, True, username]
                    )
                # 重新获取用户对象
                admin_user = User.objects.get(username=username)
                print(f"✅ 用户 {username} 创建成功")
            else:
                print("已取消")
                sys.exit(0)
        
        print()
        print("-" * 60)
        print("当前用户状态:")
        print("-" * 60)
        print(f"用户名: {admin_user.username}")
        print(f"邮箱: {admin_user.email or '(未设置)'}")
        print(f"是否有可用密码: {'✅ 是' if admin_user.has_usable_password() else '❌ 否'}")
        
        # 注意：User模型中is_staff被@property覆盖了，无法通过ORM访问
        # 使用原始SQL查询或者只检查is_superuser（is_superuser=True本身就允许访问admin）
        from django.db import connection
        
        # 使用原始SQL查询is_staff字段
        with connection.cursor() as cursor:
            cursor.execute("SELECT is_staff, is_superuser, is_active FROM users WHERE username = %s", [username])
            row = cursor.fetchone()
            if row:
                current_is_staff = bool(row[0])
                current_is_superuser = bool(row[1])
                current_is_active = bool(row[2])
            else:
                current_is_staff = False
                current_is_superuser = False
                current_is_active = True
        
        print(f"is_staff (数据库字段): {'✅ True' if current_is_staff else '❌ False'}")
        print(f"is_superuser: {'✅ True' if current_is_superuser else '❌ False'}")
        print(f"is_active: {'✅ True' if current_is_active else '❌ False'}")
        print()
        
        # 检查是否需要修复
        need_fix = False
        fixes = []
        
        if not admin_user.has_usable_password():
            need_fix = True
            fixes.append("密码")
        
        if not current_is_staff:
            need_fix = True
            fixes.append("is_staff权限")
        
        if not current_is_superuser:
            need_fix = True
            fixes.append("is_superuser权限")
        
        if not current_is_active:
            need_fix = True
            fixes.append("is_active状态")
        
        if not need_fix:
            print("✅ 用户配置正常，无需修复")
            print()
            print("可以正常登录后台: http://59.224.25.175:2080/admin/login/")
            sys.exit(0)
        
        print(f"⚠️  需要修复: {', '.join(fixes)}")
        print()
        print("是否继续修复？(y/n): ", end='')
        choice = input().strip().lower()
        
        if choice != 'y':
            print("已取消")
            sys.exit(0)
        
        print()
        print("-" * 60)
        print("开始修复...")
        print("-" * 60)
        
        # 修复密码
        if not admin_user.has_usable_password():
            print("设置密码...")
            password = getpass.getpass("请输入新密码: ")
            password_confirm = getpass.getpass("请确认密码: ")
            
            if password != password_confirm:
                print("❌ 两次密码输入不一致")
                sys.exit(1)
            
            admin_user.set_password(password)
            print("✅ 密码已设置")
        
        # 修复权限
        # 注意：User模型中is_staff被@property覆盖了，需要使用原始SQL更新
        from django.db import connection
        
        # 先读取当前值（使用原始SQL）
        with connection.cursor() as cursor:
            cursor.execute("SELECT is_staff, is_superuser, is_active FROM users WHERE username = %s", [username])
            row = cursor.fetchone()
            if row:
                current_is_staff = bool(row[0])
                current_is_superuser = bool(row[1])
                current_is_active = bool(row[2])
            else:
                current_is_staff = False
                current_is_superuser = False
                current_is_active = True
        
        # 使用原始SQL更新数据库，绕过@property
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
        
        # 如果有需要更新的字段，使用原始SQL更新
        if updates:
            params.append(username)
            sql = f"UPDATE users SET {', '.join(updates)} WHERE username = %s"
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
            # 重新获取用户对象以刷新缓存
            admin_user = User.objects.get(username=username)
        
        print()
        print("=" * 60)
        print("✅ 修复完成！")
        print("=" * 60)
        print()
        # 重新从数据库读取字段值（使用原始SQL）
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT is_staff, is_superuser, is_active FROM users WHERE username = %s", [username])
            row = cursor.fetchone()
            if row:
                final_is_staff = bool(row[0])
                final_is_superuser = bool(row[1])
                final_is_active = bool(row[2])
            else:
                final_is_staff = False
                final_is_superuser = False
                final_is_active = True
        
        print("修复后的用户状态:")
        print(f"  用户名: {admin_user.username}")
        print(f"  有密码: {'✅ 是' if admin_user.has_usable_password() else '❌ 否'}")
        print(f"  is_staff (数据库字段): {'✅ True' if final_is_staff else '❌ False'}")
        print(f"  is_superuser: {'✅ True' if final_is_superuser else '❌ False'}")
        print(f"  is_active: {'✅ True' if final_is_active else '❌ False'}")
        print()
        print("现在可以使用以下信息登录后台:")
        print(f"  地址: http://59.224.25.175:2080/admin/login/")
        print(f"  用户名: {admin_user.username}")
        print(f"  密码: (刚才设置的密码)")
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
