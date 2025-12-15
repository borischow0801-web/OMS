from rest_framework import serializers
from .models import WorkflowLog, Notification
from apps.tasks.serializers import TaskSerializer
from apps.accounts.serializers import UserSerializer


class WorkflowLogSerializer(serializers.ModelSerializer):
    """工作流日志序列化器"""
    task = TaskSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = WorkflowLog
        fields = ('id', 'task', 'user', 'action', 'from_status', 'to_status', 
                  'comment', 'created_at')
        read_only_fields = ('id', 'created_at')


class NotificationSerializer(serializers.ModelSerializer):
    """通知序列化器"""
    task = TaskSerializer(read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = ('id', 'task', 'notification_type', 'notification_type_display',
                  'title', 'content', 'is_read', 'created_at')
        read_only_fields = ('id', 'created_at')

