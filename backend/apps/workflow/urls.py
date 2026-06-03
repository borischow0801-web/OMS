from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkflowLogViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'logs', WorkflowLogViewSet, basename='workflow-log')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]

