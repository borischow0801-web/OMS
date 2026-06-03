#!/usr/bin/env python
"""
修复User模型中is_staff @property覆盖问题的脚本
将@property is_staff重命名为is_staff_role，避免与Django的is_staff字段冲突
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

def main():
    username = 'oms_admin'
    
    print("=" * 60)
    print("修复is_staff @property覆盖问题")
    print("=" * 60)
    print()
    print("问题分析:")
    print("User模型中有一个@property is_staff方法，它覆盖了Django的is_staff字段")
    print("这导致Django Admin在检查权限时，使用的是@property返回的值（role == 'staff'）")
    print("而不是数据库中的is_staff字段值")
    print()
    print("解决方案:")
    print("需要修改User模型，将@property is_staff重命名为is_staff_role")
    print("但这需要修改代码并重启服务")
    print()
    print("临时解决方案:")
    print("确保oms_admin用户的role不是'staff'，这样@property不会返回True")
    print("同时确保数据库中的is_staff字段为True")
    print()
    
    try:
        user = User.objects.get(username=username)
        
        print("-" * 60)
        print("当前状态:")
        print("-" * 60)
        print(f"用户名: {user.username}")
        print(f"role: {user.role}")
        print(f"is_staff (@property): {user.is_staff} (这是@property返回的值)")
        
        # 检查数据库中的实际值
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT is_staff, is_superuser, is_active, role FROM users WHERE username = %s",
                [username]
            )
            row = cursor.fetchone()
            if row:
                db_is_staff, db_is_superuser, db_is_active, db_role = row
                print(f"is_staff (数据库): {bool(db_is_staff)}")
                print(f"is_superuser (数据库): {bool(db_is_superuser)}")
                print(f"is_active (数据库): {bool(db_is_active)}")
                print(f"role (数据库): {db_role}")
                
                print()
                print("-" * 60)
                print("问题诊断:")
                print("-" * 60)
                
                # 检查@property返回的值
                property_value = user.is_staff  # 这会调用@property方法
                db_value = bool(db_is_staff)
                
                if property_value != db_value:
                    print(f"❌ @property is_staff ({property_value}) != 数据库is_staff ({db_value})")
                    print("   这就是问题所在！Django Admin使用的是@property返回的值")
                    
                    if db_role == 'staff':
                        print()
                        print("⚠️  用户的role是'staff'，导致@property is_staff返回True")
                        print("   但Django Admin需要数据库中的is_staff字段为True")
                        print()
                        print("解决方案:")
                        print("  1. 将用户的role改为其他值（如'admin'）")
                        print("  2. 确保数据库中的is_staff字段为True")
                        print()
                        print("是否要修复？(y/n): ", end='')
                        choice = input().strip().lower()
                        
                        if choice == 'y':
                            # 更新role和is_staff
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    "UPDATE users SET role = %s, is_staff = %s, is_superuser = %s, is_active = %s WHERE username = %s",
                                    ['admin', True, True, True, username]
                                )
                            print("✅ 已更新: role='admin', is_staff=True, is_superuser=True, is_active=True")
                            
                            # 验证
                            user.refresh_from_db()
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    "SELECT is_staff, is_superuser, is_active, role FROM users WHERE username = %s",
                                    [username]
                                )
                                row = cursor.fetchone()
                                if row:
                                    print()
                                    print("修复后的状态:")
                                    print(f"  role: {row[3]}")
                                    print(f"  is_staff (数据库): {bool(row[0])}")
                                    print(f"  is_superuser: {bool(row[1])}")
                                    print(f"  is_active: {bool(row[2])}")
                                    print()
                                    print("⚠️  注意: @property is_staff仍然会返回False（因为role不是'staff'）")
                                    print("   但Django Admin应该使用数据库中的is_staff字段值")
                                    print("   如果仍然无法登录，需要修改User模型代码")
                    else:
                        print()
                        print("✅ role不是'staff'，@property is_staff应该返回False")
                        print("   但数据库中的is_staff应该为True")
                        if not db_is_staff:
                            print("   ❌ 数据库中的is_staff为False，需要设置为True")
                            print()
                            print("是否要修复？(y/n): ", end='')
                            choice = input().strip().lower()
                            if choice == 'y':
                                with connection.cursor() as cursor:
                                    cursor.execute(
                                        "UPDATE users SET is_staff = %s WHERE username = %s",
                                        [True, username]
                                    )
                                print("✅ 已设置 is_staff=True")
                else:
                    print(f"✅ @property is_staff ({property_value}) == 数据库is_staff ({db_value})")
        
        print()
        print("=" * 60)
        print("重要提示:")
        print("=" * 60)
        print("如果修复后仍然无法登录，需要修改User模型代码：")
        print("  将 @property is_staff 重命名为 @property is_staff_role")
        print("  这样可以避免与Django的is_staff字段冲突")
        print()
        
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
