# Generated manually for SMS functionality

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0005_alter_task_task_type'),
        ('workflow', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SmsConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='default', max_length=100, unique=True, verbose_name='配置名称')),
                ('api_url', models.URLField(verbose_name='短信接口地址')),
                ('api_params', models.TextField(help_text='JSON格式的接口参数模板，使用{phone}、{content}等占位符', verbose_name='接口参数模板')),
                ('is_enabled', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '短信配置',
                'verbose_name_plural': '短信配置',
                'db_table': 'sms_configs',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='SmsTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_type', models.CharField(choices=[('task_submitted', '任务提交'), ('task_reviewed', '任务审核通过'), ('task_reviewed_rejected', '任务审核不通过'), ('task_assigned', '任务分配'), ('task_completed', '任务完成')], max_length=50, unique=True, verbose_name='模板类型')),
                ('content', models.TextField(help_text='短信内容模板，使用{任务标题}等占位符', verbose_name='模板内容')),
                ('is_enabled', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '短信模板',
                'verbose_name_plural': '短信模板',
                'db_table': 'sms_templates',
                'ordering': ['template_type'],
            },
        ),
        migrations.CreateModel(
            name='SmsRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(max_length=20, verbose_name='手机号')),
                ('content', models.TextField(verbose_name='短信内容')),
                ('template_type', models.CharField(blank=True, max_length=50, null=True, verbose_name='模板类型')),
                ('status', models.CharField(choices=[('pending', '待发送'), ('success', '发送成功'), ('failed', '发送失败')], default='pending', max_length=20, verbose_name='发送状态')),
                ('error_message', models.TextField(blank=True, null=True, verbose_name='错误信息')),
                ('response_data', models.TextField(blank=True, null=True, verbose_name='接口响应数据')),
                ('sent_at', models.DateTimeField(blank=True, null=True, verbose_name='发送时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('recipient', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sms_received', to=settings.AUTH_USER_MODEL, verbose_name='接收人')),
                ('task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sms_records', to='tasks.task', verbose_name='关联任务')),
            ],
            options={
                'verbose_name': '短信发送记录',
                'verbose_name_plural': '短信发送记录',
                'db_table': 'sms_records',
                'ordering': ['-created_at'],
            },
        ),
    ]

