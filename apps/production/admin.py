from django.contrib import admin
from .models import (
    ManufacturingJob,
    ProductionPlan,
    WorkCenter,
    RoutingOperation,
    WorkOrder,
    ProductionOrder,
    ProductionScheduleItem,
    ProductionEntry,
    WIPRecord,
    ProductionHold,
    ReworkOrder,
    ProductionScrap,
    FinishedGoodsItem,
    ProductionMaterialRequest,
    DispatchOrder,
)

@admin.register(ManufacturingJob)
class ManufacturingJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_number', 'project_id', 'project_number', 'customer_id', 'customer_name')
    search_fields = ('id', 'job_number', 'project_id', 'project_number')
    list_filter = ('planned_start_date', 'planned_completion_date', 'actual_start_date', 'actual_completion_date')

@admin.register(ProductionPlan)
class ProductionPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan_number', 'job_id', 'job_number', 'project_id', 'product_name')
    search_fields = ('id', 'plan_number', 'job_id', 'job_number')
    list_filter = ('material_availability_status', 'planned_start_date', 'planned_completion_date', 'status')

@admin.register(WorkCenter)
class WorkCenterAdmin(admin.ModelAdmin):
    list_display = ('id', 'work_center_code', 'work_center_name', 'department', 'machine_name', 'machine_number')
    search_fields = ('id', 'work_center_code', 'work_center_name', 'machine_name')
    list_filter = ('status',)

@admin.register(RoutingOperation)
class RoutingOperationAdmin(admin.ModelAdmin):
    list_display = ('id', 'operation_number', 'operation_name', 'sequence', 'work_center_code', 'work_center_name')
    search_fields = ('id', 'operation_name', 'work_center_code', 'work_center_name')
    list_filter = ('qc_required', 'status')

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'work_order_number', 'job_id', 'job_number', 'project_id', 'customer_id')
    search_fields = ('id', 'work_order_number', 'job_id', 'job_number')
    list_filter = ('planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date')

@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'production_order_number', 'work_order_id', 'work_order_number', 'job_id', 'job_number')
    search_fields = ('id', 'production_order_number', 'work_order_id', 'work_order_number')
    list_filter = ('planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date')

@admin.register(ProductionScheduleItem)
class ProductionScheduleItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'schedule_number', 'job_id', 'job_number', 'work_order_number', 'operation_name')
    search_fields = ('id', 'schedule_number', 'job_id', 'job_number')
    list_filter = ('planned_start', 'planned_end', 'actual_start', 'actual_end')

@admin.register(ProductionEntry)
class ProductionEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'production_entry_number', 'entry_date', 'job_id', 'job_number', 'work_order_number')
    search_fields = ('id', 'production_entry_number', 'job_id', 'job_number')
    list_filter = ('entry_date',)

@admin.register(WIPRecord)
class WIPRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_id', 'job_number', 'work_order_number', 'production_order_number', 'current_operation_name')
    search_fields = ('id', 'job_id', 'job_number', 'work_order_number')
    list_filter = ('start_date', 'expected_completion_date', 'status')

@admin.register(ProductionHold)
class ProductionHoldAdmin(admin.ModelAdmin):
    list_display = ('id', 'hold_number', 'job_id', 'job_number', 'work_order_number', 'operation_name')
    search_fields = ('id', 'hold_number', 'job_id', 'job_number')
    list_filter = ('start_date', 'expected_resume_date', 'resume_date', 'status')

@admin.register(ReworkOrder)
class ReworkOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'rework_number', 'job_id', 'job_number', 'work_order_number', 'production_entry_number')
    search_fields = ('id', 'rework_number', 'job_id', 'job_number')
    list_filter = ('start_date', 'completion_date', 'status')

@admin.register(ProductionScrap)
class ProductionScrapAdmin(admin.ModelAdmin):
    list_display = ('id', 'scrap_number', 'entry_date', 'job_id', 'job_number', 'work_order_number')
    search_fields = ('id', 'scrap_number', 'job_id', 'job_number')
    list_filter = ('entry_date', 'scrap_type')

@admin.register(FinishedGoodsItem)
class FinishedGoodsItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'finished_goods_number', 'job_id', 'job_number', 'work_order_number', 'production_order_number')
    search_fields = ('id', 'finished_goods_number', 'job_id', 'job_number')
    list_filter = ('completion_date', 'qc_status', 'status', 'created_at')


@admin.register(ProductionMaterialRequest)
class ProductionMaterialRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'request_number', 'job_number', 'work_order_number', 'requested_by', 'issued_to', 'warehouse_name', 'total_value', 'status')
    search_fields = ('id', 'request_number', 'job_number', 'work_order_number', 'requested_by', 'issued_to')
    list_filter = ('status', 'production_stage', 'created_at')

@admin.register(DispatchOrder)
class DispatchOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'dispatch_number', 'dispatch_date', 'job_number', 'customer_name', 'product_name', 'quantity', 'vehicle_number', 'status')
    search_fields = ('id', 'dispatch_number', 'job_number', 'customer_name', 'product_name', 'vehicle_number', 'invoice_number')
    list_filter = ('status', 'dispatch_date', 'dispatch_type', 'created_at')
