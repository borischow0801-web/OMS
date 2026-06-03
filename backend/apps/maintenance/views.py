from rest_framework import viewsets, status, serializers as rest_serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q, Count, Case, When, IntegerField, Max, Value, CharField, F
from django.db.models.functions import TruncDate, TruncMonth
from django.http import FileResponse
import os
from .models import MaintenanceRecord, MaintenanceAttachment, MaintenanceUpdateLog
from .serializers import (
    MaintenanceRecordSerializer,
    MaintenanceRecordCreateSerializer,
    MaintenanceRecordUpdateSerializer,
    MaintenanceAttachmentSerializer,
)
import logging

logger = logging.getLogger(__name__)


class MaintenanceRecordPagination(PageNumberPagination):
    """运维记录分页类"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    """运维记录视图集"""
    queryset = MaintenanceRecord.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = MaintenanceRecordPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MaintenanceRecordCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MaintenanceRecordUpdateSerializer
        return MaintenanceRecordSerializer
    
    def get_queryset(self):
        """根据用户角色过滤运维记录"""
        user = self.request.user
        
        # 只有承建方（项目经理和员工）可以查看运维记录
        if not (user.is_manager or user.is_employee):
            return MaintenanceRecord.objects.none()
        
        queryset = MaintenanceRecord.objects.all()
        
        # 搜索过滤
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(region__icontains=search) |
                Q(department__icontains=search) |
                Q(requester__icontains=search) |
                Q(issue_description__icontains=search) |
                Q(functional_module__icontains=search)
            )
        
        # 区划过滤
        region = self.request.query_params.get('region')
        if region:
            queryset = queryset.filter(region__icontains=region)
        
        # 问题类型过滤
        issue_type = self.request.query_params.get('issue_type')
        if issue_type:
            queryset = queryset.filter(issue_type=issue_type)
        
        # 完成情况过滤
        completion_status = self.request.query_params.get('completion_status')
        if completion_status:
            queryset = queryset.filter(completion_status=completion_status)
        
        # 优先级过滤
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # 处理人过滤
        handler = self.request.query_params.get('handler')
        if handler:
            try:
                handler_id = int(handler)
                queryset = queryset.filter(handler_id=handler_id)
            except (ValueError, TypeError):
                # 如果不是数字，尝试按用户名或姓名搜索
                queryset = queryset.filter(
                    Q(handler__username__icontains=handler) |
                    Q(handler__first_name__icontains=handler) |
                    Q(handler__last_name__icontains=handler)
                )
        
        # 日期范围过滤
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(request_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(request_date__lte=end_date)
        
        return queryset.order_by('-created_at').prefetch_related('attachments__uploaded_by', 'update_logs')
    
    def create(self, request, *args, **kwargs):
        """创建运维记录（只有承建方可以创建）"""
        # 检查用户角色
        if not (request.user.is_manager or request.user.is_employee):
            return Response(
                {'error': '只有承建方可以创建运维记录'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 弹出 update_logs，不传给 Model.create()
        update_logs_data = serializer.validated_data.pop('update_logs', [])
        # 处理人默认为当前登录用户，序号自动生成（使用当前最大序号+1）
        max_sequence = MaintenanceRecord.objects.aggregate(
            max_seq=Max('sequence_number')
        )['max_seq'] or 0
        instance = serializer.save(
            creator=request.user,
            handler=request.user,
            sequence_number=max_sequence + 1,
        )
        # 创建更新内容明细
        for log_data in update_logs_data:
            MaintenanceUpdateLog.objects.create(record=instance, **log_data)

        return Response(
            MaintenanceRecordSerializer(instance).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """更新运维记录（只有承建方可以更新，且只能更新自己录入的记录）"""
        # 检查用户角色
        if not (request.user.is_manager or request.user.is_employee):
            return Response(
                {'error': '只有承建方可以更新运维记录'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            instance = self.get_object()
            # 只能更新自己录入的记录
            if instance.creator != request.user:
                return Response(
                    {'error': '只能修改自己录入的运维记录'},
                    status=status.HTTP_403_FORBIDDEN
                )
            # 记录请求数据，便于调试
            logger.debug(f'更新运维记录，ID: {instance.id}, 请求数据: {request.data}')
            
            serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
            serializer.is_valid(raise_exception=True)

            # 记录验证后的数据，便于调试
            logger.debug(f'验证后的数据: {serializer.validated_data}')

            # 弹出 update_logs（可选字段，未提供时为 None，表示不修改现有明细）
            update_logs_data = serializer.validated_data.pop('update_logs', None)

            updated_instance = serializer.save()

            # 如果请求中包含 update_logs，整体替换现有明细
            if update_logs_data is not None:
                MaintenanceUpdateLog.objects.filter(record=updated_instance).delete()
                for log_data in update_logs_data:
                    MaintenanceUpdateLog.objects.create(record=updated_instance, **log_data)
            
            # 记录保存后的数据，便于调试
            logger.debug(f'保存后的assistant字段: {updated_instance.assistant}')
            
            return Response(
                MaintenanceRecordSerializer(updated_instance).data,
                status=status.HTTP_200_OK
            )
        except rest_serializers.ValidationError as e:
            # 序列化器验证错误，返回400
            logger.warning(f'更新运维记录验证失败: {str(e)}, 数据: {request.data}')
            return Response(
                {'error': '数据验证失败', 'details': e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # 其他异常（如数据库错误等），返回500并记录日志
            logger.error(f'更新运维记录失败: {str(e)}', exc_info=True)
            return Response(
                {'error': f'更新失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """删除运维记录（只有承建方且本人录入才可删除）"""
        # 检查用户角色
        if not (request.user.is_manager or request.user.is_employee):
            return Response(
                {'error': '只有承建方可以删除运维记录'},
                status=status.HTTP_403_FORBIDDEN
            )
        # 只能删除自己录入的记录
        instance = self.get_object()
        if instance.creator != request.user:
            return Response(
                {'error': '只能删除自己录入的运维记录'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_attachment(self, request, pk=None):
        """上传附件（只有本人录入的记录才可上传）"""
        if not (request.user.is_manager or request.user.is_employee):
            return Response({'error': '只有承建方可以上传附件'}, status=status.HTTP_403_FORBIDDEN)

        record = self.get_object()
        if record.creator != request.user:
            return Response({'error': '只能为自己录入的运维记录上传附件'}, status=status.HTTP_403_FORBIDDEN)

        if 'file' not in request.FILES:
            return Response({'error': '请选择要上传的文件'}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']
        if not uploaded_file.name:
            return Response({'error': '文件名不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            attachment = MaintenanceAttachment.objects.create(
                record=record,
                file=uploaded_file,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                uploaded_by=request.user,
            )
            serializer = MaintenanceAttachmentSerializer(attachment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f'上传运维记录附件失败，记录ID: {record.id}, 错误: {e}', exc_info=True)
            return Response({'error': f'上传失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['delete'], url_path='attachments/(?P<attachment_id>[^/.]+)')
    def delete_attachment(self, request, pk=None, attachment_id=None):
        """删除附件（只有本人录入的记录才可删除附件）"""
        if not (request.user.is_manager or request.user.is_employee):
            return Response({'error': '只有承建方可以删除附件'}, status=status.HTTP_403_FORBIDDEN)

        record = self.get_object()
        if record.creator != request.user:
            return Response({'error': '只能删除自己录入的运维记录的附件'}, status=status.HTTP_403_FORBIDDEN)

        try:
            attachment = MaintenanceAttachment.objects.get(id=attachment_id, record=record)
        except MaintenanceAttachment.DoesNotExist:
            return Response({'error': '附件不存在'}, status=status.HTTP_404_NOT_FOUND)

        if attachment.file:
            file_path = attachment.file.path
            if os.path.exists(file_path):
                os.remove(file_path)

        attachment.delete()
        return Response({'message': '附件已删除'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='attachments/(?P<attachment_id>[^/.]+)/download')
    def download_attachment(self, request, pk=None, attachment_id=None):
        """下载附件（承建方均可下载）"""
        if not (request.user.is_manager or request.user.is_employee):
            return Response({'error': '只有承建方可以下载附件'}, status=status.HTTP_403_FORBIDDEN)

        record = self.get_object()

        try:
            attachment = MaintenanceAttachment.objects.get(id=attachment_id, record=record)
        except MaintenanceAttachment.DoesNotExist:
            return Response({'error': '附件不存在'}, status=status.HTTP_404_NOT_FOUND)

        if not attachment.file:
            return Response({'error': '文件不存在'}, status=status.HTTP_404_NOT_FOUND)

        file_path = attachment.file.path
        if not os.path.exists(file_path):
            return Response({'error': '文件已丢失'}, status=status.HTTP_404_NOT_FOUND)

        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=attachment.original_filename,
        )

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取运维记录统计报告"""
        # 检查用户角色
        if not (request.user.is_manager or request.user.is_employee):
            return Response(
                {'error': '只有承建方可以查看统计报告'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset()
        
        # 总事件数
        total_count = queryset.count()
        
        # 完成数
        completed_count = queryset.filter(completion_status='completed').count()
        
        # 未完成数
        incomplete_count = total_count - completed_count
        
        # 按事件类型统计
        issue_type_stats = queryset.values('issue_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        issue_type_list = []
        for stat in issue_type_stats:
            issue_type_list.append({
                'issue_type': stat['issue_type'],
                'issue_type_display': dict(MaintenanceRecord.ISSUE_TYPE_CHOICES).get(stat['issue_type'], stat['issue_type']),
                'count': stat['count']
            })
        
        # 按完成情况统计
        completion_status_stats = queryset.values('completion_status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        completion_status_list = []
        for stat in completion_status_stats:
            completion_status_list.append({
                'completion_status': stat['completion_status'],
                'completion_status_display': dict(MaintenanceRecord.COMPLETION_STATUS_CHOICES).get(
                    stat['completion_status'], stat['completion_status']
                ),
                'count': stat['count']
            })

        # 按处理人员统计（处理人为空归为“未指定”）
        handler_stats = queryset.values(
            'handler_id', 'handler__username', 'handler__first_name', 'handler__last_name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')

        handler_list = []
        for stat in handler_stats:
            if stat['handler_id'] is None:
                handler_display = '未指定'
            else:
                last_name = (stat.get('handler__last_name') or '').strip()
                first_name = (stat.get('handler__first_name') or '').strip()
                handler_display = f"{last_name}{first_name}".strip() or stat.get('handler__username') or '未指定'

            handler_list.append({
                'handler_id': stat['handler_id'],
                'handler_username': stat.get('handler__username'),
                'handler_display': handler_display,
                'count': stat['count'],
            })

        # 按区划统计（区划为空归为“其他”，理论上region必填，这里兜底）
        region_grouped_stats = queryset.annotate(
            region_group=Case(
                When(region__isnull=True, then=Value('其他')),
                When(region='', then=Value('其他')),
                default=F('region'),
                output_field=CharField()
            )
        ).values('region_group').annotate(count=Count('id')).order_by('-count')

        region_list = [
            {'region': stat['region_group'], 'count': stat['count']}
            for stat in region_grouped_stats
        ]

        # 按需求提出日期统计（按月份）
        month_stats = queryset.annotate(
            month=TruncMonth('request_date')
        ).values('month').annotate(count=Count('id')).order_by('month')

        request_month_list = []
        for stat in month_stats:
            month_val = stat.get('month')
            month_str = month_val.strftime('%Y-%m') if month_val else '未知'
            request_month_list.append({'month': month_str, 'count': stat['count']})

        # 按功能模块统计（为空归为“其他”）
        module_stats = queryset.annotate(
            module_group=Case(
                When(functional_module__isnull=True, then=Value('其他')),
                When(functional_module='', then=Value('其他')),
                default=F('functional_module'),
                output_field=CharField()
            )
        ).values('module_group').annotate(count=Count('id')).order_by('-count')

        functional_module_list = [
            {'functional_module': stat['module_group'], 'count': stat['count']}
            for stat in module_stats
        ]
        
        return Response({
            'total_count': total_count,
            'completed_count': completed_count,
            'incomplete_count': incomplete_count,
            'issue_type_statistics': issue_type_list,
            'completion_status_statistics': completion_status_list,
            'handler_statistics': handler_list,
            'region_statistics': region_list,
            'request_month_statistics': request_month_list,
            'functional_module_statistics': functional_module_list,
        })
