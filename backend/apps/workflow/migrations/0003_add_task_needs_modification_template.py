# Generated manually for adding task_needs_modification template type

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0002_sms_models'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smstemplate',
            name='template_type',
            field=models.CharField(
                choices=[
                    ('task_submitted', '任务提交'),
                    ('task_reviewed', '任务审核通过'),
                    ('task_reviewed_rejected', '任务审核不通过'),
                    ('task_assigned', '任务分配'),
                    ('task_completed', '任务完成'),
                    ('task_needs_modification', '任务需要修改'),
                ],
                max_length=50,
                unique=True,
                verbose_name='模板类型'
            ),
        ),
    ]

