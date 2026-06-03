from django.contrib import admin
from .models import MaintenanceRecord, MaintenanceUpdateLog


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('sequence_number', 'region', 'department', 'requester', 'issue_type',
                    'completion_status', 'completion_time', 'creator', 'created_at')
    list_filter = ('issue_type', 'completion_status', 'priority', 'region', 'created_at')
    search_fields = ('region', 'department', 'requester', 'issue_description', 'functional_module')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('sequence_number', 'region', 'department', 'requester', 'request_date')
        }),
        ('问题信息', {
            'fields': ('issue_type', 'functional_module', 'issue_description', 'priority')
        }),
        ('处理信息', {
            'fields': ('handler', 'assistant')
        }),
        ('完成信息', {
            'fields': ('completion_status', 'completion_time', 'quantity')
        }),
        ('创建信息', {
            'fields': ('creator', 'created_at', 'updated_at')
        }),
    )


@admin.register(MaintenanceUpdateLog)
class MaintenanceUpdateLogAdmin(admin.ModelAdmin):
    list_display = ('record', 'update_time', 'content')
    list_filter = ('update_time',)
    search_fields = ('content',)
