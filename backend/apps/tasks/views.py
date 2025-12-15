from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.http import FileResponse
from django.conf import settings
from datetime import datetime, timedelta
import os
import threading
from .models import Task, Comment, TaskAttachment
from .serializers import (
    TaskSerializer, TaskCreateSerializer, TaskUpdateSerializer, TaskReviewSerializer,
    TaskAssignSerializer, TaskHandleSerializer, TaskCompleteSerializer,
    TaskConfirmSerializer, TaskAssistantSerializer, CommentSerializer,
    TaskAttachmentSerializer
)
from apps.workflow.models import WorkflowLog, Notification
import logging
logger = logging.getLogger(__name__)


def _send_sms_async(template_type, task, recipient=None, extra_context=None):
    """异步发送短信（不影响业务流转）"""
    try:
        from apps.workflow.sms_service import SmsService
        if template_type == 'task_submitted':
            SmsService.send_task_submitted_sms(task)
        elif template_type == 'task_reviewed':
            SmsService.send_task_reviewed_sms(task)
        elif template_type == 'task_reviewed_rejected':
            SmsService.send_task_sms('task_reviewed_rejected', task, recipient=recipient, extra_context=extra_context)
        elif template_type == 'task_assigned':
            SmsService.send_task_sms('task_assigned', task, recipient=recipient)
        elif template_type == 'task_completed':
            SmsService.send_task_sms('task_completed', task, recipient=recipient)
        elif template_type == 'task_needs_modification':
            SmsService.send_task_sms('task_needs_modification', task, recipient=recipient, extra_context=extra_context)
    except Exception as e:
        # 记录错误但不影响业务流程
        logger.error(f'发送短信失败（模板类型: {template_type}, 任务ID: {task.id}）: {e}', exc_info=True)


