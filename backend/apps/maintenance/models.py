from django.db import models
from django.conf import settings
from apps.tasks.storage import DateBasedFileStorage


class MaintenanceRecord(models.Model):
    """运维记录模型"""
    ISSUE_TYPE_CHOICES = [
        ('user_consultation', '用户咨询'),
        ('new_feature', '新增功能'),
        ('program_issue', '程序问题'),
        ('implementation', '实施定制'),
        ('data_issue', '数据问题'),
        ('statistics', '统计类'),
        ('simple_training', '简单培训'),
        ('troubleshooting', '故障排查'),
        ('technical_support', '技术支持'),
        ('account_issue', '账号问题'),
        ('other', '其他'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    COMPLETION_STATUS_CHOICES = [
        ('completed', '已完成'),
        ('in_progress', '处理中'),
        ('pending', '待处理'),
        ('cancelled', '已取消'),
    ]
    
    # 基本信息
    sequence_number = models.IntegerField(verbose_name='序号', null=True, blank=True)
    region = models.CharField(max_length=200, verbose_name='区划')
    department = models.CharField(max_length=200, blank=True, null=True, verbose_name='部门')
    requester = models.CharField(max_length=100, blank=True, null=True, verbose_name='需求提出人')
    request_date = models.DateField(verbose_name='需求提出日期')
    
    # 问题信息
    issue_type = models.CharField(max_length=50, choices=ISSUE_TYPE_CHOICES, verbose_name='问题类型')
    functional_module = models.CharField(max_length=200, blank=True, null=True, verbose_name='功能模块')
    issue_description = models.TextField(verbose_name='问题描述')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='优先级')
    
    # 处理信息
    handler = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_records',
        verbose_name='处理人'
    )
    assistant = models.JSONField(default=list, blank=True, null=True, verbose_name='协助人', help_text='存储协助人用户名列表')
    # processing_time 和 expected_completion_time 已废弃，保留DB字段兼容历史数据，不再通过接口使用
    processing_time = models.CharField(max_length=100, blank=True, null=True, verbose_name='处理耗时（总）')
    expected_completion_time = models.DateField(null=True, blank=True, verbose_name='预计完成时间')

    # 完成信息
    completion_time = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    completion_status = models.CharField(
        max_length=20, 
        choices=COMPLETION_STATUS_CHOICES, 
        default='pending',
        verbose_name='完成情况'
    )
    quantity = models.IntegerField(default=1, verbose_name='数量')
    
    # 创建信息
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_maintenance_records',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'maintenance_records'
        verbose_name = '运维记录'
        verbose_name_plural = '运维记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.region} - {self.issue_type} - {self.get_completion_status_display()}"


class MaintenanceUpdateLog(models.Model):
    """运维记录更新内容明细"""
    record = models.ForeignKey(
        MaintenanceRecord,
        on_delete=models.CASCADE,
        related_name='update_logs',
        verbose_name='运维记录'
    )
    content = models.TextField(verbose_name='更新内容')
    update_time = models.DateTimeField(verbose_name='更新时间')

    class Meta:
        db_table = 'maintenance_update_logs'
        verbose_name = '更新内容记录'
        verbose_name_plural = '更新内容记录'
        ordering = ['update_time']

    def __str__(self):
        return f"{self.record} - {self.update_time}"


class MaintenanceAttachment(models.Model):
    """运维记录附件模型"""
    record = models.ForeignKey(
        MaintenanceRecord,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='运维记录'
    )
    file = models.FileField(
        upload_to='',
        storage=DateBasedFileStorage(),
        verbose_name='文件'
    )
    original_filename = models.CharField(max_length=255, verbose_name='原始文件名')
    file_size = models.BigIntegerField(verbose_name='文件大小（字节）')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='上传人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')

    class Meta:
        db_table = 'maintenance_attachments'
        verbose_name = '运维记录附件'
        verbose_name_plural = '运维记录附件'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_filename} ({self.record})"

    @property
    def file_size_display(self):
        """显示格式化的文件大小"""
        size = self.file_size
        if size is None:
            return '-'
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
