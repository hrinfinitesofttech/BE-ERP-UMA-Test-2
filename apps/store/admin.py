from django.contrib import admin
from .models import ItemCategory, UOMMaster, ItemMaster, Warehouse, WarehouseLocation, GoodsReceiptNote, QCInspection, StockBalance, StockReservation, MaterialIssue, MaterialReturn, StockLedgerEntry, ScrapEntry

@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code')
    search_fields = ('id', 'name', 'code')

@admin.register(UOMMaster)
class UOMMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code')
    search_fields = ('id', 'name', 'code')

@admin.register(ItemMaster)
class ItemMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'item_code', 'item_name', 'item_type', 'category', 'sub_category')
    search_fields = ('id', 'item_code', 'item_name', 'drawing_number')
    list_filter = ('item_type', 'category', 'sub_category', 'status')

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('id', 'warehouse_code', 'name', 'warehouse_type', 'location', 'incharge')
    search_fields = ('id', 'warehouse_code', 'name')
    list_filter = ('warehouse_type', 'status')

@admin.register(WarehouseLocation)
class WarehouseLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'warehouse_id', 'rack', 'bin', 'shelf', 'code')
    search_fields = ('id', 'warehouse_id', 'code')

@admin.register(GoodsReceiptNote)
class GoodsReceiptNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'grn_number', 'date', 'po_id', 'po_number', 'supplier_id')
    search_fields = ('id', 'grn_number', 'po_id', 'po_number')
    list_filter = ('status', 'qc_status', 'created_at', 'updated_at')

@admin.register(QCInspection)
class QCInspectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'grn_id', 'grn_number', 'inspection_date', 'inspector', 'overall_result')
    search_fields = ('id', 'grn_id', 'grn_number')
    list_filter = ('overall_result', 'created_at')

@admin.register(StockBalance)
class StockBalanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'item_id', 'item_code', 'item_name', 'category', 'uom')
    search_fields = ('id', 'item_id', 'item_code', 'item_name')
    list_filter = ('category', 'updated_at')

@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'reservation_number', 'project_id', 'job_number', 'item_id', 'item_code')
    search_fields = ('id', 'reservation_number', 'project_id', 'job_number')
    list_filter = ('status',)

@admin.register(MaterialIssue)
class MaterialIssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'issue_number', 'project_id', 'job_number', 'work_order_id', 'department')
    search_fields = ('id', 'issue_number', 'project_id', 'job_number')
    list_filter = ('status', 'created_at')

@admin.register(MaterialReturn)
class MaterialReturnAdmin(admin.ModelAdmin):
    list_display = ('id', 'return_number', 'project_id', 'job_number', 'returned_by', 'department')
    search_fields = ('id', 'return_number', 'project_id', 'job_number')
    list_filter = ('status', 'created_at')

@admin.register(StockLedgerEntry)
class StockLedgerEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'transaction_type', 'reference_number', 'item_id', 'item_code')
    search_fields = ('id', 'reference_number', 'item_id', 'item_code')
    list_filter = ('transaction_type', 'created_at')

@admin.register(ScrapEntry)
class ScrapEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'scrap_number', 'date', 'source', 'source_reference', 'item_id')
    search_fields = ('id', 'scrap_number', 'source_reference', 'item_id')
    list_filter = ('status',)
