from django.contrib import admin
from .models import CompanySetting, NumberingSetting, AuditLog, Notification

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
