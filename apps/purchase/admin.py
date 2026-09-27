from django.contrib import admin
from .models import Supplier, SupplierContact, PurchaseRequisition, RequestForQuotation, SupplierQuotation, QuotationComparison, PurchaseOrder, PurchaseReturn

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor_code', 'name', 'category', 'supplier_type', 'contact_person')
    search_fields = ('id', 'vendor_code', 'name', 'email')
    list_filter = ('category', 'supplier_type', 'status', 'created_at')

@admin.register(SupplierContact)
class SupplierContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier_id', 'name', 'designation', 'department', 'mobile')
    search_fields = ('id', 'supplier_id', 'name', 'email')
    list_filter = ('is_primary',)

@admin.register(PurchaseRequisition)
class PurchaseRequisitionAdmin(admin.ModelAdmin):
    list_display = ('id', 'pr_number', 'project_id', 'job_code', 'requested_by', 'department')
    search_fields = ('id', 'pr_number', 'project_id', 'job_code')
    list_filter = ('status', 'created_at', 'updated_at')

@admin.register(RequestForQuotation)
class RequestForQuotationAdmin(admin.ModelAdmin):
    list_display = ('id', 'rfq_number', 'pr_id', 'rfq_date', 'due_date', 'status')
    search_fields = ('id', 'rfq_number', 'pr_id')
    list_filter = ('status', 'created_at')

@admin.register(SupplierQuotation)
class SupplierQuotationAdmin(admin.ModelAdmin):
    list_display = ('id', 'quotation_number', 'rfq_id', 'supplier_id', 'supplier_name', 'date')
    search_fields = ('id', 'quotation_number', 'rfq_id', 'supplier_id')
    list_filter = ('status', 'created_at')

@admin.register(QuotationComparison)
class QuotationComparisonAdmin(admin.ModelAdmin):
    list_display = ('id', 'rfq_id', 'comparison_date', 'recommended_supplier_id', 'recommended_supplier_name', 'prepared_by')
    search_fields = ('id', 'rfq_id', 'recommended_supplier_id', 'recommended_supplier_name')
    list_filter = ('status', 'created_at')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'po_number', 'revision_number', 'date', 'supplier_id', 'supplier_name')
    search_fields = ('id', 'po_number', 'revision_number', 'supplier_id')
    list_filter = ('status', 'created_at', 'updated_at')

@admin.register(PurchaseReturn)
class PurchaseReturnAdmin(admin.ModelAdmin):
    list_display = ('id', 'return_number', 'po_id', 'po_number', 'grn_id', 'grn_number')
    search_fields = ('id', 'return_number', 'po_id', 'po_number')
    list_filter = ('status', 'created_at')
