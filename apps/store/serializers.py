from rest_framework import serializers
from .models import (
    ItemCategory,
    UOMMaster,
    ItemMaster,
    Warehouse,
    WarehouseLocation,
    GoodsReceiptNote,
    QCInspection,
    StockBalance,
    StockReservation,
    MaterialIssue,
    MaterialReturn,
    StockLedgerEntry,
    ScrapEntry,
)


class ItemCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory
        fields = ['id', 'name', 'code', 'description']


class UOMMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UOMMaster
        fields = ['id', 'name', 'code', 'description']


class ItemMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemMaster
        fields = [
            'id',
            'item_code',
            'item_name',
            'item_type',
            'category',
            'sub_category',
            'description',
            'specification',
            'drawing_number',
            'brand_make',
            'hsn_sac',
            'gst_rate',
            'uom',
            'minimum_stock',
            'maximum_stock',
            'reorder_level',
            'unit_cost',
            'status',
        ]


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = [
            'id',
            'warehouse_code',
            'name',
            'warehouse_type',
            'location',
            'incharge',
            'status',
        ]


class WarehouseLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseLocation
        fields = ['id', 'warehouse_id', 'rack', 'bin', 'shelf', 'code']


class GoodsReceiptNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsReceiptNote
        fields = [
            'id',
            'grn_number',
            'date',
            'po_id',
            'po_number',
            'supplier_id',
            'supplier_name',
            'challan_number',
            'challan_date',
            'invoice_number',
            'invoice_date',
            'vehicle_number',
            'received_by',
            'warehouse_id',
            'items',
            'status',
            'qc_status',
            'notes',
        ]


class QCInspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QCInspection
        fields = [
            'id',
            'grn_id',
            'grn_number',
            'inspection_date',
            'inspector',
            'items',
            'overall_result',
            'remarks',
        ]


class StockBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockBalance
        fields = [
            'id',
            'item_id',
            'item_code',
            'item_name',
            'category',
            'uom',
            'warehouse_id',
            'warehouse_name',
            'location',
            'quantity',
            'reserved_quantity',
            'available_quantity',
            'unit_rate',
            'total_value',
        ]


class StockReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockReservation
        fields = [
            'id',
            'reservation_number',
            'project_id',
            'job_number',
            'item_id',
            'item_code',
            'item_name',
            'reserved_quantity',
            'reserved_date',
            'reserved_by',
            'status',
        ]


class MaterialIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialIssue
        fields = [
            'id',
            'issue_number',
            'project_id',
            'job_number',
            'work_order_id',
            'department',
            'issued_to',
            'issue_date',
            'warehouse_id',
            'items',
            'status',
            'notes',
        ]


class MaterialReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialReturn
        fields = [
            'id',
            'return_number',
            'project_id',
            'job_number',
            'returned_by',
            'department',
            'return_date',
            'warehouse_id',
            'items',
            'status',
            'notes',
        ]


class StockLedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockLedgerEntry
        fields = [
            'id',
            'date',
            'transaction_type',
            'reference_number',
            'item_id',
            'item_code',
            'item_name',
            'warehouse_id',
            'inward_quantity',
            'outward_quantity',
            'closing_quantity',
            'unit_rate',
            'total_amount',
            'performed_by',
        ]


class ScrapEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapEntry
        fields = [
            'id',
            'scrap_number',
            'date',
            'source',
            'source_reference',
            'item_id',
            'item_code',
            'quantity',
            'uom',
            'disposal_method',
            'estimated_value',
            'status',
        ]
