from django.db import models
from django.conf import settings
from .storage import DateBasedFileStorage


class Task(models.Model):
    """任务模型"""
    TASK_TYPE_CHOICES = [
        ('problem', '问题'),
        ('requirement', '需求'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending_review', '待审核'),
        ('reviewed', '已审核'),
        ('assigned', '已指派'),
        ('in_progress', '处理中'),
        ('completed', '已完成'),
        ('confirmed', '已确认'),
        ('closed', '已结单'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='标题')
    description = models.TextField(verbose_name='描述')
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, null=True, blank=True, verbose_name='任务类型')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_review', verbose_name='状态')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='优先级')
    
    # 关联用户
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                related_name='created_tasks', verbose_name='创建人')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                 null=True, blank=True, related_name='reviewed_tasks', verbose_name='审核人')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                null=True, blank=True, related_name='assigned_tasks', verbose_name='指派人')
    handler = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                null=True, blank=True, related_name='handled_tasks', verbose_name='处理人')
    assistant_employees = models.ManyToManyField(settings.AUTH_USER_MODEL, 
                                                   related_name='assisted_tasks', 
                                                   blank=True, 
                                                   verbose_name='协助员工')
    
    # 流程评论
    review_comment = models.TextField(blank=True, null=True, verbose_name='审核意见')
    assign_comment = models.TextField(blank=True, null=True, verbose_name='指派说明')
    handle_comment = models.TextField(blank=True, null=True, verbose_name='处理说明')
    confirm_comment = models.TextField(blank=True, null=True, verbose_name='确认意见')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='结单时间')
    
    class Meta:
        db_table = 'tasks'
        verbose_name = '任务'
        verbose_name_plural = '任务'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class Comment(models.Model):
    """任务评论模型"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', verbose_name='任务')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='评论人')
    content = models.TextField(verbose_name='评论内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'comments'
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} 评论: {self.content[:50]}"


class TaskAttachment(models.Model):
    """任务附件模型"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments', verbose_name='任务')
    file = models.FileField(
        upload_to='',  # 由自定义存储类处理路径
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
        db_table = 'task_attachments'
        verbose_name = '任务附件'
        verbose_name_plural = '任务附件'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.original_filename} ({self.task.title})"
    
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