class TaskPagination(PageNumberPagination):
    """任务分页类"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class TaskViewSet(viewsets.ModelViewSet):
    """任务视图集"""
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = TaskPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        return TaskSerializer
    
    def update(self, request, *args, **kwargs):
        """更新任务（只有草稿状态的任务可以更新）"""
        task = self.get_object()
        user = request.user
        
        # 检查权限：只有创建者或管理员可以更新草稿
        if task.status != 'draft':
            return Response(
                {'error': '只能编辑草稿状态的任务'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if task.creator != user and not user.is_admin:
            return Response(
                {'error': '只能编辑自己创建的草稿任务'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """创建任务（只有使用方和管理员可以创建）"""
        # 检查用户角色
        if not (request.user.is_user or request.user.is_admin):
            return Response(
                {'error': '只有使用方和管理员可以创建任务'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 调用perform_create来创建工作流日志和通知
        self.perform_create(serializer)
        task = serializer.instance
        
        # 创建任务后，使用TaskSerializer返回完整数据（包含id）
        task_serializer = TaskSerializer(task, context={'request': request})
        headers = self.get_success_headers(task_serializer.data)
        
        # 在事务外发送短信，不影响业务流程
        if task.status != 'draft':
            _send_sms_async('task_submitted', task)
        
        return Response(task_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def get_queryset(self):
        """根据用户角色过滤任务"""
        user = self.request.user
        queryset = Task.objects.all()
        
        if user.is_user:
            # 使用方：可以看到自己创建的任务（包括草稿）
            queryset = queryset.filter(creator=user)
        elif user.is_admin:
            # 管理方：可以看到所有任务（包括草稿）
            pass
        elif user.is_manager:
            # 项目经理：可以看到已审核的任务（不包括草稿）
            queryset = queryset.filter(status__in=['reviewed', 'assigned', 'in_progress', 'completed', 'confirmed', 'closed'])
        elif user.is_employee:
            # 员工：可以看到指派给自己的任务或作为协助员工的任务（不包括草稿）
            queryset = queryset.filter(
                Q(handler=user) | Q(assistant_employees=user)
            ).distinct()
        
        # 状态过滤
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 类型过滤
        task_type = self.request.query_params.get('task_type')
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        
        # 标题关键字过滤
        title = self.request.query_params.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)
        
        # 优先级过滤
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # 创建日期过滤（按日期，不是时间）
        created_date = self.request.query_params.get('created_date')
        if created_date:
            try:
                # 解析日期字符串（格式：YYYY-MM-DD）
                date_obj = datetime.strptime(created_date, '%Y-%m-%d').date()
                # 使用日期范围查询，考虑时区
                # 获取当天的开始时间（本地时区 Asia/Shanghai）
                start_datetime = timezone.make_aware(
                    datetime.combine(date_obj, datetime.min.time()),
                    timezone.get_current_timezone()
                )
                # 获取下一天的开始时间（用于范围查询，使用__lt）
                next_date = date_obj + timedelta(days=1)
                end_datetime = timezone.make_aware(
                    datetime.combine(next_date, datetime.min.time()),
                    timezone.get_current_timezone()
                )
                # 使用日期范围查询：>= 当天00:00:00 且 < 下一天00:00:00
                queryset = queryset.filter(created_at__gte=start_datetime, created_at__lt=end_datetime)
            except (ValueError, TypeError) as e:
                # 如果日期格式错误，忽略该过滤条件
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'日期过滤格式错误: {created_date}, 错误: {e}')
                pass
        
        return queryset.select_related('creator', 'reviewer', 'assignee', 'handler').prefetch_related(
            'assistant_employees', 'comments__user', 'attachments__uploaded_by'
        )
    
    def perform_create(self, serializer):
        """创建任务"""
        task = serializer.save()
        # 只有非草稿任务才创建工作流日志和通知
        if task.status != 'draft':
            self._create_workflow_log(task, '创建任务', None, 'pending_review')
            self._create_notification(task, 'task_created', '新任务创建', f'您创建了任务：{task.title}')
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """审核任务（管理方）"""
        if not request.user.is_admin:
            return Response(
                {'error': '只有管理方可以审核任务'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        task = self.get_object()
        if task.status != 'pending_review':
            return Response(
                {'error': '该任务不是待审核状态'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TaskReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review_comment = serializer.validated_data.get('review_comment', '')
        
        with transaction.atomic():
            task.reviewer = request.user
            task.review_comment = review_comment
            
            if serializer.validated_data['approved']:
                task.status = 'reviewed'
                self._create_workflow_log(task, '审核通过', 'pending_review', 'reviewed', review_comment)
                self._create_notification(task, 'task_reviewed', '任务审核通过', 
                                         f'任务"{task.title}"已通过审核', notify_user=task.creator)
            else:
                task.status = 'closed'
                task.closed_at = timezone.now()
                # 审核不通过时必须填写理由
                if not review_comment:
                    return Response(
                        {'error': '审核不通过时，必须填写不通过理由'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                self._create_workflow_log(task, '审核不通过', 'pending_review', 'closed', review_comment)
                notification_content = f'任务"{task.title}"审核不通过。\n不通过理由：{review_comment}'
                self._create_notification(task, 'task_closed', '任务已结单', 
                                         notification_content, notify_user=task.creator)
            
            task.save()
        
        # 先序列化数据并返回响应，避免短信发送阻塞
        response_data = TaskSerializer(task, context={'request': request}).data
        response = Response(response_data)
        
        # 在后台线程中异步发送短信，完全不影响响应返回
        def send_sms_background():
            try:
                if serializer.validated_data['approved']:
                    _send_sms_async('task_reviewed', task)
                else:
                    _send_sms_async('task_reviewed_rejected', task, recipient=task.creator, 
                                  extra_context={'审核不通过的理由': review_comment, '原因为': review_comment})
            except Exception as e:
                logger.error(f'后台发送短信失败（不影响业务）: {e}', exc_info=True)
        
        threading.Thread(target=send_sms_background, daemon=True).start()
        
        return response
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """指派任务（项目经理）"""
        if not request.user.is_manager:
            return Response(
                {'error': '只有项目经理可以指派任务'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        task = self.get_object()
        # 允许对 reviewed 或 assigned 状态的任务进行指派/重新指派
        if task.status not in ['reviewed', 'assigned']:
            return Response(
                {'error': '该任务状态不允许指派。只有"已审核"或"已指派"状态的任务可以指派'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TaskAssignSerializer(data=request.data, context={'task': task})
        serializer.is_valid(raise_exception=True)
        
        from apps.accounts.models import User
        new_handler = User.objects.get(id=serializer.validated_data['handler_id'])
        if not new_handler.is_employee:
            return Response(
                {'error': '只能指派给员工'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查是否是指派给同一个员工（仅当任务已有处理人时）
        if task.handler and task.handler.id == new_handler.id:
            return Response(
                {'error': '该任务已经指派给该员工'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            old_handler = task.handler  # 保存原处理人
            old_status = task.status  # 保存原状态
            
            task.assignee = request.user
            task.handler = new_handler
            task.assign_comment = serializer.validated_data.get('assign_comment', '')
            # 如果提供了任务类型，则设置任务类型（首次指派时）
            if 'task_type' in serializer.validated_data and serializer.validated_data['task_type']:
                task.task_type = serializer.validated_data['task_type']
            task.status = 'assigned'
            task.save()
            
            # 如果是重新指派（原状态为 assigned 且有原处理人）
            if old_status == 'assigned' and old_handler:
                # 记录重新指派操作
                reassign_comment = serializer.validated_data.get('assign_comment', '')
                self._create_workflow_log(task, '重新指派任务', 'assigned', 'assigned', 
                                         f'原处理人：{old_handler.full_name or old_handler.username}。新处理人：{new_handler.full_name or new_handler.username}。' + 
                                         (f'理由：{reassign_comment}' if reassign_comment else ''))
                # 通知原处理人任务已被重新指派（使用task_assigned类型，但内容说明是重新指派）
                self._create_notification(task, 'task_assigned', '任务已重新指派', 
                                         f'任务"{task.title}"已重新指派给其他员工，您无需再处理此任务', notify_user=old_handler)
            else:
                # 首次指派
                self._create_workflow_log(task, '指派任务', old_status, 'assigned')
            
            # 通知新处理人
            self._create_notification(task, 'task_assigned', '任务已指派', 
                                     f'任务"{task.title}"已指派给您', notify_user=new_handler)
        
        # 先返回响应，避免短信发送阻塞
        response_data = TaskSerializer(task, context={'request': request}).data
        
        # 在后台线程中异步发送短信，完全不影响响应返回
        if old_status != 'assigned':
            def send_sms_background():
                try:
                    _send_sms_async('task_assigned', task, recipient=new_handler)
                except Exception as e:
                    logger.error(f'后台发送短信失败（不影响业务）: {e}', exc_info=True)
            threading.Thread(target=send_sms_background, daemon=True).start()
        
        return Response(response_data)
    
    @action(detail=True, methods=['post'])
    def set_assistants(self, request, pk=None):
        """设置协助员工（处理员工）"""
        task = self.get_object()
        # 只有处理人（接单员工）可以设置协助员工
        if task.handler != request.user:
            return Response(
                {'error': '只有处理人（接单员工）可以设置协助员工'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 只能在 assigned 或 in_progress 状态设置协助员工
        if task.status not in ['assigned', 'in_progress']:
            return Response(
                {'error': '该任务状态不允许设置协助员工'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TaskAssistantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        assistant_employee_ids = serializer.validated_data.get('assistant_employee_ids', [])
        
        from apps.accounts.models import User
        # 验证所有ID都是员工
        if assistant_employee_ids:
            assistants = User.objects.filter(id__in=assistant_employee_ids, role='employee', is_active=True)
            if assistants.count() != len(assistant_employee_ids):
                return Response(
                    {'error': '协助员工必须是有效的员工账号'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 不能将自己设为协助员工
            if request.user.id in assistant_employee_ids:
                return Response(
                    {'error': '不能将自己设为协助员工'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        with transaction.atomic():
            # 更新协助员工
            task.assistant_employees.set(assistant_employee_ids if assistant_employee_ids else [])
            task.save()
            
            # 创建工作流日志
            if assistant_employee_ids:
                assistant_names = [assist.full_name or assist.username for assist in assistants]
                self._create_workflow_log(task, '设置协助员工', task.status, task.status, 
                                         f'协助员工：{", ".join(assistant_names)}')
                # 通知协助员工
                for assistant in assistants:
                    self._create_notification(task, 'task_assigned', '任务协助', 
                                             f'您被添加为任务"{task.title}"的协助员工，可以查看任务详情', notify_user=assistant)
            else:
                # 清空协助员工
                self._create_workflow_log(task, '清空协助员工', task.status, task.status)
        
        return Response(TaskSerializer(task, context={'request': request}).data)
    
    @action(detail=True, methods=['post'])
    def handle(self, request, pk=None):
        """处理任务（员工）"""
        task = self.get_object()
        # 只有处理人（接单员工）可以处理任务，协助员工不能操作
        if task.handler != request.user:
            return Response(
                {'error': '只有处理人（接单员工）可以处理任务，协助员工仅可查看'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if task.status not in ['assigned', 'in_progress']:
            return Response(
                {'error': '该任务状态不允许处理'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TaskHandleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            task.handle_comment = serializer.validated_data.get('handle_comment', '')
            task.status = 'in_progress'
            task.save()
            
            self._create_workflow_log(task, '开始处理', 'assigned', 'in_progress')
        
        return Response(TaskSerializer(task, context={'request': request}).data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """完成任务（员工）"""
        task = self.get_object()
        # 只有处理人（接单员工）可以完成任务，协助员工不能操作
        if task.handler != request.user:
            return Response(
                {'error': '只有处理人（接单员工）可以完成任务，协助员工仅可查看'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if task.status != 'in_progress':
            return Response(
                {'error': '该任务不是处理中状态'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TaskCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # 如果有处理说明，更新它
            if serializer.validated_data.get('handle_comment'):
                task.handle_comment = serializer.validated_data['handle_comment']
            task.status = 'completed'
            task.save()
            
            self._create_workflow_log(task, '完成任务', 'in_progress', 'completed', 
                                     serializer.validated_data.get('handle_comment', ''))
            self._create_notification(task, 'task_completed', '任务已完成', 
                                     f'任务"{task.title}"已完成，请确认', notify_user=task.creator)
        
        # 先返回响应，避免短信发送阻塞
        response_data = TaskSerializer(task, context={'request': request}).data
        
        # 在后台线程中异步发送短信，完全不影响响应返回
        def send_sms_background():
            try:
                _send_sms_async('task_completed', task, recipient=task.creator)
            except Exception as e:
                logger.error(f'后台发送短信失败（不影响业务）: {e}', exc_info=True)
        threading.Thread(target=send_sms_background, daemon=True).start()
        
        return Response(response_data)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """确认任务（使用方）"""
        task = self.get_object()
        if task.creator != request.user:
            return Response(
                {'error': '您无权确认此任务'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if task.status != 'completed':
            return Response(
                {'error': '该任务不是已完成状态'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TaskConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            confirm_comment = serializer.validated_data.get('confirm_comment', '')
            task.confirm_comment = confirm_comment
            
            if serializer.validated_data['confirmed']:
                task.status = 'confirmed'
                task.closed_at = timezone.now()
                self._create_workflow_log(task, '确认完成', 'completed', 'confirmed', confirm_comment)
                self._create_notification(task, 'task_confirmed', '任务已确认', 
                                         f'任务"{task.title}"已确认完成', notify_user=task.handler)
            else:
                # 需要修改时，必须填写修改意见
                if not confirm_comment:
                    return Response(
                        {'error': '需要修改时，必须填写修改意见'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                task.status = 'in_progress'
                # 将修改意见保存到工作流日志，并通知相关人员
                self._create_workflow_log(task, '需要修改', 'completed', 'in_progress', 
                                         f'修改意见：{confirm_comment}')
                # 通知处理员工
                self._create_notification(task, 'task_reopened', '任务需重新处理', 
                                         f'任务"{task.title}"需要修改。修改意见：{confirm_comment}', notify_user=task.handler)
                # 通知项目经理和管理方
                if task.assignee:
                    self._create_notification(task, 'task_reopened', '任务需修改', 
                                             f'任务"{task.title}"需要修改。修改意见：{confirm_comment}', notify_user=task.assignee)
                if task.reviewer:
                    self._create_notification(task, 'task_reopened', '任务需修改', 
                                             f'任务"{task.title}"需要修改。修改意见：{confirm_comment}', notify_user=task.reviewer)
            
            task.save()
        
        # 先序列化数据并返回响应，避免短信发送阻塞
        response_data = TaskSerializer(task, context={'request': request}).data
        response = Response(response_data)
        
        # 在后台线程中异步发送短信，完全不影响响应返回
        if not serializer.validated_data['confirmed']:
            # 需要修改时，发送短信给处理员工
            def send_sms_background():
                try:
                    if task.handler:
                        _send_sms_async('task_needs_modification', task, recipient=task.handler,
                                      extra_context={'修改意见': confirm_comment})
                except Exception as e:
                    logger.error(f'后台发送短信失败（不影响业务）: {e}', exc_info=True)
            threading.Thread(target=send_sms_background, daemon=True).start()
        
        return response
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """添加评论"""
        task = self.get_object()
        content = request.data.get('content', '')
        if not content:
            return Response(
                {'error': '评论内容不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment = Comment.objects.create(
            task=task,
            user=request.user,
            content=content
        )
        
        # 通知相关人员
        notify_users = set([task.creator, task.reviewer, task.assignee, task.handler])
        notify_users.discard(None)
        notify_users.discard(request.user)
        
        for user in notify_users:
            Notification.objects.create(
                user=user,
                task=task,
                notification_type='comment_added',
                title='新增评论',
                content=f'{request.user.username} 在任务"{task.title}"中添加了评论'
            )
        
        return Response(CommentSerializer(comment).data)
    
    def _create_workflow_log(self, task, action, from_status, to_status, comment=''):
        """创建工作流日志"""
        WorkflowLog.objects.create(
            task=task,
            user=self.request.user,
            action=action,
            from_status=from_status,
            to_status=to_status,
            comment=comment or ''
        )
    
    def _create_notification(self, task, notification_type, title, content, notify_user=None):
        """创建通知"""
        if notify_user:
            Notification.objects.create(
                user=notify_user,
                task=task,
                notification_type=notification_type,
                title=title,
                content=content
            )
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_attachment(self, request, pk=None):
        """上传附件（只有使用方和管理员在创建时可以上传，提交后只可查看和下载）"""
        task = self.get_object()
        user = request.user
        
        # 检查权限：使用方和管理员在任务创建时（pending_review）或草稿状态（draft）可以上传
        if task.status in ['pending_review', 'draft'] and (user.is_user or user.is_admin):
            if task.creator != user and not user.is_admin:
                return Response(
                    {'error': '只能为自己的任务上传附件'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif task.status not in ['pending_review', 'draft']:
            # 任务提交后，任何人都不能上传新附件
            return Response(
                {'error': '任务已提交，不能上传新附件'},
                status=status.HTTP_403_FORBIDDEN
            )
        else:
            return Response(
                {'error': '没有权限上传附件'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 检查文件是否存在
        if 'file' not in request.FILES:
            return Response(
                {'error': '请选择要上传的文件'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        # 检查文件名
        if not uploaded_file.name:
            return Response(
                {'error': '文件名不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        original_filename = uploaded_file.name
        file_size = uploaded_file.size
        
        try:
            # 创建附件记录
            attachment = TaskAttachment.objects.create(
                task=task,
                file=uploaded_file,
                original_filename=original_filename,
                file_size=file_size,
                uploaded_by=user
            )
            
            serializer = TaskAttachmentSerializer(attachment, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            import traceback
            print(f"上传附件失败: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'上传附件失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'], url_path='attachments/(?P<attachment_id>[^/.]+)')
    def delete_attachment(self, request, pk=None, attachment_id=None):
        """删除附件（只有使用方和管理员在创建时可以删除，提交后不可删除）"""
        task = self.get_object()
        user = request.user
        
        try:
            attachment = TaskAttachment.objects.get(id=attachment_id, task=task)
        except TaskAttachment.DoesNotExist:
            return Response(
                {'error': '附件不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查权限：只有使用方和管理员在任务创建时（pending_review）或草稿状态（draft）可以删除
        if task.status in ['pending_review', 'draft'] and (user.is_user or user.is_admin):
            if task.creator != user and not user.is_admin:
                return Response(
                    {'error': '只能删除自己任务的附件'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': '任务已提交，不能删除附件'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 删除文件
        if attachment.file:
            file_path = attachment.file.path
            if os.path.exists(file_path):
                os.remove(file_path)
        
        attachment.delete()
        return Response({'message': '附件已删除'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='attachments/(?P<attachment_id>[^/.]+)/download')
    def download_attachment(self, request, pk=None, attachment_id=None):
        """下载附件（所有角色都可以下载）"""
        task = self.get_object()
        
        try:
            attachment = TaskAttachment.objects.get(id=attachment_id, task=task)
        except TaskAttachment.DoesNotExist:
            return Response(
                {'error': '附件不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not attachment.file:
            return Response(
                {'error': '文件不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        file_path = attachment.file.path
        if not os.path.exists(file_path):
            return Response(
                {'error': '文件已丢失'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=attachment.original_filename
        )
    
    @action(detail=True, methods=['post'])
    def submit_draft(self, request, pk=None):
        """提交草稿任务（将草稿状态改为pending_review）"""
        task = self.get_object()
        user = request.user
        
        # 检查权限：只有创建者或管理员可以提交草稿
        if task.status != 'draft':
            return Response(
                {'error': '该任务不是草稿状态，无法提交'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if task.creator != user and not user.is_admin:
            return Response(
                {'error': '只能提交自己创建的草稿任务'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 更新任务状态
        task.status = 'pending_review'
        task.save()
        
        # 创建工作流日志和通知
        self._create_workflow_log(task, '提交草稿', 'draft', 'pending_review')
        self._create_notification(task, 'task_created', '新任务创建', f'您提交了任务：{task.title}')
        
        serializer = TaskSerializer(task, context={'request': request})
        
        # 在事务外发送短信，不影响业务流程
        _send_sms_async('task_submitted', task)
        
        return Response(serializer.data)

