from django.contrib import admin
from .models import (
    CompanySetting,
    NumberingSetting,
    AuditLog,
    Notification,
    BugTicket,
    BackupRecord,
    DataImportLog,
    SecurityCheckRecord,
    GoLiveChecklistItem,
)

@admin.register(CompanySetting)
class CompanySettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_name', 'tagline', 'logo_url', 'city', 'state')
    search_fields = ('company_name', 'pincode', 'email', 'bank_name')
    list_filter = ('updated_at',)

@admin.register(NumberingSetting)
class NumberingSettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'module', 'doc_type', 'prefix', 'suffix', 'current_number')
    search_fields = ('id', 'prefix')
    list_filter = ('doc_type',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'user_id', 'user_name', 'role', 'department')
    search_fields = ('id', 'user_id', 'user_name', 'record_id')
    list_filter = ('timestamp', 'role')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'title', 'type', 'department', 'link_url')
    search_fields = ('id', 'title')
    list_filter = ('timestamp', 'type', 'is_read')

@admin.register(BugTicket)
class BugTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'bug_no', 'title', 'module_page', 'severity', 'priority', 'status', 'assignee')
    search_fields = ('id', 'bug_no', 'title', 'assignee')
    list_filter = ('severity', 'priority', 'status')

@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'backup_name', 'backup_type', 'file_size', 'status', 'backup_date', 'created_by')
    search_fields = ('id', 'backup_name', 'created_by')
    list_filter = ('status', 'backup_type', 'is_automatic')

@admin.register(DataImportLog)
class DataImportLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'entity_type', 'file_name', 'records_count', 'status', 'imported_by', 'imported_at')
    search_fields = ('id', 'entity_type', 'file_name', 'imported_by')
    list_filter = ('entity_type', 'status')

@admin.register(SecurityCheckRecord)
class SecurityCheckRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'check_name', 'category', 'status', 'severity', 'last_evaluated_at')
    search_fields = ('id', 'check_name', 'category')
    list_filter = ('status', 'severity', 'category')

@admin.register(GoLiveChecklistItem)
class GoLiveChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'module_name', 'item_title', 'status', 'owner', 'signoff_date')
    search_fields = ('id', 'module_name', 'item_title', 'owner')
    list_filter = ('module_name', 'status')


