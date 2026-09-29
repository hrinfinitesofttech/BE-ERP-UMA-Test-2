from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanySettingView,
    NumberingSettingViewSet,
    AuditLogViewSet,
    NotificationViewSet,
    BugTicketViewSet,
    BackupRecordViewSet,
    DataImportLogViewSet,
    SecurityCheckRecordViewSet,
    GoLiveChecklistItemViewSet,
)

router = DefaultRouter()
router.register(r'numbering', NumberingSettingViewSet, basename='numbering')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'bug-tickets', BugTicketViewSet, basename='bug-ticket')
router.register(r'backups', BackupRecordViewSet, basename='backup')
router.register(r'data-imports', DataImportLogViewSet, basename='data-import')
router.register(r'security-checks', SecurityCheckRecordViewSet, basename='security-check')
router.register(r'go-live-checklist', GoLiveChecklistItemViewSet, basename='go-live-checklist')


urlpatterns = [
    path('company/', CompanySettingView.as_view(), name='company-settings'),
    path('', include(router.urls)),
]
