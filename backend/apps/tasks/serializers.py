from rest_framework import serializers
from .models import Task, Comment, TaskAttachment
from apps.accounts.serializers import UserSerializer


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化器"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ('id', 'user', 'content', 'created_at')
        read_only_fields = ('id', 'created_at')


class TaskAttachmentSerializer(serializers.ModelSerializer):
    """任务附件序列化器"""
    uploaded_by = UserSerializer(read_only=True)
    file_size_display = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskAttachment
        fields = ('id', 'task', 'file', 'original_filename', 'file_size', 
                  'file_size_display', 'uploaded_by', 'created_at', 'file_url')
        read_only_fields = ('id', 'uploaded_by', 'created_at', 'file_size_display', 'file_url')
    
    def get_file_size_display(self, obj):
        """获取格式化的文件大小"""
        return obj.file_size_display
    
    def get_file_url(self, obj):
        """获取文件下载URL"""
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None


class TaskSerializer(serializers.ModelSerializer):
    """任务序列化器"""
    creator = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    handler = UserSerializer(read_only=True)
    assistant_employees = UserSerializer(many=True, read_only=True)
    task_type_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    
    def get_task_type_display(self, obj):
        """获取任务类型显示文本，处理None值"""
        if obj.task_type:
            return obj.get_task_type_display()
        return None
    
    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'task_type', 'task_type_display',
                  'status', 'status_display', 'priority', 'priority_display',
                  'creator', 'reviewer', 'assignee', 'handler', 'assistant_employees',
                  'review_comment', 'assign_comment', 'handle_comment', 'confirm_comment',
                  'created_at', 'updated_at', 'closed_at', 'comments', 'attachments')
        read_only_fields = ('id', 'created_at', 'updated_at', 'closed_at')


class TaskCreateSerializer(serializers.ModelSerializer):
    """创建任务序列化器"""
    save_as_draft = serializers.BooleanField(write_only=True, required=False, default=False, help_text='是否保存为草稿')
    
    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'task_type', 'priority', 'save_as_draft')
        read_only_fields = ('id',)
        extra_kwargs = {
            'task_type': {'required': False, 'allow_null': True, 'allow_blank': True}
        }
    
    def create(self, validated_data):
        save_as_draft = validated_data.pop('save_as_draft', False)
        validated_data['creator'] = self.context['request'].user
        # 如果保存为草稿，状态设为draft，否则为pending_review
        if save_as_draft:
            validated_data['status'] = 'draft'
        else:
            validated_data['status'] = 'pending_review'
        return super().create(validated_data)


class TaskUpdateSerializer(serializers.ModelSerializer):
    """更新任务序列化器（用于编辑草稿）"""
    class Meta:
        model = Task
        fields = ('title', 'description', 'priority')
    
    def validate(self, attrs):
        """验证只有草稿状态的任务可以编辑"""
        if self.instance.status != 'draft':
            raise serializers.ValidationError('只能编辑草稿状态的任务')
        return attrs


class TaskReviewSerializer(serializers.Serializer):
    """审核任务序列化器"""
    approved = serializers.BooleanField(required=True)
    review_comment = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """验证审核不通过时必须填写理由"""
        if not attrs.get('approved') and not attrs.get('review_comment'):
            raise serializers.ValidationError({
                'review_comment': '审核不通过时，必须填写不通过理由'
            })
        return attrs


class TaskAssignSerializer(serializers.Serializer):
    """指派任务序列化器"""
    handler_id = serializers.IntegerField(required=True)
    task_type = serializers.ChoiceField(choices=[('problem', '问题'), ('requirement', '需求')], required=False, allow_null=True, allow_blank=True, help_text='任务类型（首次指派时必填）')
    assign_comment = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """验证首次指派时必须填写任务类型"""
        task = self.context.get('task')
        if task and not task.task_type and not attrs.get('task_type'):
            raise serializers.ValidationError({
                'task_type': '首次指派任务时，必须选择任务类型'
            })
        return attrs


class TaskHandleSerializer(serializers.Serializer):
    """处理任务序列化器"""
    handle_comment = serializers.CharField(required=False, allow_blank=True)


class TaskCompleteSerializer(serializers.Serializer):
    """完成任务序列化器"""
    handle_comment = serializers.CharField(required=False, allow_blank=True)


class TaskConfirmSerializer(serializers.Serializer):
    """确认任务序列化器"""
    confirmed = serializers.BooleanField(required=True)
    confirm_comment = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """验证需要修改时必须填写修改意见"""
        if not attrs.get('confirmed') and not attrs.get('confirm_comment'):
            raise serializers.ValidationError({
                'confirm_comment': '需要修改时，必须填写修改意见'
            })
        return attrs


class TaskAssistantSerializer(serializers.Serializer):
    """设置协助员工序列化器"""
    assistant_employee_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text='协助员工ID列表'
    )

