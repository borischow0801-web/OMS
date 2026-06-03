"""
测试短信发送功能的管理命令

使用方法:
    python manage.py test_sms --phone 13800138000 --content "测试短信内容"
    python manage.py test_sms --phone 13800138000 --template task_submitted --task-id 1
"""
from django.core.management.base import BaseCommand
from apps.workflow.sms_service import SmsService
from apps.tasks.models import Task
from apps.accounts.models import User
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '测试短信发送功能'

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            required=True,
            help='接收短信的手机号'
        )
        parser.add_argument(
            '--content',
            type=str,
            help='短信内容（如果使用模板则不需要此参数）'
        )
        parser.add_argument(
            '--template',
            type=str,
            choices=['task_submitted', 'task_reviewed', 'task_reviewed_rejected', 
                    'task_assigned', 'task_completed', 'task_needs_modification'],
            help='短信模板类型（如果使用模板）'
        )
        parser.add_argument(
            '--task-id',
            type=int,
            help='任务ID（使用模板时需要）'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='接收人用户ID（使用模板时需要）'
        )

    def handle(self, *args, **options):
        phone = options['phone']
        content = options.get('content')
        template_type = options.get('template')
        task_id = options.get('task_id')
        user_id = options.get('user_id')
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('短信发送测试'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # 检查短信配置
        sms_config = SmsService.get_config()
        if not sms_config:
            self.stdout.write(self.style.ERROR('错误: 未配置短信接口或配置已禁用'))
            self.stdout.write('请在 Django Admin 中配置短信接口: /admin/workflow/smsconfig/')
            return
        
        self.stdout.write(f'短信配置: {sms_config.name}')
        self.stdout.write(f'接口URL: {sms_config.api_url}')
        self.stdout.write(f'接口参数模板: {sms_config.api_params}')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('注意: 接口使用 GET 请求，参数通过 URL 查询字符串传递'))
        self.stdout.write('')
        
        # 如果使用模板
        if template_type:
            if not task_id:
                self.stdout.write(self.style.ERROR('错误: 使用模板时必须提供 --task-id'))
                return
            
            try:
                task = Task.objects.get(id=task_id)
            except Task.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'错误: 任务ID {task_id} 不存在'))
                return
            
            recipient = None
            if user_id:
                try:
                    recipient = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'警告: 用户ID {user_id} 不存在，将使用默认接收人'))
            
            self.stdout.write(f'任务标题: {task.title}')
            self.stdout.write(f'模板类型: {template_type}')
            if recipient:
                self.stdout.write(f'接收人: {recipient.username} ({recipient.phone or "无手机号"})')
            self.stdout.write('')
            self.stdout.write('正在发送短信...')
            
            # 发送短信
            success = SmsService.send_task_sms(
                template_type=template_type,
                task=task,
                recipient=recipient
            )
            
            if success:
                self.stdout.write(self.style.SUCCESS('✓ 短信发送成功！'))
            else:
                self.stdout.write(self.style.ERROR('✗ 短信发送失败！'))
                self.stdout.write('请查看日志或 Django Admin 中的短信发送记录了解详细错误信息')
                self.stdout.write(f'短信记录: /admin/workflow/smsrecord/')
        
        # 如果直接发送
        elif content:
            self.stdout.write(f'手机号: {phone}')
            self.stdout.write(f'短信内容: {content}')
            self.stdout.write('')
            self.stdout.write('正在发送短信...')
            
            # 发送短信
            success = SmsService.send_sms(
                phone=phone,
                content=content
            )
            
            if success:
                self.stdout.write(self.style.SUCCESS('✓ 短信发送成功！'))
            else:
                self.stdout.write(self.style.ERROR('✗ 短信发送失败！'))
                self.stdout.write('请查看日志或 Django Admin 中的短信发送记录了解详细错误信息')
                self.stdout.write(f'短信记录: /admin/workflow/smsrecord/')
        
        else:
            self.stdout.write(self.style.ERROR('错误: 必须提供 --content 或 --template 参数'))
            return
        
        self.stdout.write('')
        self.stdout.write('提示: 详细的请求和响应日志已记录到日志文件中')
        self.stdout.write('可以通过以下方式查看日志:')
        self.stdout.write('  1. 查看 Django 日志文件')
        self.stdout.write('  2. 查看 Gunicorn 日志: journalctl -u oms-backend -f')
        self.stdout.write('  3. 在 Django Admin 中查看短信记录详情: /admin/workflow/smsrecord/')

