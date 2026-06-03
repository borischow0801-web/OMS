from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0004_maintenanceattachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='maintenancerecord',
            name='completion_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='完成时间'),
        ),
        migrations.CreateModel(
            name='MaintenanceUpdateLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='更新内容')),
                ('update_time', models.DateTimeField(verbose_name='更新时间')),
                ('record', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='update_logs',
                    to='maintenance.maintenancerecord',
                    verbose_name='运维记录',
                )),
            ],
            options={
                'verbose_name': '更新内容记录',
                'verbose_name_plural': '更新内容记录',
                'db_table': 'maintenance_update_logs',
                'ordering': ['update_time'],
            },
        ),
    ]
