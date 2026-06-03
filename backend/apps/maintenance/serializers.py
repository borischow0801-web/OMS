from rest_framework import serializers
from .models import MaintenanceRecord, MaintenanceAttachment, MaintenanceUpdateLog
from apps.accounts.serializers import UserSerializer


class MaintenanceAttachmentSerializer(serializers.ModelSerializer):
    """运维记录附件序列化器"""
    uploaded_by = UserSerializer(read_only=True)
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceAttachment
        fields = ('id', 'record', 'file', 'original_filename', 'file_size',
                  'file_size_display', 'uploaded_by', 'created_at')
        read_only_fields = ('id', 'uploaded_by', 'created_at', 'file_size_display')

    def get_file_size_display(self, obj):
        return obj.file_size_display


class MaintenanceUpdateLogSerializer(serializers.ModelSerializer):
    """更新内容记录序列化器（读）"""
    class Meta:
        model = MaintenanceUpdateLog
        fields = ('id', 'content', 'update_time')


class UpdateLogInputSerializer(serializers.Serializer):
    """更新内容记录输入序列化器（写，用于 Create/Update）"""
    content = serializers.CharField(allow_blank=False)
    update_time = serializers.DateTimeField()


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    """运维记录序列化器（读）"""
    creator = UserSerializer(read_only=True)
    handler = UserSerializer(read_only=True)
    issue_type_display = serializers.CharField(source='get_issue_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    completion_status_display = serializers.CharField(source='get_completion_status_display', read_only=True)
    assistant_display = serializers.SerializerMethodField()
    assistant_user_ids = serializers.SerializerMethodField()
    attachments = MaintenanceAttachmentSerializer(many=True, read_only=True)
    update_logs = MaintenanceUpdateLogSerializer(many=True, read_only=True)

    class Meta:
        model = MaintenanceRecord
        fields = (
            'id', 'sequence_number', 'region', 'department', 'requester', 'request_date',
            'issue_type', 'issue_type_display', 'functional_module', 'issue_description',
            'priority', 'priority_display', 'handler', 'assistant', 'assistant_display',
            'assistant_user_ids', 'completion_status', 'completion_status_display',
            'completion_time', 'quantity', 'creator', 'created_at', 'updated_at',
            'attachments', 'update_logs',
        )
        read_only_fields = ('id', 'creator', 'created_at', 'updated_at')

    def get_assistant_display(self, obj):
        """获取协助人显示名称列表（优先显示姓名，其次用户名）"""
        if not obj.assistant:
            return []
        assistant_usernames = obj.assistant if isinstance(obj.assistant, list) else [obj.assistant] if obj.assistant else []
        if not assistant_usernames:
            return []

        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            users = User.objects.filter(username__in=assistant_usernames)
            user_map = {user.username: user for user in users}

            display_names = []
            for username in assistant_usernames:
                if username in user_map:
                    user = user_map[username]
                    display_names.append(user.full_name or user.username)
                else:
                    display_names.append(username)
            return display_names
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'获取协助人显示名称时发生错误: {str(e)}', exc_info=True)
            return assistant_usernames

    def get_assistant_user_ids(self, obj):
        """根据assistant(用户名列表)反查用户ID列表，供前端编辑页回填下拉框"""
        if not obj.assistant:
            return []
        assistant_usernames = obj.assistant if isinstance(obj.assistant, list) else [obj.assistant] if obj.assistant else []
        if not assistant_usernames:
            return []

        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            users = User.objects.filter(username__in=assistant_usernames).only('id', 'username')
            user_map = {user.username: user.id for user in users}

            user_ids = []
            for username in assistant_usernames:
                if username in user_map:
                    user_ids.append(user_map[username])
            return user_ids
        except Exception:
            return []


def _validate_assistant_ids(value):
    """共用的协助人 ID 列表校验逻辑：转换为用户名列表"""
    import logging
    logger = logging.getLogger(__name__)

    if not value or (isinstance(value, list) and len(value) == 0):
        return []

    if not isinstance(value, list):
        raise serializers.ValidationError('协助人必须是用户ID列表')

    from django.contrib.auth import get_user_model
    User = get_user_model()
    usernames = []

    for user_id in value:
        if user_id is None or user_id == '' or user_id == 0:
            continue

        try:
            user_id_int = int(user_id)
            if user_id_int <= 0:
                continue
        except (ValueError, TypeError):
            raise serializers.ValidationError(f'协助人用户ID格式错误: {user_id}')

        try:
            user = User.objects.get(id=user_id_int, role__in=['manager', 'employee'], is_active=True)
            usernames.append(user.username)
        except User.DoesNotExist:
            raise serializers.ValidationError(f'协助人用户不存在或不是承建方用户: {user_id}')
        except Exception as e:
            logger.error(f'验证协助人用户ID时发生错误: {str(e)}', exc_info=True)
            raise serializers.ValidationError(f'验证协助人用户时出错: {str(e)}')

    return usernames


def _validate_completion_time(attrs):
    """完成时间与完成情况联动校验（共用）"""
    completion_status = attrs.get('completion_status')
    completion_time = attrs.get('completion_time')

    if completion_status == 'completed' and not completion_time:
        raise serializers.ValidationError({'completion_time': '完成情况为已完成时，完成时间为必填项'})

    if completion_status and completion_status != 'completed':
        attrs['completion_time'] = None

    return attrs


class MaintenanceRecordCreateSerializer(serializers.ModelSerializer):
    """创建运维记录序列化器"""
    assistant = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text='协助人用户ID列表',
    )
    update_logs = UpdateLogInputSerializer(many=True, required=False, default=list, write_only=True)

    class Meta:
        model = MaintenanceRecord
        fields = (
            'region', 'department', 'requester', 'request_date',
            'issue_type', 'functional_module', 'issue_description', 'priority',
            'assistant', 'completion_status', 'completion_time', 'update_logs',
        )

    def validate_assistant(self, value):
        return _validate_assistant_ids(value)

    def validate(self, attrs):
        return _validate_completion_time(attrs)


class MaintenanceRecordUpdateSerializer(serializers.ModelSerializer):
    """更新运维记录序列化器"""
    assistant = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text='协助人用户ID列表',
    )
    update_logs = UpdateLogInputSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = MaintenanceRecord
        fields = (
            'region', 'department', 'requester', 'request_date',
            'issue_type', 'functional_module', 'issue_description', 'priority',
            'assistant', 'completion_status', 'completion_time', 'update_logs',
        )

    def validate_assistant(self, value):
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f'validate_assistant收到值: {value}, 类型: {type(value)}')
        return _validate_assistant_ids(value)

    def validate(self, attrs):
        return _validate_completion_time(attrs)

    def update(self, instance, validated_data):
        """重写update方法，确保assistant字段能正确保存（包括空列表）"""
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f'更新实例，validated_data: {validated_data}')

        if 'assistant' in validated_data:
            assistant_value = validated_data.pop('assistant')
            logger.debug(f'设置assistant字段为: {assistant_value}')
            instance.assistant = assistant_value if assistant_value else []

        return super().update(instance, validated_data)
