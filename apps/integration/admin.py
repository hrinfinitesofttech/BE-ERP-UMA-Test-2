from django.contrib import admin
from .models import ApprovalItem, ERPAlertItem

@admin.register(ApprovalItem)
class ApprovalItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'title', 'record_number', 'requester_name', 'requester_role')
    search_fields = ('id', 'title', 'record_number', 'requester_name')
    list_filter = ('category', 'requester_role', 'request_date', 'status')

@admin.register(ERPAlertItem)
class ERPAlertItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'module', 'severity', 'title', 'target_url', 'timestamp')
    search_fields = ('id', 'title')
    list_filter = ('timestamp', 'is_read')
