from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanySettingView,
    NumberingSettingViewSet,
    AuditLogViewSet,
    NotificationViewSet,
)

router = DefaultRouter()
router.register(r'numbering', NumberingSettingViewSet, basename='numbering')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('company/', CompanySettingView.as_view(), name='company-settings'),
    path('', include(router.urls)),
]
