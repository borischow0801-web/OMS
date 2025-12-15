"""
URL configuration for oms_backend project.
"""
import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/tasks/', include('apps.tasks.urls')),
    path('api/workflow/', include('apps.workflow.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # 添加附件文件访问路径
    attachment_root = getattr(settings, 'ATTACHMENT_ROOT', os.path.join(settings.BASE_DIR.parent, 'docs'))
    urlpatterns += static('/docs/', document_root=attachment_root)

