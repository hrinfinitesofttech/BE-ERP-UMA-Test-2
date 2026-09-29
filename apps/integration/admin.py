from django.contrib import admin
from .models import (
    ApprovalItem,
    ERPAlertItem,
    Job360Overview,
    ExecutiveDashboardKPI,
    Customer360Summary,
    Supplier360Summary,
    ItemMaterial360Summary,
    Employee360Summary,
    GlobalActivityLog,
    ERPReportCenterItem,
    JobProfitabilityRecord,
)

@admin.register(ApprovalItem)
class ApprovalItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'title', 'record_number', 'requester_name', 'status')
    search_fields = ('id', 'title', 'record_number', 'requester_name')
    list_filter = ('category', 'status')

@admin.register(ERPAlertItem)
class ERPAlertItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'module', 'severity', 'title', 'timestamp', 'is_read')
    search_fields = ('id', 'title', 'description')
    list_filter = ('module', 'severity', 'is_read')

@admin.register(Job360Overview)
class Job360OverviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_number', 'customer_name', 'product_name', 'current_status', 'progress_percent')
    search_fields = ('job_number', 'customer_name', 'product_name')
    list_filter = ('current_status', 'priority')

@admin.register(ExecutiveDashboardKPI)
class ExecutiveDashboardKPIAdmin(admin.ModelAdmin):
    list_display = ('id', 'kpi_name', 'category', 'current_value', 'target_value', 'period')
    search_fields = ('kpi_name', 'category')
    list_filter = ('category', 'period')

@admin.register(Customer360Summary)
class Customer360SummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'total_revenue_billed', 'active_projects_count', 'outstanding_receivable')
    search_fields = ('customer_name', 'customer_id')

@admin.register(Supplier360Summary)
class Supplier360SummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier_name', 'category', 'total_purchase_spend', 'on_time_delivery_rate')
    search_fields = ('supplier_name', 'supplier_id')

@admin.register(ItemMaterial360Summary)
class ItemMaterial360SummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'item_code', 'item_name', 'current_stock', 'total_stock_value')
    search_fields = ('item_code', 'item_name')

@admin.register(Employee360Summary)
class Employee360SummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee_name', 'employee_id', 'department', 'designation', 'performance_rating')
    search_fields = ('employee_name', 'employee_id', 'department')

@admin.register(GlobalActivityLog)
class GlobalActivityLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'module', 'action', 'user_name', 'date', 'time')
    search_fields = ('module', 'action', 'user_name', 'details')
    list_filter = ('module', 'date')

@admin.register(ERPReportCenterItem)
class ERPReportCenterItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'report_code', 'title', 'category', 'frequency')
    search_fields = ('report_code', 'title')
    list_filter = ('category', 'frequency')

@admin.register(JobProfitabilityRecord)
class JobProfitabilityRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_number', 'customer_name', 'contract_price', 'total_cost', 'profit_margin_percent')
    search_fields = ('job_number', 'customer_name')
    list_filter = ('status',)
