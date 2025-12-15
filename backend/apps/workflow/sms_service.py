"""
短信发送服务
"""
import requests
import json
import logging
from urllib.parse import urlencode, quote
from typing import Optional, Dict, Any
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from datetime import timedelta
from .models import SmsConfig, SmsTemplate, SmsRecord
from apps.tasks.models import Task
from apps.accounts.models import User

logger = logging.getLogger(__name__)


class SmsService:
    """短信发送服务类"""
    
    @staticmethod
    def get_config() -> Optional[SmsConfig]:
        """获取启用的短信配置"""
        try:
            return SmsConfig.objects.filter(is_enabled=True).first()
        except Exception as e:
            logger.error(f'获取短信配置失败: {e}')
            return None
    
    @staticmethod
    def get_template(template_type: str) -> Optional[SmsTemplate]:
        """获取启用的短信模板"""
        try:
            return SmsTemplate.objects.filter(
                template_type=template_type,
                is_enabled=True
            ).first()
        except Exception as e:
            logger.error(f'获取短信模板失败: {e}')
            return None
    
    @staticmethod
    def format_template_content(template_content: str, context: Dict[str, Any]) -> str:
        """格式化模板内容
        
        Args:
            template_content: 模板内容，包含占位符如{任务标题}
            context: 上下文变量字典
            
        Returns:
            格式化后的内容
        """
        content = template_content
        for key, value in context.items():
            placeholder = f'{{{key}}}'
            content = content.replace(placeholder, str(value) if value else '')
        return content
    
    @staticmethod
    def _check_duplicate_sms(
        phone: str,
        template_type: Optional[str] = None,
        task: Optional[Task] = None,
        recipient: Optional[User] = None,
        time_window_minutes: int = 5
    ) -> bool:
        """检查是否在短时间内重复发送相同的短信
        
        Args:
            phone: 手机号
            template_type: 模板类型
            task: 关联的任务
            recipient: 接收人
            time_window_minutes: 时间窗口（分钟），在这个时间内的相同短信视为重复
            
        Returns:
            True表示是重复发送，False表示不是重复
        """
        # 构建查询条件
        time_threshold = timezone.now() - timedelta(minutes=time_window_minutes)
        
        query = Q(phone=phone.strip(), created_at__gte=time_threshold)
        
        # 如果有关联任务和模板类型，检查是否有相同的任务+模板类型组合
        if task and template_type:
            query &= Q(task=task, template_type=template_type)
            if recipient:
                query &= Q(recipient=recipient)
        
        # 检查是否有成功或待发送的记录
        existing = SmsRecord.objects.filter(
            query,
            status__in=['success', 'pending']
        ).exists()
        
        if existing:
            logger.warning(
                f'[重复发送检查] 手机号: {phone}, '
                f'任务ID: {task.id if task else None}, '
                f'模板类型: {template_type}, '
                f'在最近{time_window_minutes}分钟内已发送过相同短信，跳过发送'
            )
            return True
        
        return False
    
    @staticmethod
    def send_sms(
        phone: str,
        content: str,
        template_type: Optional[str] = None,
        task: Optional[Task] = None,
        recipient: Optional[User] = None
    ) -> bool:
        """发送短信
        
        Args:
            phone: 手机号
            content: 短信内容
            template_type: 模板类型
            task: 关联的任务
            recipient: 接收人
            
        Returns:
            是否发送成功
        """
        # 验证手机号
        phone = phone.strip() if phone else ''
        if not phone:
            logger.warning(f'手机号为空，无法发送短信')
            return False
        
        # 防止重复发送：检查是否在短时间内已经发送过相同的短信
        if SmsService._check_duplicate_sms(phone, template_type, task, recipient):
            return False
        
        # 获取短信配置
        sms_config = SmsService.get_config()
        if not sms_config:
            error_msg = '未配置短信接口或配置已禁用'
            logger.warning(error_msg)
            # 创建失败记录
            SmsRecord.objects.create(
                phone=phone,
                content=content,
                template_type=template_type,
                task=task,
                recipient=recipient,
                status='failed',
                error_message=error_msg
            )
            return False
        
        # 创建发送记录（使用事务确保原子性）
        with transaction.atomic():
            # 再次检查是否有其他进程已经创建了相同的记录（双重检查）
            if SmsService._check_duplicate_sms(phone, template_type, task, recipient, time_window_minutes=1):
                return False
            
            sms_record = SmsRecord.objects.create(
                phone=phone,
                content=content,
                template_type=template_type,
                task=task,
                recipient=recipient,
                status='pending'
            )
        
        try:
            # 构建请求参数（POST请求，但参数通过URL查询字符串传递）
            api_params = sms_config.get_api_params().copy()
            
            # 构建查询参数字典
            query_params = {}
            for key, value in api_params.items():
                if isinstance(value, str):
                    # 替换占位符
                    formatted_value = value.replace('{phone}', phone)
                    formatted_value = formatted_value.replace('{content}', content)
                    query_params[key] = formatted_value
                else:
                    query_params[key] = str(value)
            
            # 如果没有配置参数，使用默认参数名和固定值
            if not query_params:
                query_params = {
                    'phoneNum': phone,
                    'mesConent': content,
                    'regionCode': '371000000000',
                    'source': 'oms'
                }
            
            # 构建完整的URL（POST请求，但参数在URL查询字符串中）
            base_url = sms_config.api_url.rstrip('?&')
            # 检查URL中是否已有查询参数
            separator = '&' if '?' in base_url else '?'
            full_url = f"{base_url}{separator}{urlencode(query_params)}"
            
            # 记录请求信息到日志
            logger.info(
                f'[短信发送请求] 手机号: {phone}, '
                f'请求方式: POST, '
                f'完整URL: {full_url}, '
                f'查询参数: {json.dumps(query_params, ensure_ascii=False)}'
            )
            
            # 发送HTTP POST请求（参数在URL中，不是JSON body）
            response = requests.post(
                full_url,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            # 记录响应
            response_data = None
            try:
                response_data = response.json()
                sms_record.response_data = json.dumps(response_data, ensure_ascii=False)
            except:
                response_text = response.text[:1000]  # 限制长度
                sms_record.response_data = response_text
            
            # 记录响应信息到日志
            logger.info(
                f'[短信发送响应] 记录ID: {sms_record.id}, 手机号: {phone}, '
                f'HTTP状态码: {response.status_code}, '
                f'响应内容: {sms_record.response_data}'
            )
            
            # 判断是否成功
            # 1. HTTP状态码必须是200
            if response.status_code != 200:
                error_msg = f'短信接口返回错误HTTP状态码: {response.status_code}'
                sms_record.status = 'failed'
                sms_record.error_message = error_msg
                sms_record.save()
                logger.error(f'[短信发送失败] 记录ID: {sms_record.id}, 手机号: {phone}, 原因: {error_msg}')
                return False
            
            # 2. 检查响应体内容
            if response_data:
                # 检查 code 字段，正常应该是 "200"（根据图片中的响应格式）
                code = response_data.get('code', '')
                
                if code == '200':
                    # 发送成功
                    sms_record.status = 'success'
                    sms_record.sent_at = timezone.now()
                    sms_record.save()
                    logger.info(f'[短信发送成功] 记录ID: {sms_record.id}, 手机号: {phone}, code: {code}')
                    return True
                else:
                    # 发送失败，记录错误信息
                    error_msg = f'短信接口返回失败: code={code}'
                    sms_record.status = 'failed'
                    sms_record.error_message = error_msg
                    sms_record.save()
                    logger.error(f'[短信发送失败] 记录ID: {sms_record.id}, 手机号: {phone}, 原因: {error_msg}')
                    return False
            else:
                # 响应体不是JSON格式，尝试从文本中判断
                # 如果HTTP状态码是200但没有JSON响应，认为可能成功，但记录警告
                sms_record.status = 'success'
                sms_record.sent_at = timezone.now()
                sms_record.save()
                logger.warning(
                    f'[短信发送警告] 记录ID: {sms_record.id}, 手机号: {phone}, '
                    f'HTTP状态码200但响应体不是JSON格式，已标记为成功，请人工检查'
                )
                return True
                
        except requests.exceptions.Timeout:
            error_msg = '短信接口请求超时'
            sms_record.status = 'failed'
            sms_record.error_message = error_msg
            sms_record.save()
            logger.error(f'短信发送失败: {phone}, {error_msg}')
            return False
        except requests.exceptions.RequestException as e:
            error_msg = f'短信接口请求异常: {str(e)}'
            sms_record.status = 'failed'
            sms_record.error_message = error_msg
            sms_record.save()
            logger.error(f'短信发送失败: {phone}, {error_msg}')
            return False
        except Exception as e:
            error_msg = f'发送短信时发生未知错误: {str(e)}'
            sms_record.status = 'failed'
            sms_record.error_message = error_msg
            sms_record.save()
            logger.error(f'短信发送失败: {phone}, {error_msg}')
            return False
    
    @staticmethod
    def send_task_sms(
        template_type: str,
        task: Task,
        recipient: Optional[User] = None,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """发送任务相关短信
        
        Args:
            template_type: 模板类型
            task: 任务对象
            recipient: 接收人（如果为None，则根据模板类型自动确定）
            extra_context: 额外的上下文变量
            
        Returns:
            是否发送成功
        """
        # 获取模板
        template = SmsService.get_template(template_type)
        if not template:
            error_msg = f'未找到启用的短信模板: {template_type}'
            logger.warning(f'{error_msg} (任务ID: {task.id if task else "未知"})')
            # 创建失败记录
            if task:
                SmsRecord.objects.create(
                    phone='',
                    content='',
                    template_type=template_type,
                    task=task,
                    recipient=recipient,
                    status='failed',
                    error_message=error_msg
                )
            return False
        
        # 确定接收人
        if not recipient:
            recipient = SmsService._get_default_recipient(template_type, task)
        
        if not recipient:
            error_msg = f'无法确定短信接收人: {template_type}'
            logger.warning(f'{error_msg} (任务ID: {task.id if task else "未知"})')
            # 创建失败记录
            if task and template:
                context = {
                    '任务标题': task.title,
                    '任务名称': task.title,
                }
                if extra_context:
                    context.update(extra_context)
                content = SmsService.format_template_content(template.content, context)
                SmsRecord.objects.create(
                    phone='',
                    content=content,
                    template_type=template_type,
                    task=task,
                    status='failed',
                    error_message=error_msg
                )
            return False
        
        # 检查接收人是否有手机号
        if not recipient or not recipient.phone:
            username = recipient.username if recipient else "未知"
            task_id = task.id if task else "未知"
            error_msg = f'接收人 {username} 未设置手机号，无法发送短信'
            logger.warning(f'{error_msg} (任务ID: {task_id})')
            # 创建失败记录
            if task and template:
                context = {
                    '任务标题': task.title,
                    '任务名称': task.title,
                }
                if extra_context:
                    context.update(extra_context)
                content = SmsService.format_template_content(template.content, context)
                SmsRecord.objects.create(
                    phone='',
                    content=content,
                    template_type=template_type,
                    task=task,
                    recipient=recipient,
                    status='failed',
                    error_message=error_msg
                )
            return False
        
        # 构建上下文
        context = {
            '任务标题': task.title,
            '任务名称': task.title,
        }
        
        # 添加额外上下文
        if extra_context:
            context.update(extra_context)
        
        # 格式化内容
        content = SmsService.format_template_content(template.content, context)
        
        # 发送短信
        return SmsService.send_sms(
            phone=recipient.phone,
            content=content,
            template_type=template_type,
            task=task,
            recipient=recipient
        )
    
    @staticmethod
    def _get_default_recipient(template_type: str, task: Task) -> Optional[User]:
        """根据模板类型和任务获取默认接收人"""
        from apps.accounts.models import User
        
        if template_type == 'task_submitted':
            # 任务提交后，给所有管理方发送
            admins = User.objects.filter(role='admin', is_active=True, phone__isnull=False).exclude(phone='')
            return admins.first()  # 如果有多个管理方，发送给第一个，后续可以改为批量发送
        elif template_type == 'task_reviewed':
            # 任务审核通过后，给项目经理发送
            return task.assignee if task.assignee else None
        elif template_type == 'task_reviewed_rejected':
            # 任务审核不通过后，给创建者发送
            return task.creator
        elif template_type == 'task_assigned':
            # 任务分配后，给处理员工发送
            return task.handler
        elif template_type == 'task_completed':
            # 任务完成后，给创建者发送
            return task.creator
        else:
            return None
    
    @staticmethod
    def send_task_submitted_sms(task: Task) -> bool:
        """发送任务提交短信给所有管理方"""
        from apps.accounts.models import User
        
        template = SmsService.get_template('task_submitted')
        if not template:
            logger.warning(f'未找到启用的任务提交短信模板 (任务ID: {task.id})')
            # 创建失败记录
            SmsRecord.objects.create(
                phone='',
                content='',
                template_type='task_submitted',
                task=task,
                status='failed',
                error_message='未找到启用的任务提交短信模板'
            )
            return False
        
        # 获取所有管理方（包括没有手机号的，用于记录）
        all_admins = User.objects.filter(role='admin', is_active=True)
        admins_with_phone = all_admins.filter(phone__isnull=False).exclude(phone='')
        
        if admins_with_phone.count() == 0:
            # 没有可发送的管理方用户，创建失败记录
            error_msg = '没有找到可发送短信的管理方用户（管理方用户未设置手机号）'
            logger.warning(f'{error_msg} (任务ID: {task.id})')
            
            # 为每个管理方用户创建一条失败记录
            context = {
                '任务标题': task.title,
                '任务名称': task.title,
            }
            content = SmsService.format_template_content(template.content, context)
            
            for admin in all_admins:
                SmsRecord.objects.create(
                    phone=admin.phone or '',
                    content=content,
                    template_type='task_submitted',
                    task=task,
                    recipient=admin,
                    status='failed',
                    error_message=f'管理方用户 {admin.username} 未设置手机号'
                )
            return False
        
        success_count = 0
        context = {
            '任务标题': task.title,
            '任务名称': task.title,
        }
        content = SmsService.format_template_content(template.content, context)
        
        for admin in admins_with_phone:
            if SmsService.send_sms(
                phone=admin.phone,
                content=content,
                template_type='task_submitted',
                task=task,
                recipient=admin
            ):
                success_count += 1
        
        return success_count > 0
    
    @staticmethod
    def send_task_reviewed_sms(task: Task) -> bool:
        """发送任务审核通过短信给所有项目经理"""
        from apps.accounts.models import User
        
        template = SmsService.get_template('task_reviewed')
        if not template:
            logger.warning(f'未找到启用的任务审核通过短信模板 (任务ID: {task.id})')
            # 创建失败记录
            SmsRecord.objects.create(
                phone='',
                content='',
                template_type='task_reviewed',
                task=task,
                status='failed',
                error_message='未找到启用的任务审核通过短信模板'
            )
            return False
        
        # 获取所有项目经理（包括没有手机号的，用于记录）
        all_managers = User.objects.filter(role='manager', is_active=True)
        managers_with_phone = all_managers.filter(phone__isnull=False).exclude(phone='')
        
        if managers_with_phone.count() == 0:
            # 没有可发送的项目经理，创建失败记录
            error_msg = '没有找到可发送短信的项目经理（项目经理未设置手机号）'
            logger.warning(f'{error_msg} (任务ID: {task.id})')
            
            # 为每个项目经理创建一条失败记录
            context = {
                '任务标题': task.title,
                '任务名称': task.title,
            }
            content = SmsService.format_template_content(template.content, context)
            
            for manager in all_managers:
                SmsRecord.objects.create(
                    phone=manager.phone or '',
                    content=content,
                    template_type='task_reviewed',
                    task=task,
                    recipient=manager,
                    status='failed',
                    error_message=f'项目经理 {manager.username} 未设置手机号'
                )
            return False
        
        success_count = 0
        context = {
            '任务标题': task.title,
            '任务名称': task.title,
        }
        content = SmsService.format_template_content(template.content, context)
        
        for manager in managers_with_phone:
            if SmsService.send_sms(
                phone=manager.phone,
                content=content,
                template_type='task_reviewed',
                task=task,
                recipient=manager
            ):
                success_count += 1
        
        return success_count > 0
    
    @staticmethod
    def resend_sms(sms_record) -> bool:
        """重发短信（更新现有记录）
        
        Args:
            sms_record: 要重发的短信记录对象
            
        Returns:
            是否发送成功
        """
        # 验证手机号
        if not sms_record.phone or not sms_record.phone.strip():
            logger.warning(f'手机号为空，无法重发短信 (ID: {sms_record.id})')
            sms_record.status = 'failed'
            sms_record.error_message = '手机号为空'
            sms_record.save()
            return False
        
        # 重置状态
        sms_record.status = 'pending'
        sms_record.error_message = None
        sms_record.response_data = None
        sms_record.sent_at = None
        sms_record.save()
        
        # 获取短信配置
        sms_config = SmsService.get_config()
        if not sms_config:
            error_msg = '未配置短信接口或配置已禁用'
            logger.warning(error_msg)
            sms_record.status = 'failed'
            sms_record.error_message = error_msg
            sms_record.save()
            return False
        
        try:
            # 构建请求参数（POST请求，但参数通过URL查询字符串传递）
            api_params = sms_config.get_api_params().copy()
            phone = sms_record.phone.strip()
            content = sms_record.content
            
            # 构建查询参数字典
            query_params = {}
            for key, value in api_params.items():
                if isinstance(value, str):
                    # 替换占位符
                    formatted_value = value.replace('{phone}', phone)
                    formatted_value = formatted_value.replace('{content}', content)
                    query_params[key] = formatted_value
                else:
                    query_params[key] = str(value)
            
            # 如果没有配置参数，使用默认参数名和固定值
            if not query_params:
                query_params = {
                    'phoneNum': phone,
                    'mesConent': content,
                    'regionCode': '371000000000',
                    'source': 'oms'
                }
            
            # 构建完整的URL（POST请求，但参数在URL查询字符串中）
            base_url = sms_config.api_url.rstrip('?&')
            # 检查URL中是否已有查询参数
            separator = '&' if '?' in base_url else '?'
            full_url = f"{base_url}{separator}{urlencode(query_params)}"
            
            # 记录请求信息到日志
            logger.info(
                f'[短信重发请求] 记录ID: {sms_record.id}, 手机号: {phone}, '
                f'请求方式: POST, '
                f'完整URL: {full_url}, '
                f'查询参数: {json.dumps(query_params, ensure_ascii=False)}'
            )
            
            # 发送HTTP POST请求（参数在URL中，不是JSON body）
            response = requests.post(
                full_url,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            # 记录响应
            response_data = None
            try:
                response_data = response.json()
                sms_record.response_data = json.dumps(response_data, ensure_ascii=False)
            except:
                response_text = response.text[:1000]  # 限制长度
                sms_record.response_data = response_text
            
            # 记录响应信息到日志
            logger.info(
                f'[短信重发响应] 记录ID: {sms_record.id}, 手机号: {phone}, '
                f'HTTP状态码: {response.status_code}, '
                f'响应内容: {sms_record.response_data}'
            )
            
            # 判断是否成功
            # 1. HTTP状态码必须是200
            if response.status_code != 200:
                error_msg = f'短信接口返回错误HTTP状态码: {response.status_code}'
                sms_record.status = 'failed'
                sms_record.error_message = error_msg
                sms_record.save()
                logger.error(f'[短信重发失败] 记录ID: {sms_record.id}, 手机号: {phone}, 原因: {error_msg}')
                return False
            
            # 2. 检查响应体内容
            if response_data:
                # 检查 code 字段，正常应该是 "200"（根据图片中的响应格式）
                code = response_data.get('code', '')
                
                if code == '200':
                    # 发送成功
                    sms_record.status = 'success'
                    sms_record.sent_at = timezone.now()
                    sms_record.save()
                    logger.info(f'[短信重发成功] 记录ID: {sms_record.id}, 手机号: {phone}, code: {code}')
                    return True
                else:
                    # 发送失败，记录错误信息
                    error_msg = f'短信接口返回失败: code={code}'
                    sms_record.status = 'failed'
                    sms_record.error_message = error_msg
                    sms_record.save()
                    logger.error(f'[短信重发失败] 记录ID: {sms_record.id}, 手机号: {phone}, 原因: {error_msg}')
                    return False
            else:
                # 响应体不是JSON格式，尝试从文本中判断
                # 如果HTTP状态码是200但没有JSON响应，认为可能成功，但记录警告
                sms_record.status = 'success'
                sms_record.sent_at = timezone.now()
                sms_record.save()
                logger.warning(
                    f'[短信重发警告] 记录ID: {sms_record.id}, 手机号: {phone}, '
                    f'HTTP状态码200但响应体不是JSON格式，已标记为成功，请人工检查'
                )
                return True
                
        except requests.exceptions.Timeout:
            error_msg = '短信接口请求超时'
            sms_record.status = 'failed'
            sms_record.error_message = error_msg
            sms_record.save()
            logger.error(f'短信重发失败: {sms_record.phone} (ID: {sms_record.id}), {error_msg}')
            return False
        except requests.exceptions.RequestException as e:
            error_msg = f'短信接口请求异常: {str(e)}'
            sms_record.status = 'failed'
            sms_record.error_message = error_msg
            sms_record.save()
            logger.error(f'短信重发失败: {sms_record.phone} (ID: {sms_record.id}), {error_msg}')
            return False
        except Exception as e:
            error_msg = f'重发短信时发生未知错误: {str(e)}'
            sms_record.status = 'failed'
            sms_record.error_message = error_msg
            sms_record.save()
            logger.error(f'短信重发失败: {sms_record.phone} (ID: {sms_record.id}), {error_msg}')
            return False

