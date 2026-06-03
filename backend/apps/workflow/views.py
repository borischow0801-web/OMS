from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import WorkflowLog, Notification
from .serializers import WorkflowLogSerializer, NotificationSerializer


class WorkflowLogViewSet(viewsets.ReadOnlyModelViewSet):
    """工作流日志视图集"""
    serializer_class = WorkflowLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        task_id = self.request.query_params.get('task_id')
        if task_id:
            return WorkflowLog.objects.filter(task_id=task_id).select_related('task', 'user')
        return WorkflowLog.objects.none()


class NotificationViewSet(viewsets.ModelViewSet):
    """通知视图集"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).select_related('task')
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """标记通知已读"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'message': '已标记为已读'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """标记所有通知已读"""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': '已标记所有通知为已读'})

