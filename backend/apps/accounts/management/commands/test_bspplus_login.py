"""
测试Bspplus登录接口，验证返回的用户信息结构
使用方法：
    python manage.py test_bspplus_login <username> <password>
    
示例：
    python manage.py test_bspplus_login zhouxiangyu your_password
"""
from django.core.management.base import BaseCommand, CommandError
from apps.accounts.bspplus_service import BspplusService
import json


class Command(BaseCommand):
    help = '测试Bspplus登录接口，验证返回的用户信息结构（特别是role字段）'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='登录用户名')
        parser.add_argument('password', type=str, help='登录密码')
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='显示详细的调试信息',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        verbose = options.get('verbose', False)

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('Bspplus登录接口测试'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # 步骤1：显示配置信息
        self.stdout.write(self.style.WARNING('步骤1：检查配置信息'))
        from django.conf import settings
        api_root = getattr(settings, 'BSPPLUS_API_ROOT', None)
        app_code = getattr(settings, 'BSPPLUS_APP_CODE', None)
        
        self.stdout.write(f'  BSPPLUS_API_ROOT: {api_root}')
        self.stdout.write(f'  BSPPLUS_APP_CODE: {app_code}')
        self.stdout.write('')

        if not api_root or not app_code:
            raise CommandError('BSPPLUS_API_ROOT 或 BSPPLUS_APP_CODE 未配置！')

        # 步骤2：调用Bspplus登录接口
        self.stdout.write(self.style.WARNING('步骤2：调用Bspplus登录接口'))
        self.stdout.write(f'  用户名: {username}')
        self.stdout.write(f'  密码: {"*" * len(password)} (已隐藏)')
        self.stdout.write(f'  接口地址: {api_root}/user/login')
        self.stdout.write('')

        try:
            bspplus_result = BspplusService.login(username, password)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ 调用接口时发生异常: {str(e)}'))
            raise CommandError(f'接口调用失败: {str(e)}')

        # 步骤3：检查登录结果
        self.stdout.write(self.style.WARNING('步骤3：检查登录结果'))
        success = bspplus_result.get('success', False)
        flag = bspplus_result.get('flag', False)
        msg = bspplus_result.get('msg', '')

        if success:
            self.stdout.write(self.style.SUCCESS(f'  ✅ 接口调用成功'))
        else:
            self.stdout.write(self.style.ERROR(f'  ❌ 接口调用失败: {msg}'))
            return

        if flag:
            self.stdout.write(self.style.SUCCESS(f'  ✅ 登录成功 (flag=True)'))
        else:
            self.stdout.write(self.style.ERROR(f'  ❌ 登录失败 (flag=False): {msg}'))
            return

        self.stdout.write('')

        # 步骤4：检查用户信息
        self.stdout.write(self.style.WARNING('步骤4：检查返回的用户信息'))
        bspplus_user_data = bspplus_result.get('user', {})

        if not bspplus_user_data:
            self.stdout.write(self.style.ERROR('  ❌ 用户信息为空！'))
            return

        self.stdout.write(self.style.SUCCESS(f'  ✅ 用户信息存在，包含 {len(bspplus_user_data)} 个字段'))
        self.stdout.write('')

        # 步骤5：详细检查关键字段
        self.stdout.write(self.style.WARNING('步骤5：检查关键字段'))
        
        # 检查username
        username_field = bspplus_user_data.get('username')
        if username_field:
            self.stdout.write(self.style.SUCCESS(f'  ✅ username: {username_field}'))
        else:
            self.stdout.write(self.style.ERROR('  ❌ username: 缺失'))

        # 检查name
        name_field = bspplus_user_data.get('name')
        if name_field:
            self.stdout.write(self.style.SUCCESS(f'  ✅ name: {name_field}'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  name: 缺失或为空'))

        # 检查mobile（重要）
        mobile_field = bspplus_user_data.get('mobile')
        if mobile_field:
            self.stdout.write(self.style.SUCCESS(f'  ✅ mobile: {mobile_field}'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  mobile: 缺失或为空'))

        # 检查phone（可能为空）
        phone_field = bspplus_user_data.get('phone')
        if phone_field:
            self.stdout.write(self.style.SUCCESS(f'  ✅ phone: {phone_field}'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  phone: 缺失或为空'))

        # 检查organName
        organ_name_field = bspplus_user_data.get('organName')
        if organ_name_field:
            self.stdout.write(self.style.SUCCESS(f'  ✅ organName: {organ_name_field}'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  organName: 缺失或为空'))

        # 检查regionName
        region_name_field = bspplus_user_data.get('regionName')
        if region_name_field:
            self.stdout.write(self.style.SUCCESS(f'  ✅ regionName: {region_name_field}'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  regionName: 缺失或为空'))

        # 检查email
        email_field = bspplus_user_data.get('email')
        if email_field:
            self.stdout.write(self.style.SUCCESS(f'  ✅ email: {email_field}'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  email: 缺失或为空'))

        # 检查role（重点）
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('  🔍 重点检查：role字段'))
        role_field = bspplus_user_data.get('role')
        
        if role_field:
            self.stdout.write(self.style.SUCCESS(f'  ✅ role字段存在'))
            self.stdout.write(self.style.SUCCESS(f'  ✅ role值: {role_field}'))
            self.stdout.write(self.style.SUCCESS(f'  ✅ role类型: {type(role_field).__name__}'))
            self.stdout.write(f'  ✅ role长度: {len(str(role_field))} 字符')
            
            # 检查role值是否包含关键角色
            role_str = str(role_field).upper()
            if 'PM' in role_str:
                self.stdout.write(self.style.SUCCESS(f'  ✅ 包含PM角色'))
            if 'AUDITOR' in role_str:
                self.stdout.write(self.style.SUCCESS(f'  ✅ 包含AUDITOR角色'))
            if 'REQUESTER' in role_str:
                self.stdout.write(self.style.SUCCESS(f'  ✅ 包含REQUESTER角色'))
            if 'STAFF' in role_str:
                self.stdout.write(self.style.SUCCESS(f'  ✅ 包含STAFF角色'))
        else:
            self.stdout.write(self.style.ERROR('  ❌ role字段缺失！'))
            self.stdout.write(self.style.ERROR('  ❌ 这是导致角色解析失败的根本原因！'))

        self.stdout.write('')

        # 步骤6：测试角色解析
        if role_field:
            self.stdout.write(self.style.WARNING('步骤6：测试角色解析'))
            system_role = BspplusService._parse_role(role_field)
            self.stdout.write(f'  输入role值: {role_field}')
            self.stdout.write(f'  解析后角色: {system_role}')
            
            # 显示角色映射
            role_mapping = {
                'admin': '管理方',
                'manager': '承建方-项目经理',
                'user': '使用方',
                'employee': '承建方-员工',
            }
            role_display = role_mapping.get(system_role, '未知角色')
            self.stdout.write(f'  角色显示名: {role_display}')
            
            if system_role == 'user':
                self.stdout.write(self.style.WARNING('  ⚠️  解析结果为默认角色"user"，可能未匹配到有效角色'))
            else:
                self.stdout.write(self.style.SUCCESS(f'  ✅ 角色解析成功'))
            
            self.stdout.write('')

        # 步骤7：显示完整的用户信息（可选）
        if verbose:
            self.stdout.write(self.style.WARNING('步骤7：完整的用户信息（详细模式）'))
            self.stdout.write(json.dumps(bspplus_user_data, indent=2, ensure_ascii=False))
            self.stdout.write('')

        # 步骤8：总结
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('测试总结'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        if role_field:
            self.stdout.write(self.style.SUCCESS('✅ role字段存在，值为: ' + str(role_field)))
            self.stdout.write(self.style.SUCCESS('✅ 角色解析结果: ' + system_role))
        else:
            self.stdout.write(self.style.ERROR('❌ role字段缺失！'))
            self.stdout.write(self.style.ERROR('❌ 需要检查Bspplus接口返回的数据结构'))
        
        self.stdout.write('')
