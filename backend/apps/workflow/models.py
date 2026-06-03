from django.db import models
from django.conf import settings
from apps.tasks.models import Task
import json


class WorkflowLog(models.Model):
    """工作流日志模型"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='workflow_logs', verbose_name='任务')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='操作人')
    action = models.CharField(max_length=50, verbose_name='操作')
    from_status = models.CharField(max_length=20, blank=True, null=True, verbose_name='原状态')
    to_status = models.CharField(max_length=20, blank=True, null=True, verbose_name='新状态')
    comment = models.TextField(blank=True, null=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'workflow_logs'
        verbose_name = '工作流日志'
        verbose_name_plural = '工作流日志'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.task.title} - {self.action} ({self.created_at})"


class Notification(models.Model):
    """通知模型"""
    NOTIFICATION_TYPE_CHOICES = [
        ('task_created', '任务创建'),
        ('task_reviewed', '任务审核'),
        ('task_assigned', '任务指派'),
        ('task_completed', '任务完成'),
        ('task_confirmed', '任务确认'),
        ('task_closed', '任务结单'),
        ('comment_added', '新增评论'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                            related_name='notifications', verbose_name='接收人')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, 
                            related_name='notifications', verbose_name='关联任务')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, verbose_name='通知类型')
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    is_read = models.BooleanField(default=False, verbose_name='已读')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'notifications'
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class SmsConfig(models.Model):
    """短信配置模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name='配置名称', default='default')
    api_url = models.URLField(verbose_name='短信接口地址')
    api_params = models.TextField(
        help_text='JSON格式的接口参数模板，使用{phone}、{content}等占位符。例如：{"phoneNum": "{phone}", "mesConent": "{content}", "regionCode": "371000000000", "source": "oms"}。如果不配置，将使用默认值：phoneNum和mesConent为动态值，regionCode固定为371000000000，source固定为oms', 
        verbose_name='接口参数模板',
        blank=True,
        null=True
    )
    is_enabled = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'sms_configs'
        verbose_name = '短信配置'
        verbose_name_plural = '短信配置'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} ({'启用' if self.is_enabled else '禁用'})"
    
    def get_api_params(self):
        """获取解析后的接口参数"""
        try:
            return json.loads(self.api_params)
        except (json.JSONDecodeError, TypeError):
            return {}


class SmsTemplate(models.Model):
    """短信模板模型"""
    TEMPLATE_TYPE_CHOICES = [
        ('task_submitted', '任务提交'),
        ('task_reviewed', '任务审核通过'),
        ('task_reviewed_rejected', '任务审核不通过'),
        ('task_assigned', '任务分配'),
        ('task_completed', '任务完成'),
        ('task_needs_modification', '任务需要修改'),
    ]
    
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPE_CHOICES, unique=True, verbose_name='模板类型')
    content = models.TextField(help_text='短信内容模板，使用{任务标题}等占位符', verbose_name='模板内容')
    is_enabled = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'sms_templates'
        verbose_name = '短信模板'
        verbose_name_plural = '短信模板'
        ordering = ['template_type']
    
    def __str__(self):
        return f"{self.get_template_type_display()} ({'启用' if self.is_enabled else '禁用'})"


class SmsRecord(models.Model):
    """短信发送记录模型"""
    STATUS_CHOICES = [
        ('pending', '待发送'),
        ('success', '发送成功'),
        ('failed', '发送失败'),
    ]
    
    phone = models.CharField(max_length=20, verbose_name='手机号')
    content = models.TextField(verbose_name='短信内容')
    template_type = models.CharField(max_length=50, blank=True, null=True, verbose_name='模板类型')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='sms_records', verbose_name='关联任务')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sms_received', verbose_name='接收人')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='发送状态')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    response_data = models.TextField(blank=True, null=True, verbose_name='接口响应数据')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='发送时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'sms_records'
        verbose_name = '短信发送记录'
        verbose_name_plural = '短信发送记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.phone} - {self.status} ({self.created_at})"

