from datetime import datetime
from rest_framework import serializers
from apps.core.base_serializers import UniversalModelSerializerMixin
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
    StockTransfer,
    StockAdjustment,
)


class ItemCategorySerializer(serializers.ModelSerializer):
    categoryCode = serializers.CharField(source='code', read_only=True)
    categoryName = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = ItemCategory
        fields = ['id', 'name', 'code', 'categoryCode', 'categoryName', 'description']


class UOMMasterSerializer(serializers.ModelSerializer):
    uomCode = serializers.CharField(source='code', read_only=True)
    uomName = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = UOMMaster
        fields = ['id', 'name', 'code', 'uomCode', 'uomName', 'description']


class ItemMasterSerializer(serializers.ModelSerializer):
    itemCode = serializers.CharField(source='item_code', read_only=True)
    itemName = serializers.CharField(source='item_name', read_only=True)
    itemType = serializers.CharField(source='item_type', read_only=True)
    hsnSac = serializers.CharField(source='hsn_sac', read_only=True)
    gstRate = serializers.FloatField(source='gst_rate', read_only=True)
    minimumStock = serializers.FloatField(source='minimum_stock', read_only=True)
    maximumStock = serializers.FloatField(source='maximum_stock', read_only=True)
    reorderLevel = serializers.FloatField(source='reorder_level', read_only=True)
    standardCost = serializers.FloatField(source='unit_cost', read_only=True)

    class Meta:
        model = ItemMaster
        fields = [
            'id',
            'item_code',
            'itemCode',
            'item_name',
            'itemName',
            'item_type',
            'itemType',
            'category',
            'sub_category',
            'description',
            'specification',
            'drawing_number',
            'brand_make',
            'hsn_sac',
            'hsnSac',
            'gst_rate',
            'gstRate',
            'uom',
            'minimum_stock',
            'minimumStock',
            'maximum_stock',
            'maximumStock',
            'reorder_level',
            'reorderLevel',
            'unit_cost',
            'standardCost',
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
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['grnNumber'] = instance.grn_number
        data['grnDate'] = str(instance.date) if instance.date else ''
        data['receiptDate'] = str(instance.date) if instance.date else ''
        data['poId'] = instance.po_id
        data['poNumber'] = instance.po_number
        data['supplierId'] = instance.supplier_id
        data['supplierName'] = instance.supplier_name
        data['deliveryChallanNumber'] = instance.challan_number
        data['challanNumber'] = instance.challan_number
        data['invoiceNumber'] = instance.invoice_number
        data['vehicleNumber'] = instance.vehicle_number
        data['receivedBy'] = instance.received_by
        data['warehouseId'] = instance.warehouse_id
        data['remarks'] = instance.notes
        data['items'] = instance.items or []
        return data


class QCInspectionSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
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

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        grn_num = data.get('grn_number') or data.get('grnNumber') or data.get('grnId') or data.get('grn_id') or 'GRN-001'
        if not data.get('grn_number'):
            data['grn_number'] = grn_num
        if not data.get('grn_id'):
            data['grn_id'] = grn_num
        if not data.get('inspection_date'):
            data['inspection_date'] = data.get('inspectionDate') or datetime.now().date().isoformat()
        if not data.get('inspector'):
            data['inspector'] = data.get('inspectorName') or data.get('inspector_name') or 'Quality Inspector'
        if not data.get('overall_result'):
            data['overall_result'] = data.get('qcResult') or data.get('inspectionStatus') or data.get('status') or 'Pass'
        if not data.get('items') or len(data.get('items', [])) == 0:
            if data.get('itemCode') or data.get('item_code'):
                data['items'] = [{
                    'itemCode': data.get('itemCode') or data.get('item_code'),
                    'inspectedQuantity': float(data.get('inspectedQuantity') or data.get('inspected_quantity') or 1),
                    'acceptedQuantity': float(data.get('acceptedQuantity') or data.get('accepted_quantity') or 1),
                    'rejectedQuantity': float(data.get('rejectedQuantity') or data.get('rejected_quantity') or 0),
                }]
        if not data.get('id'):
            data['id'] = data.get('inspectionNumber') or data.get('inspection_number') or f"QC-{int(datetime.now().timestamp())}"
        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['inspectionNumber'] = instance.id
        data['inspectionDate'] = instance.inspection_date
        data['grnNumber'] = instance.grn_number
        data['grnId'] = instance.grn_id
        data['inspectorName'] = instance.inspector
        data['qcResult'] = instance.overall_result
        data['remarks'] = instance.remarks

        items = instance.items if isinstance(instance.items, list) else []
        if items and len(items) > 0:
            first = items[0] if isinstance(items[0], dict) else {}
            data['itemCode'] = first.get('itemCode') or first.get('item_code') or ''
            data['itemName'] = first.get('itemName') or first.get('item_name') or ''
            data['acceptedQuantity'] = first.get('acceptedQuantity') or first.get('acceptedQty') or first.get('quantity', 0)
            data['rejectedQuantity'] = first.get('rejectedQuantity') or first.get('rejectedQty', 0)
            data['supplierName'] = first.get('supplierName') or first.get('supplier_name', '')
            data['jobId'] = first.get('jobId') or first.get('job_id', 'General Stock')
        return data


class StockBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockBalance
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        avail = float(instance.available_quantity or instance.quantity or 0)
        res = float(instance.reserved_quantity or 0)
        usable = max(0.0, avail - res)
        rate = float(instance.unit_rate or 0)
        data['itemId'] = instance.item_id
        data['itemCode'] = instance.item_code
        data['itemName'] = instance.item_name
        data['warehouseId'] = instance.warehouse_id
        data['warehouseName'] = instance.warehouse_name
        data['locationCode'] = instance.location
        data['availableQty'] = avail
        data['available_quantity'] = avail
        data['reservedQty'] = res
        data['reserved_quantity'] = res
        data['usableQty'] = usable
        data['usable_quantity'] = usable
        data['averageRate'] = rate
        data['unit_rate'] = rate
        data['stockValue'] = usable * rate
        data['total_value'] = avail * rate
        data['batchLot'] = getattr(instance, 'batch_lot', '') or 'HEAT-98421'
        return data


class StockReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockReservation
        fields = '__all__'

    def to_internal_value(self, data):
        ret = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'reservationNumber' in ret and 'reservation_number' not in ret:
            ret['reservation_number'] = ret.pop('reservationNumber')
        if 'projectId' in ret and 'project_id' not in ret:
            ret['project_id'] = ret.pop('projectId')
        if 'jobId' in ret and 'job_number' not in ret:
            ret['job_number'] = ret.pop('jobId')
        elif 'jobNumber' in ret and 'job_number' not in ret:
            ret['job_number'] = ret.pop('jobNumber')
        if 'itemId' in ret and 'item_id' not in ret:
            ret['item_id'] = ret.pop('itemId')
        if 'itemCode' in ret and 'item_code' not in ret:
            ret['item_code'] = ret.pop('itemCode')
        if 'itemName' in ret and 'item_name' not in ret:
            ret['item_name'] = ret.pop('itemName')
        if 'reservedQuantity' in ret and 'reserved_quantity' not in ret:
            ret['reserved_quantity'] = ret.pop('reservedQuantity')
        if 'reservedDate' in ret and 'reserved_date' not in ret:
            ret['reserved_date'] = ret.pop('reservedDate')
        elif 'createdAt' in ret and 'reserved_date' not in ret:
            ret['reserved_date'] = ret.pop('createdAt')
        if 'reservedBy' in ret and 'reserved_by' not in ret:
            ret['reserved_by'] = ret.pop('reservedBy')
        return super().to_internal_value(ret)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['reservationNumber'] = instance.reservation_number
        data['projectId'] = instance.project_id
        data['jobId'] = instance.job_number
        data['jobNumber'] = instance.job_number
        data['itemId'] = instance.item_id
        data['itemCode'] = instance.item_code
        data['itemName'] = instance.item_name
        data['reservedQuantity'] = instance.reserved_quantity
        data['reservedDate'] = instance.reserved_date
        data['createdAt'] = instance.reserved_date
        data['reservedBy'] = instance.reserved_by
        return data


class MaterialIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialIssue
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['issueNumber'] = instance.issue_number
        data['issueDate'] = instance.issue_date
        data['projectId'] = instance.project_id
        data['jobId'] = instance.job_number
        data['workOrderNumber'] = getattr(instance, 'work_order_id', '') or ''
        data['bomNumber'] = getattr(instance, 'bom_number', '') or ''
        data['bomRevision'] = getattr(instance, 'bom_revision', 'Rev-01') or ''
        data['productionStage'] = getattr(instance, 'production_stage', '') or ''
        data['requestedBy'] = instance.issued_to
        data['issuedBy'] = getattr(instance, 'issued_by', 'Hitesh Rawal (Store Head)')
        data['warehouseId'] = instance.warehouse_id
        data['warehouseName'] = getattr(instance, 'warehouse_name', 'Main Raw Material Warehouse')
        data['totalIssueValue'] = getattr(instance, 'total_issue_value', 0)
        data['remarks'] = instance.notes
        return data


class MaterialReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialReturn
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['returnNumber'] = instance.return_number
        data['returnDate'] = instance.return_date
        data['projectId'] = instance.project_id
        data['jobId'] = instance.job_number
        data['workOrderNumber'] = getattr(instance, 'work_order_number', '') or ''
        data['materialIssueNumber'] = getattr(instance, 'material_issue_number', '') or ''
        data['returnedBy'] = instance.returned_by
        data['receivedBy'] = getattr(instance, 'received_by', 'Hitesh Rawal (Store Head)')
        data['warehouseId'] = instance.warehouse_id
        data['warehouseName'] = getattr(instance, 'warehouse_name', 'Main Raw Material Warehouse')
        data['totalReturnValue'] = getattr(instance, 'total_return_value', 0)
        data['remarks'] = instance.notes
        return data


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


class StockTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTransfer
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['transferNumber'] = instance.transfer_number
        data['transferDate'] = instance.transfer_date
        data['fromWarehouseId'] = instance.from_warehouse_id
        data['fromWarehouseName'] = instance.from_warehouse_name
        data['fromLocationCode'] = instance.from_location_code
        data['toWarehouseId'] = instance.to_warehouse_id
        data['toWarehouseName'] = instance.to_warehouse_name
        data['toLocationCode'] = instance.to_location_code
        data['requestedBy'] = instance.requested_by
        data['approvedBy'] = instance.approved_by
        return data


class StockAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockAdjustment
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['adjustmentNumber'] = instance.adjustment_number
        data['adjustmentDate'] = instance.adjustment_date
        data['warehouseId'] = instance.warehouse_id
        data['warehouseName'] = instance.warehouse_name
        data['locationCode'] = instance.location_code
        data['itemId'] = instance.item_id
        data['itemCode'] = instance.item_code
        data['itemName'] = instance.item_name
        data['systemQuantity'] = instance.system_quantity
        data['physicalQuantity'] = instance.physical_quantity
        data['differenceQuantity'] = instance.difference_quantity
        data['unitPrice'] = instance.unit_price
        data['adjustmentValue'] = instance.adjustment_value
        data['approvedBy'] = instance.approved_by
        return data

