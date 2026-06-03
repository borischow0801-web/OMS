"""
Bspplus服务类，用于调用Bspplus通用用户登录接口
"""
import requests
import logging
import hashlib
import re
from django.conf import settings
from django.db import transaction
from .models import User

logger = logging.getLogger(__name__)


class BspplusService:
    """Bspplus服务类"""
    
    # 角色映射：Bspplus返回的角色值 -> 系统内部角色值（使用旧角色值以兼容）
    # 映射关系说明：
    # - AUDITOR（审核方）-> admin（管理方/审核方）
    # - PM（项目经理）-> manager（承建方-项目经理/项目经理）
    # - REQUESTER（提出方）-> user（使用方/提出方）
    # - STAFF（员工）-> employee（承建方-员工/员工）
    # 注意：使用旧角色值（admin, manager, user, employee）以兼容现有系统
    ROLE_MAPPING = {
        'AUDITOR': 'admin',         # 审核方（即管理方）
        'PM': 'manager',            # 项目经理（即承建方-项目经理）
        'REQUESTER': 'user',        # 提出方（即使用方）
        'STAFF': 'employee',        # 员工（即承建方-员工）
    }
    
    @classmethod
    def _parse_role(cls, role_str):
        """
        解析Bspplus返回的角色字段
        如果包含多个角色（用逗号分隔），检查是否包含PM、STAFF、AUDITOR、REQUESTER
        只要role字符串中包含这些关键词，就识别为对应角色
        其他值忽略
        
        Args:
            role_str: Bspplus返回的角色字符串，例如："ROLE_MAINTEN,PM,ROLE_SYSTEM"
            
        Returns:
            str: 映射后的系统角色值（使用旧角色值：admin, manager, user, employee）
                 如果都不包含则返回'user'（使用方）
        """
        if not role_str:
            logger.error(f"[角色解析] role字符串为空，返回默认角色'user'")
            return 'user'
        
        # 转换为字符串，去除首尾空格
        role_str = str(role_str).strip()
        role_str_upper = role_str.upper()  # 转换为大写进行匹配
        
        logger.error(f"[角色解析] 开始解析role字符串: '{role_str}' (大写: '{role_str_upper}')")
        
        # 优先顺序：AUDITOR（审核方/管理方）> PM（项目经理）> REQUESTER（提出方/使用方）> STAFF（员工）
        # 只要role字符串中包含这些关键词，就识别为对应角色
        priority_roles = ['AUDITOR', 'PM', 'REQUESTER', 'STAFF']
        
        # 遍历优先顺序，检查role字符串是否包含该关键词
        for priority_role in priority_roles:
            # 检查是否包含该角色关键词（注意：PM需要精确匹配，避免匹配到其他包含PM的字符串）
            if priority_role == 'PM':
                # PM需要精确匹配（不能匹配到COMP、ROLE_SYSTEM等）
                # 使用单词边界匹配：检查是否包含",PM,"或"PM,"或",PM"或"^PM$"
                pm_pattern = r'(^|[,;])PM([,;]|$)'
                if re.search(pm_pattern, role_str_upper):
                    mapped_role = cls.ROLE_MAPPING.get(priority_role, 'user')
                    logger.error(f"[角色解析] 识别角色: '{priority_role}' (从 '{role_str}') -> '{mapped_role}'")
                    return mapped_role
            else:
                # 其他角色关键词匹配
                if priority_role in role_str_upper:
                    mapped_role = cls.ROLE_MAPPING.get(priority_role, 'user')
                    logger.error(f"[角色解析] 识别角色: '{priority_role}' (从 '{role_str}') -> '{mapped_role}'")
                    return mapped_role
        
        # 都不包含，返回默认值（使用方）
        logger.error(f"[角色解析] role字符串 '{role_str}' 中未找到有效角色（AUDITOR/PM/REQUESTER/STAFF），使用默认角色'user'（使用方）")
        return 'user'
    
    @classmethod
    def login(cls, username, password):
        """
        调用Bspplus登录接口
        
        Args:
            username: 用户名
            password: 密码（需要加密）
            
        Returns:
            dict: {
                'success': bool,
                'flag': bool,
                'user': dict,  # Bspplus返回的用户信息
                'token': str,
                'refreshToken': str,
                'msg': str,  # 错误信息
            }
        """
        api_root = settings.BSPPLUS_API_ROOT
        app_code = settings.BSPPLUS_APP_CODE
        login_url = f"{api_root}/user/login"
        
        try:
            # 根据接口文档，password需要MD5加密
            # 如果密码已经是32位MD5字符串，则不重复加密；否则进行MD5加密
            if len(password) == 32 and all(c in '0123456789abcdef' for c in password.lower()):
                # 已经是MD5格式，直接使用
                encrypted_password = password
            else:
                # 进行MD5加密
                encrypted_password = hashlib.md5(password.encode('utf-8')).hexdigest()
            
            payload = {
                'username': username,
                'password': encrypted_password,
                'appCode': app_code,
            }
            
            response = requests.post(
                login_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 检查返回状态
            data = result.get('data', {})
            flag = data.get('flag', False)
            
            if result.get('status') == 200 and flag is True:
                return {
                    'success': True,
                    'flag': True,
                    'user': data.get('user', {}),
                    'token': data.get('token', ''),
                    'refreshToken': data.get('refreshToken', ''),
                    'msg': result.get('msg', 'ok'),
                }
            else:
                # 登录失败
                # 如果msg是"ok"或为空，使用更明确的错误提示
                msg = result.get('msg', '')
                if not msg or msg.lower() == 'ok':
                    msg = '账号或密码错误'
                return {
                    'success': False,
                    'flag': False,
                    'user': None,
                    'token': None,
                    'refreshToken': None,
                    'msg': msg,
                }
                
        except requests.exceptions.RequestException as e:
            # 网络异常（连接失败、超时等），标记为网络错误，允许回退到本地认证
            logger.error(f"Bspplus登录接口调用失败（网络异常）: {str(e)}")
            return {
                'success': False,
                'flag': False,
                'user': None,
                'token': None,
                'refreshToken': None,
                'msg': f'登录服务异常: {str(e)}',  # 消息以'登录服务异常'开头，用于标识网络错误
                'is_network_error': True,  # 标记为网络错误
            }
        except Exception as e:
            # 其他异常，标记为网络错误，允许回退到本地认证
            logger.error(f"Bspplus登录处理异常: {str(e)}")
            return {
                'success': False,
                'flag': False,
                'user': None,
                'token': None,
                'refreshToken': None,
                'msg': f'登录处理异常: {str(e)}',  # 消息以'登录处理异常'开头，用于标识网络错误
                'is_network_error': True,  # 标记为网络错误
            }
    
    @classmethod
    def sync_user_from_bspplus(cls, bspplus_user_data):
        """
        根据Bspplus返回的用户信息同步到本地数据库
        如果用户不存在则创建，如果存在则更新（手机号、姓名、部门、区划）
        
        Args:
            bspplus_user_data: Bspplus返回的用户信息字典
            
        Returns:
            User: 同步后的用户对象
        """
        username = bspplus_user_data.get('username')
        if not username:
            logger.error("Bspplus用户数据缺少username字段")
            return None
        
        # 特殊处理：oms_admin用户不应该被Bspplus同步逻辑影响
        # 保持其原有密码和权限不变
        if username == 'oms_admin':
            try:
                user = User.objects.get(username=username)
                logger.info(f"跳过oms_admin用户的Bspplus同步，保持原有配置")
                return user
            except User.DoesNotExist:
                # 如果oms_admin不存在，也不应该通过Bspplus创建
                logger.warning(f"oms_admin用户不存在，但不通过Bspplus创建")
                return None
        
        try:
            with transaction.atomic():
                # 映射角色（先解析角色，用于创建和更新）
                # 注意：role字段可能包含多个角色，用逗号或其他分隔符分隔
                # 只取PM、STAFF、AUDITOR、REQUESTER中的第一个有效值
                bspplus_role = bspplus_user_data.get('role', '')
                system_role = cls._parse_role(bspplus_role)
                logger.error(f"[用户同步] 用户 {username} 角色解析结果: '{bspplus_role}' -> '{system_role}'")
                
                # 获取或创建用户
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': bspplus_user_data.get('name', ''),
                        'phone': bspplus_user_data.get('mobile', '') or bspplus_user_data.get('phone', ''),
                        'department': bspplus_user_data.get('organName', ''),
                        'region_name': bspplus_user_data.get('regionName', ''),
                        'email': bspplus_user_data.get('email', ''),
                        'role': system_role,  # 设置角色
                        'is_active': True,
                    }
                )
                
                # 如果是新创建的用户，设置不可用密码（防止通过Django Admin登录）
                # 后台登录应该使用独立的认证方式，不受Bspplus影响
                if created:
                    user.set_unusable_password()
                    user.save()
                    logger.info(f"新用户 {username} 已创建，角色: '{system_role}'")
                
                # 如果用户已存在，检查并更新变更的字段
                if not created:
                    updated = False
                    
                    # 更新手机号（确保同步，即使为空也更新）
                    # 优先使用mobile字段，如果没有则使用phone字段
                    new_phone = bspplus_user_data.get('mobile', '') or bspplus_user_data.get('phone', '') or ''
                    current_phone = user.phone or ''
                    if current_phone != new_phone:
                        user.phone = new_phone
                        updated = True
                        logger.debug(f"用户 {username} 手机号更新: '{current_phone}' -> '{new_phone}'")
                    
                    # 更新姓名
                    new_name = bspplus_user_data.get('name', '') or ''
                    current_name = user.first_name or ''
                    if current_name != new_name:
                        user.first_name = new_name
                        updated = True
                        logger.debug(f"用户 {username} 姓名更新: '{current_name}' -> '{new_name}'")
                    
                    # 更新部门
                    new_department = bspplus_user_data.get('organName', '') or ''
                    current_department = user.department or ''
                    if current_department != new_department:
                        user.department = new_department
                        updated = True
                        logger.debug(f"用户 {username} 部门更新: '{current_department}' -> '{new_department}'")
                    
                    # 更新区划名称（确保同步，即使为空也更新）
                    new_region_name = bspplus_user_data.get('regionName', '') or ''
                    current_region_name = user.region_name or ''
                    if current_region_name != new_region_name:
                        user.region_name = new_region_name
                        updated = True
                        logger.debug(f"用户 {username} 区划名称更新: '{current_region_name}' -> '{new_region_name}'")
                    
                    # 更新邮箱
                    new_email = bspplus_user_data.get('email', '') or ''
                    current_email = user.email or ''
                    if current_email != new_email:
                        user.email = new_email
                        updated = True
                        logger.debug(f"用户 {username} 邮箱更新: '{current_email}' -> '{new_email}'")
                    
                    # 更新角色
                    if user.role != system_role:
                        user.role = system_role
                        updated = True
                        logger.info(f"用户 {username} 角色更新: '{user.role}' -> '{system_role}'")
                    
                    if updated:
                        user.save()
                        logger.info(f"用户 {username} 信息已更新")
                
                return user
                
        except Exception as e:
            logger.error(f"同步用户信息失败: {str(e)}")
            return None
