from django.contrib import admin
from .models import Task, Comment, TaskAttachment


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task_type', 'status', 'priority', 'creator', 'created_at')
    list_filter = ('task_type', 'status', 'priority', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'closed_at')
    fieldsets = (
        ('基本信息', {'fields': ('title', 'description', 'task_type', 'status', 'priority')}),
        ('关联用户', {'fields': ('creator', 'reviewer', 'assignee', 'handler')}),
        ('流程评论', {'fields': ('review_comment', 'assign_comment', 'handle_comment', 'confirm_comment')}),
        ('时间信息', {'fields': ('created_at', 'updated_at', 'closed_at')}),
    )
    
    class TaskAttachmentInline(admin.TabularInline):
        model = TaskAttachment
        extra = 0
        readonly_fields = ('uploaded_by', 'created_at')
        fields = ('file', 'original_filename', 'file_size', 'uploaded_by', 'created_at')
    
    inlines = [TaskAttachmentInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content',)


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'task', 'uploaded_by', 'file_size', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('original_filename', 'task__title')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('基本信息', {'fields': ('task', 'file', 'original_filename')}),
        ('上传信息', {'fields': ('uploaded_by', 'file_size', 'created_at')}),
    )

