from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import WorkflowLog, Notification, SmsConfig, SmsTemplate, SmsRecord


@admin.register(WorkflowLog)
class WorkflowLogAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'action', 'from_status', 'to_status', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('task__title', 'comment')
    readonly_fields = ('created_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at',)


@admin.register(SmsConfig)
class SmsConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_url', 'is_enabled', 'updated_at')
    list_filter = ('is_enabled', 'created_at', 'updated_at')
    search_fields = ('name', 'api_url')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'is_enabled')
        }),
        ('接口配置', {
            'fields': ('api_url', 'api_params'),
            'description': 'api_params 应为 JSON 格式，支持 {phone} 和 {content} 占位符。例如：{"mobile": "{phone}", "message": "{content}"}'
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SmsTemplate)
class SmsTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_type', 'is_enabled', 'content_preview', 'updated_at')
    list_filter = ('template_type', 'is_enabled', 'created_at', 'updated_at')
    search_fields = ('content',)
    readonly_fields = ('created_at', 'updated_at')
    
    def content_preview(self, obj):
        """内容预览"""
        if obj.content:
            preview = obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
            return format_html('<span title="{}">{}</span>', obj.content, preview)
        return '-'
    content_preview.short_description = '内容预览'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('template_type', 'is_enabled')
        }),
        ('模板内容', {
            'fields': ('content',),
            'description': '支持占位符：{任务标题}、{任务名称}、{审核不通过的理由}、{原因为} 等'
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SmsRecord)
class SmsRecordAdmin(admin.ModelAdmin):
    list_display = ('phone', 'content_preview', 'template_type', 'status_badge', 'task', 'recipient', 'sent_at', 'resend_button', 'created_at')
    list_filter = ('status', 'template_type', 'created_at', 'sent_at')
    search_fields = ('phone', 'content', 'task__title', 'recipient__username')
    readonly_fields = ('created_at', 'sent_at', 'response_data', 'error_message')
    # 移除 date_hierarchy 以避免时区相关问题，改用 list_filter 中的日期过滤
    # date_hierarchy = 'created_at'
    actions = ['resend_sms']
    
    def content_preview(self, obj):
        """内容预览"""
        if obj.content:
            preview = obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
            return format_html('<span title="{}">{}</span>', obj.content, preview)
        return '-'
    content_preview.short_description = '短信内容'
    
    def status_badge(self, obj):
        """状态徽章"""
        colors = {
            'pending': 'orange',
            'success': 'green',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = '发送状态'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('phone', 'content', 'template_type', 'status')
        }),
        ('关联信息', {
            'fields': ('task', 'recipient')
        }),
        ('发送结果', {
            'fields': ('sent_at', 'error_message', 'response_data'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at',)
        }),
    )
    
    def resend_button(self, obj):
        """重发按钮"""
        if obj.status in ('failed', 'pending'):
            url = reverse('admin:workflow_smsrecord_resend', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">重发</a>',
                url
            )
        return '-'
    resend_button.short_description = '操作'
    
    def get_urls(self):
        """添加自定义URL"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/resend/',
                self.admin_site.admin_view(self.resend_sms_view),
                name='workflow_smsrecord_resend',
            ),
        ]
        return custom_urls + urls
    
    def resend_sms_view(self, request, object_id, *args, **kwargs):
        """重发短信视图"""
        try:
            sms_record = SmsRecord.objects.get(pk=object_id)
            success = self._resend_sms(sms_record)
            if success:
                self.message_user(request, '短信重发成功', messages.SUCCESS)
            else:
                self.message_user(request, '短信重发失败，请查看错误信息', messages.ERROR)
        except SmsRecord.DoesNotExist:
            self.message_user(request, '短信记录不存在', messages.ERROR)
        
        return HttpResponseRedirect(reverse('admin:workflow_smsrecord_changelist'))
    
    def resend_sms(self, request, queryset):
        """批量重发短信"""
        success_count = 0
        fail_count = 0
        for sms_record in queryset:
            if self._resend_sms(sms_record):
                success_count += 1
            else:
                fail_count += 1
        
        if success_count > 0:
            self.message_user(request, f'成功重发 {success_count} 条短信', messages.SUCCESS)
        if fail_count > 0:
            self.message_user(request, f'重发失败 {fail_count} 条短信', messages.WARNING)
    
    resend_sms.short_description = '重发选中的短信'
    
    def _resend_sms(self, sms_record):
        """重发短信的内部方法"""
        try:
            from .sms_service import SmsService
            # 使用专门的重发方法
            return SmsService.resend_sms(sms_record)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'重发短信失败 (ID: {sms_record.id}): {e}', exc_info=True)
            sms_record.status = 'failed'
            sms_record.error_message = str(e)
            sms_record.save()
            return False

