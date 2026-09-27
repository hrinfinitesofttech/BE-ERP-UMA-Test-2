from django.contrib import admin
from .models import InternalAsset, CustomerMachine, ServiceRequest, PreventiveMaintenancePlan, BreakdownRecord, ServiceVisit, AMCContract

@admin.register(InternalAsset)
class InternalAssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'asset_code', 'asset_name', 'asset_type', 'category', 'manufacturer')
    search_fields = ('id', 'asset_code', 'asset_name', 'serial_number')
    list_filter = ('asset_type', 'category', 'purchase_date', 'installation_date')

@admin.register(CustomerMachine)
class CustomerMachineAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_machine_id', 'customer_id', 'customer_name', 'project_id', 'project_name')
    search_fields = ('id', 'customer_machine_id', 'customer_id', 'customer_name')
    list_filter = ('manufacturing_date', 'installation_date', 'commissioning_date', 'warranty_start')

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'request_number', 'request_date', 'origin', 'customer_id', 'customer_name')
    search_fields = ('id', 'request_number', 'customer_id', 'customer_name')
    list_filter = ('request_date', 'complaint_type', 'warranty_status', 'amc_status')

@admin.register(PreventiveMaintenancePlan)
class PreventiveMaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan_number', 'asset_id', 'asset_name', 'customer_machine_id', 'customer_name')
    search_fields = ('id', 'plan_number', 'asset_id', 'asset_name')
    list_filter = ('maintenance_type', 'start_date', 'next_due_date', 'status')

@admin.register(BreakdownRecord)
class BreakdownRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'breakdown_number', 'asset_type', 'asset_id', 'asset_name', 'serial_number')
    search_fields = ('id', 'breakdown_number', 'asset_id', 'asset_name')
    list_filter = ('asset_type', 'breakdown_date', 'status')

@admin.register(ServiceVisit)
class ServiceVisitAdmin(admin.ModelAdmin):
    list_display = ('id', 'visit_number', 'service_request_id', 'request_number', 'customer_id', 'customer_name')
    search_fields = ('id', 'visit_number', 'service_request_id', 'request_number')
    list_filter = ('visit_date', 'status', 'customer_signature')

@admin.register(AMCContract)
class AMCContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'amc_number', 'customer_id', 'customer_name', 'customer_machine_id', 'machine_name')
    search_fields = ('id', 'amc_number', 'customer_id', 'customer_name')
    list_filter = ('contract_start', 'contract_end', 'breakdown_support', 'parts_included')
