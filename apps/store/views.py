from datetime import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

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
from .serializers import (
    ItemCategorySerializer,
    UOMMasterSerializer,
    ItemMasterSerializer,
    WarehouseSerializer,
    WarehouseLocationSerializer,
    GoodsReceiptNoteSerializer,
    QCInspectionSerializer,
    StockBalanceSerializer,
    StockReservationSerializer,
    MaterialIssueSerializer,
    MaterialReturnSerializer,
    StockLedgerEntrySerializer,
    ScrapEntrySerializer,
)


class ItemCategoryViewSet(viewsets.ModelViewSet):
    queryset = ItemCategory.objects.all().order_by('name')
    serializer_class = ItemCategorySerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            data['id'] = data.get('code') or data.get('categoryCode') or f"CAT-{ItemCategory.objects.count() + 1:03d}"
        if 'code' not in data:
            data['code'] = data.get('categoryCode') or data.get('id')
        if 'name' not in data:
            data['name'] = data.get('categoryName') or data.get('name') or 'General Category'
        if 'description' not in data:
            data['description'] = data.get('desc') or ''
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UOMMasterViewSet(viewsets.ModelViewSet):
    queryset = UOMMaster.objects.all().order_by('code')
    serializer_class = UOMMasterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            data['id'] = data.get('code') or data.get('uomCode') or f"UOM-{UOMMaster.objects.count() + 1:03d}"
        if 'code' not in data:
            data['code'] = data.get('uomCode') or data.get('id')
        if 'name' not in data:
            data['name'] = data.get('uomName') or data.get('name') or data.get('code') or 'Unit'
        if 'description' not in data:
            data['description'] = data.get('desc') or ''
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ItemMasterViewSet(viewsets.ModelViewSet):
    queryset = ItemMaster.objects.all().order_by('item_code')
    serializer_class = ItemMasterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            data['id'] = data.get('item_code') or data.get('itemCode') or f"ITM-{ItemMaster.objects.count() + 1:04d}"
        if 'item_code' not in data:
            data['item_code'] = data.get('itemCode') or data.get('id')
        if 'item_name' not in data:
            data['item_name'] = data.get('itemName') or 'Item'
        if 'item_type' not in data:
            data['item_type'] = data.get('itemType') or 'Raw Material'
        if 'category' not in data:
            data['category'] = data.get('categoryName') or 'General'
        if 'sub_category' not in data:
            data['sub_category'] = data.get('subCategory') or ''
        if 'specification' not in data:
            data['specification'] = data.get('spec') or ''
        if 'brand_make' not in data:
            data['brand_make'] = data.get('brandMake') or ''
        if 'hsn_sac' not in data:
            data['hsn_sac'] = data.get('hsnSac') or '72193200'
        if 'gst_rate' not in data:
            data['gst_rate'] = data.get('gstRate') or 18.0
        if 'uom' not in data:
            data['uom'] = data.get('uomCode') or 'Kg'
        if 'minimum_stock' not in data:
            data['minimum_stock'] = data.get('minimumStock') or 0
        if 'maximum_stock' not in data:
            data['maximum_stock'] = data.get('maximumStock') or 0
        if 'reorder_level' not in data:
            data['reorder_level'] = data.get('reorderLevel') or 0
        if 'unit_cost' not in data:
            data['unit_cost'] = data.get('standardCost') or data.get('unitCost') or 0

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all().order_by('warehouse_code')
    serializer_class = WarehouseSerializer
    permission_classes = [permissions.AllowAny]


class WarehouseLocationViewSet(viewsets.ModelViewSet):
    queryset = WarehouseLocation.objects.all().order_by('code')
    serializer_class = WarehouseLocationSerializer
    permission_classes = [permissions.AllowAny]


class GoodsReceiptNoteViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceiptNote.objects.all().order_by('-date')
    serializer_class = GoodsReceiptNoteSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id') and not data.get('grn_number') and not data.get('grnNumber'):
            code = f"GRN-2026-{GoodsReceiptNote.objects.count() + 1:04d}"
            data['id'] = code
            data['grn_number'] = code
        elif not data.get('id'):
            data['id'] = data.get('grn_number') or data.get('grnNumber')

        if 'grn_number' not in data:
            data['grn_number'] = data.get('grnNumber') or data.get('id')
        if 'date' not in data:
            data['date'] = data.get('grnDate') or data.get('receiptDate') or datetime.now().strftime('%Y-%m-%d')
        if 'po_id' not in data:
            data['po_id'] = data.get('poId') or ''
        if 'po_number' not in data:
            data['po_number'] = data.get('poNumber') or ''
        if 'supplier_id' not in data:
            data['supplier_id'] = data.get('supplierId') or 'SUP-001'
        if 'supplier_name' not in data:
            data['supplier_name'] = data.get('supplierName') or 'Supplier'
        if 'challan_number' not in data:
            data['challan_number'] = data.get('deliveryChallanNumber') or data.get('challanNumber') or ''
        if 'invoice_number' not in data:
            data['invoice_number'] = data.get('invoiceNumber') or ''
        if 'vehicle_number' not in data:
            data['vehicle_number'] = data.get('vehicleNumber') or ''
        if 'received_by' not in data:
            data['received_by'] = data.get('receivedBy') or 'Store Officer'
        if 'warehouse_id' not in data:
            data['warehouse_id'] = data.get('warehouseId') or 'WH-001'
        if 'notes' not in data:
            data['notes'] = data.get('remarks') or data.get('notes') or ''
        if 'items' not in data or not data['items']:
            data['items'] = []

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        grn = serializer.save()

        # Update Stock Balance and Ledger for accepted items
        for itm in grn.items:
            item_code = itm.get('itemCode') or itm.get('item_code')
            qty = float(itm.get('acceptedQty') or itm.get('receivedQty') or itm.get('quantity', 0))
            rate = float(itm.get('unitRate') or itm.get('rate', 0))

            bal = StockBalance.objects.filter(item_code=item_code, warehouse_id=grn.warehouse_id).first()
            if not bal:
                bal = StockBalance(
                    id=f"stk-{item_code.lower()}",
                    item_id=itm.get('itemId', item_code),
                    item_code=item_code,
                    item_name=itm.get('itemName', item_code),
                    warehouse_id=grn.warehouse_id,
                    quantity=0,
                    available_quantity=0,
                    unit_rate=rate,
                )
            bal.quantity += qty
            bal.available_quantity += qty
            bal.total_value = bal.quantity * (bal.unit_rate or rate)
            bal.save()

            # Record in perpetual stock ledger
            StockLedgerEntry.objects.create(
                id=f"ledg-{grn.grn_number.lower()}-{item_code.lower()}",
                date=grn.date,
                transaction_type='GRN',
                reference_number=grn.grn_number,
                item_id=itm.get('itemId', item_code),
                item_code=item_code,
                item_name=itm.get('itemName', item_code),
                warehouse_id=grn.warehouse_id,
                inward_quantity=qty,
                outward_quantity=0,
                closing_quantity=bal.quantity,
                unit_rate=rate,
                total_amount=qty * rate,
                performed_by=grn.received_by,
            )

        return Response(GoodsReceiptNoteSerializer(grn).data, status=status.HTTP_201_CREATED)


class QCInspectionViewSet(viewsets.ModelViewSet):
    queryset = QCInspection.objects.all().order_by('-inspection_date')
    serializer_class = QCInspectionSerializer
    permission_classes = [permissions.AllowAny]


class StockBalanceViewSet(viewsets.ModelViewSet):
    queryset = StockBalance.objects.all().order_by('item_code')
    serializer_class = StockBalanceSerializer
    permission_classes = [permissions.AllowAny]


class StockReservationViewSet(viewsets.ModelViewSet):
    queryset = StockReservation.objects.all().order_by('-reserved_date')
    serializer_class = StockReservationSerializer
    permission_classes = [permissions.AllowAny]


class MaterialIssueViewSet(viewsets.ModelViewSet):
    queryset = MaterialIssue.objects.all().order_by('-issue_date')
    serializer_class = MaterialIssueSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id') or not data.get('issue_number') and not data.get('issueNumber'):
            code = f"ISSUE-2026-{MaterialIssue.objects.count() + 1:04d}"
            data['id'] = code
            data['issue_number'] = code
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        issue = serializer.save()

        # Deduct from Stock Balance and log outward in Stock Ledger
        for itm in issue.items:
            item_code = itm.get('itemCode') or itm.get('item_code')
            qty = float(itm.get('issuedQty') or itm.get('issued_qty') or itm.get('quantity', 0))

            bal = StockBalance.objects.filter(item_code=item_code).first()
            if bal:
                bal.quantity = max(0, bal.quantity - qty)
                bal.available_quantity = max(0, bal.available_quantity - qty)
                bal.total_value = bal.quantity * bal.unit_rate
                bal.save()

                StockLedgerEntry.objects.create(
                    id=f"ledg-{issue.issue_number.lower()}-{item_code.lower()}",
                    date=issue.issue_date,
                    transaction_type='Material Issue',
                    reference_number=issue.issue_number,
                    item_id=bal.item_id,
                    item_code=item_code,
                    item_name=bal.item_name,
                    warehouse_id=issue.warehouse_id,
                    inward_quantity=0,
                    outward_quantity=qty,
                    closing_quantity=bal.quantity,
                    unit_rate=bal.unit_rate,
                    total_amount=qty * bal.unit_rate,
                    performed_by=issue.issued_to,
                )

        return Response(MaterialIssueSerializer(issue).data, status=status.HTTP_201_CREATED)


class MaterialReturnViewSet(viewsets.ModelViewSet):
    queryset = MaterialReturn.objects.all().order_by('-return_date')
    serializer_class = MaterialReturnSerializer
    permission_classes = [permissions.AllowAny]


class StockLedgerEntryViewSet(viewsets.ModelViewSet):
    queryset = StockLedgerEntry.objects.all().order_by('-created_at')
    serializer_class = StockLedgerEntrySerializer
    permission_classes = [permissions.AllowAny]


class ScrapEntryViewSet(viewsets.ModelViewSet):
    queryset = ScrapEntry.objects.all().order_by('-date')
    serializer_class = ScrapEntrySerializer
    permission_classes = [permissions.AllowAny]
