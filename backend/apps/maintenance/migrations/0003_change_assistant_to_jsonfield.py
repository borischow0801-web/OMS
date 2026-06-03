# Generated migration to change assistant field from CharField to JSONField

from django.db import migrations, models
import json


def convert_assistant_to_list(apps, schema_editor):
    """将现有的单个协助人用户名从旧字段迁移到新字段（列表格式）"""
    MaintenanceRecord = apps.get_model('maintenance', 'MaintenanceRecord')
    
    for record in MaintenanceRecord.objects.all():
        # 读取旧的 assistant_old 字段值
        old_value = getattr(record, 'assistant_old', None)
        
        if old_value:
            # 如果old_value是字符串且不为空，转换为列表
            if isinstance(old_value, str) and old_value.strip():
                record.assistant = [old_value]
            else:
                record.assistant = []
        else:
            record.assistant = []
        record.save()


def convert_assistant_to_string(apps, schema_editor):
    """回滚：将新字段的值转换回旧字段（取第一个）"""
    # 注意：回滚时，assistant_old 字段已被删除，assistant 是新字段
    # 但在这个函数中，我们需要假设 assistant_old 已经恢复（通过 RemoveField 的逆向操作）
    MaintenanceRecord = apps.get_model('maintenance', 'MaintenanceRecord')
    
    # 检查 assistant_old 字段是否存在（回滚时会重新创建）
    if hasattr(MaintenanceRecord, 'assistant_old'):
        for record in MaintenanceRecord.objects.all():
            new_value = getattr(record, 'assistant', None)
            
            if new_value:
                # 如果是列表，取第一个元素
                if isinstance(new_value, list) and len(new_value) > 0:
                    record.assistant_old = new_value[0]
                # 如果已经是字符串，直接使用
                elif isinstance(new_value, str):
                    record.assistant_old = new_value
                else:
                    record.assistant_old = ''
            else:
                record.assistant_old = ''
            record.save()


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0002_update_issue_type_choices'),
    ]

    operations = [
        # 步骤1: 将旧字段重命名为临时名称
        migrations.RenameField(
            model_name='maintenancerecord',
            old_name='assistant',
            new_name='assistant_old',
        ),
        # 步骤2: 添加新的 JSONField 字段
        migrations.AddField(
            model_name='maintenancerecord',
            name='assistant',
            field=models.JSONField(blank=True, default=list, help_text='存储协助人用户名列表', null=True, verbose_name='协助人'),
        ),
        # 步骤3: 迁移数据（将旧字段的值转换为列表格式存储到新字段）
        migrations.RunPython(convert_assistant_to_list, convert_assistant_to_string),
        # 步骤4: 删除旧字段
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='assistant_old',
        ),
    ]
