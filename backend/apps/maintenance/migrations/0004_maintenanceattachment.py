from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import apps.tasks.storage


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0003_change_assistant_to_jsonfield'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MaintenanceAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(storage=apps.tasks.storage.DateBasedFileStorage(), upload_to='', verbose_name='文件')),
                ('original_filename', models.CharField(max_length=255, verbose_name='原始文件名')),
                ('file_size', models.BigIntegerField(verbose_name='文件大小（字节）')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='上传时间')),
                ('record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='maintenance.maintenancerecord', verbose_name='运维记录')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='上传人')),
            ],
            options={
                'verbose_name': '运维记录附件',
                'verbose_name_plural': '运维记录附件',
                'db_table': 'maintenance_attachments',
                'ordering': ['-created_at'],
            },
        ),
    ]
