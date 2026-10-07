from datetime import datetime
from django.db.models import Q
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
    StockTransfer,
    StockAdjustment,
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
    StockTransferSerializer,
    StockAdjustmentSerializer,
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
    queryset = GoodsReceiptNote.objects.all().order_by('-created_at', '-id')
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

        # Update Stock Balance, Item Master, and Ledger for accepted items
        for itm in (grn.items or []):
            item_code = str(itm.get('itemCode') or itm.get('item_code') or itm.get('partNumber') or 'ITM-01')
            raw_name = str(itm.get('itemName') or itm.get('item_name') or itm.get('description') or item_code)
            clean_name = raw_name.split(' (')[0].strip()
            qty = float(itm.get('acceptedQuantity') or itm.get('acceptedQty') or itm.get('receivedQuantity') or itm.get('receivedQty') or itm.get('quantity') or 0.0)
            rate = float(itm.get('unitPrice') or itm.get('unitRate') or itm.get('rate') or 0.0)

            bal = StockBalance.objects.filter(item_code=item_code, warehouse_id=grn.warehouse_id).first()
            if not bal:
                bal = StockBalance.objects.filter(Q(item_code=item_code) | Q(item_name=clean_name)).first()
            if not bal:
                bal = StockBalance(
                    id=f"stk-{item_code.lower()}",
                    item_id=itm.get('itemId', item_code),
                    item_code=item_code,
                    item_name=clean_name,
                    warehouse_id=grn.warehouse_id,
                    quantity=0,
                    available_quantity=0,
                    unit_rate=rate,
                )
            bal.quantity += qty
            bal.available_quantity += qty
            bal.total_value = bal.quantity * (bal.unit_rate or rate)
            bal.save()

            # Ensure ItemMaster is also created or updated with current stock
            try:
                item_master = ItemMaster.objects.filter(Q(item_code=item_code) | Q(item_name=clean_name)).first()
                if not item_master:
                    ItemMaster.objects.create(
                        id=f"itm-{item_code.lower()}",
                        item_code=item_code,
                        item_name=clean_name,
                        category=itm.get('category', 'Fasteners, Flanges & Hardware'),
                        uom=itm.get('uom', 'PCS'),
                        unit_cost=rate,
                        status='Active'
                    )
            except Exception:
                pass

            # Record in perpetual stock ledger
            StockLedgerEntry.objects.update_or_create(
                id=f"ledg-{grn.grn_number.lower()}-{item_code.lower()}",
                defaults={
                    'date': grn.date,
                    'transaction_type': 'GRN',
                    'reference_number': grn.grn_number,
                    'item_id': itm.get('itemId', item_code),
                    'item_code': item_code,
                    'item_name': clean_name,
                    'warehouse_id': grn.warehouse_id,
                    'inward_quantity': qty,
                    'outward_quantity': 0,
                    'closing_quantity': bal.quantity,
                    'unit_rate': rate,
                    'total_amount': qty * rate,
                    'performed_by': grn.received_by,
                }
            )

        return Response(GoodsReceiptNoteSerializer(grn).data, status=status.HTTP_201_CREATED)


class QCInspectionViewSet(viewsets.ModelViewSet):
    queryset = QCInspection.objects.all().order_by('-created_at', '-id')
    serializer_class = QCInspectionSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id') and not data.get('inspection_number') and not data.get('inspectionNumber'):
            code = f"QC-2026-{QCInspection.objects.count() + 1:04d}"
            data['id'] = code
            data['inspection_number'] = code
        elif not data.get('id'):
            data['id'] = data.get('inspection_number') or data.get('inspectionNumber')

        if 'grn_id' not in data:
            data['grn_id'] = data.get('grnId') or ''
        if 'grn_number' not in data:
            data['grn_number'] = data.get('grnNumber') or ''
        if 'inspection_date' not in data:
            data['inspection_date'] = data.get('inspectionDate') or datetime.now().strftime('%Y-%m-%d')
        if 'inspector' not in data:
            data['inspector'] = data.get('inspectorName') or data.get('inspector') or 'Suresh Patel (Sr. QC Lead)'
        if 'overall_result' not in data:
            data['overall_result'] = data.get('qcResult') or data.get('result') or 'Pass'
        if 'remarks' not in data:
            data['remarks'] = data.get('remarks') or ''

        if 'items' not in data or not data['items']:
            item_code = data.get('itemCode') or data.get('item_code') or 'RAW-MAT'
            item_name = data.get('itemName') or data.get('item_name') or 'Material'
            acc_qty = data.get('acceptedQuantity') or data.get('acceptedQty') or data.get('sampleQuantity', 1)
            rej_qty = data.get('rejectedQuantity') or data.get('rejectedQty') or 0
            supp = data.get('supplierName') or data.get('supplier_name') or 'Supplier'
            data['items'] = [{
                'itemCode': item_code,
                'itemName': item_name,
                'acceptedQuantity': acc_qty,
                'rejectedQuantity': rej_qty,
                'supplierName': supp,
            }]

        target_id = data.get('id')
        existing = QCInspection.objects.filter(id=target_id).first() if target_id else None
        if not existing and data.get('grn_number'):
            existing = QCInspection.objects.filter(grn_number=data.get('grn_number')).first()

        if existing:
            serializer = self.get_serializer(existing, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            qc = serializer.save()
            return Response(QCInspectionSerializer(qc).data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        qc = serializer.save()
        return Response(QCInspectionSerializer(qc).data, status=status.HTTP_201_CREATED)


class StockBalanceViewSet(viewsets.ModelViewSet):
    queryset = StockBalance.objects.all().order_by('item_code')
    serializer_class = StockBalanceSerializer
    permission_classes = [permissions.AllowAny]


class StockReservationViewSet(viewsets.ModelViewSet):
    queryset = StockReservation.objects.all().order_by('-reserved_date')
    serializer_class = StockReservationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id') and not data.get('reservation_number') and not data.get('reservationNumber'):
            code = f"RES-2026-{StockReservation.objects.count() + 1:04d}"
            data['id'] = code
            data['reservation_number'] = code
        elif not data.get('id'):
            data['id'] = data.get('reservation_number') or data.get('reservationNumber')

        target_id = data.get('id')
        existing = StockReservation.objects.filter(id=target_id).first() if target_id else None
        if existing:
            serializer = self.get_serializer(existing, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            res = serializer.save()
            return Response(StockReservationSerializer(res).data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        res = serializer.save()
        return Response(StockReservationSerializer(res).data, status=status.HTTP_201_CREATED)


class MaterialIssueViewSet(viewsets.ModelViewSet):
    queryset = MaterialIssue.objects.all().order_by('-created_at', '-id')
    serializer_class = MaterialIssueSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id') and not data.get('issue_number') and not data.get('issueNumber'):
            code = f"ISSUE-2026-{MaterialIssue.objects.count() + 1:04d}"
            data['id'] = code
            data['issue_number'] = code
        elif not data.get('id'):
            data['id'] = data.get('issue_number') or data.get('issueNumber')

        if 'issue_number' not in data:
            data['issue_number'] = data.get('issueNumber') or data.get('id')
        if 'project_id' not in data:
            data['project_id'] = data.get('projectId') or 'PRJ-2026-0001'
        if 'job_number' not in data:
            data['job_number'] = data.get('jobId') or data.get('jobNumber') or data.get('job_number') or ''
        if 'work_order_id' not in data:
            data['work_order_id'] = data.get('workOrderNumber') or data.get('work_order_id') or data.get('workOrderId') or ''
        if 'bom_number' not in data:
            data['bom_number'] = data.get('bomNumber') or ''
        if 'bom_revision' not in data:
            data['bom_revision'] = data.get('bomRevision') or 'Rev-01'
        if 'production_stage' not in data:
            data['production_stage'] = data.get('productionStage') or data.get('stage') or ''
        if 'issued_to' not in data:
            data['issued_to'] = data.get('requestedBy') or data.get('issuedTo') or data.get('issued_to') or 'Production Head'
        if 'issued_by' not in data:
            data['issued_by'] = data.get('issuedBy') or data.get('issued_by') or 'Hitesh Rawal (Store Head)'
        if 'issue_date' not in data:
            data['issue_date'] = data.get('issueDate') or data.get('issue_date') or datetime.now().strftime('%Y-%m-%d')
        if 'warehouse_id' not in data:
            data['warehouse_id'] = data.get('warehouseId') or data.get('warehouse_id') or 'wh-main'
        if 'warehouse_name' not in data:
            data['warehouse_name'] = data.get('warehouseName') or data.get('warehouse_name') or 'Main Raw Material Warehouse'
        if 'total_issue_value' not in data:
            data['total_issue_value'] = data.get('totalIssueValue') or data.get('total_issue_value') or 0
        if 'notes' not in data:
            data['notes'] = data.get('remarks') or data.get('notes') or ''
        if 'status' not in data:
            data['status'] = data.get('status') or 'Fully Issued'

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        issue = serializer.save()

        # Deduct from Stock Balance and log outward in Stock Ledger
        raw_items = data.get('items') or getattr(issue, 'items', []) or []
        if isinstance(raw_items, str):
            try:
                import json
                raw_items = json.loads(raw_items)
            except Exception:
                raw_items = []
        if not isinstance(raw_items, list):
            raw_items = [raw_items]

        for itm in raw_items:
            if isinstance(itm, str):
                try:
                    import json
                    itm = json.loads(itm)
                except Exception:
                    itm = {}
            if not isinstance(itm, dict):
                continue
            item_code = itm.get('itemCode') or itm.get('item_code') or itm.get('itemId') or itm.get('item_id') or ''
            item_code_clean = str(item_code).strip()
            qty = float(itm.get('issuedQty') or itm.get('issued_qty') or itm.get('issuedQuantity') or itm.get('issued_quantity') or itm.get('quantity') or 0)
            rate = float(itm.get('unitPrice') or itm.get('unit_price') or itm.get('unitRate') or itm.get('unit_rate') or itm.get('standardCost') or itm.get('standard_cost') or 0)

            bal = StockBalance.objects.filter(item_code__iexact=item_code_clean).first() or \
                  StockBalance.objects.filter(id__iexact=item_code_clean).first() or \
                  StockBalance.objects.filter(item_id__iexact=item_code_clean).first()
            if not bal and item_code_clean:
                bal = StockBalance.objects.filter(item_code__icontains=item_code_clean).first() or \
                      StockBalance.objects.filter(id__icontains=item_code_clean).first()
            if not bal and itm.get('itemName'):
                bal = StockBalance.objects.filter(item_name__icontains=str(itm.get('itemName')).strip()).first()
            if bal:
                bal.quantity = max(0.0, float(bal.quantity) - qty)
                if getattr(bal, 'reserved_quantity', 0) > 0:
                    bal.reserved_quantity = max(0.0, float(bal.reserved_quantity) - qty)
                bal.available_quantity = max(0.0, float(bal.quantity) - float(bal.reserved_quantity or 0))
                bal.total_value = float(bal.quantity) * float(bal.unit_rate or rate)
                bal.save()

                ledg_id = f"ledg-{str(issue.issue_number).lower()}-{item_code_clean.lower()}-{int(datetime.now().timestamp())}"
                try:
                    StockLedgerEntry.objects.update_or_create(
                        id=ledg_id,
                        defaults={
                            'date': issue.issue_date,
                            'transaction_type': 'Material Issue',
                            'reference_number': issue.issue_number,
                            'item_id': bal.item_id or bal.id,
                            'item_code': bal.item_code or item_code_clean,
                            'item_name': bal.item_name,
                            'warehouse_id': issue.warehouse_id,
                            'inward_quantity': 0,
                            'outward_quantity': qty,
                            'closing_quantity': bal.quantity,
                            'unit_rate': bal.unit_rate or rate,
                            'total_amount': qty * (bal.unit_rate or rate),
                            'performed_by': issue.issued_to,
                        }
                    )
                except Exception:
                    pass

        if issue.job_number:
            try:
                from apps.projects.models import ProjectJobMaster, ProjectPlanningStage
                pjm = ProjectJobMaster.objects.filter(job_number=issue.job_number).first() or \
                      ProjectJobMaster.objects.filter(id=issue.job_number).first()
                if pjm:
                    pjm.current_status = 'in_progress'
                    pjm.stage = 'Shop Assembly & Fabrication'
                    if (pjm.progress_percent or 0) < 50:
                        pjm.progress_percent = 50
                    pjm.save()

                stages = ProjectPlanningStage.objects.filter(project_id=issue.project_id)
                for st in stages:
                    if any(w in st.name.lower() for w in ['material', 'procurement', 'store', 'inward']):
                        st.status = 'completed'
                        st.progress = 100
                        st.save()
            except Exception:
                pass

        return Response(MaterialIssueSerializer(issue).data, status=status.HTTP_201_CREATED)


class MaterialReturnViewSet(viewsets.ModelViewSet):
    queryset = MaterialReturn.objects.all().order_by('-created_at', '-id')
    serializer_class = MaterialReturnSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id') and not data.get('return_number') and not data.get('returnNumber'):
            code = f"RET-2026-{MaterialReturn.objects.count() + 1:04d}"
            data['id'] = code
            data['return_number'] = code
        elif not data.get('id'):
            data['id'] = data.get('return_number') or data.get('returnNumber')

        if 'return_number' not in data:
            data['return_number'] = data.get('returnNumber') or data.get('id')
        if 'project_id' not in data:
            data['project_id'] = data.get('projectId') or 'PRJ-2026-0001'
        if 'job_number' not in data:
            data['job_number'] = data.get('jobId') or data.get('jobNumber') or data.get('job_number') or ''
        if 'work_order_number' not in data:
            data['work_order_number'] = data.get('workOrderNumber') or data.get('work_order_number') or ''
        if 'material_issue_number' not in data:
            data['material_issue_number'] = data.get('materialIssueNumber') or data.get('issueNo') or data.get('material_issue_number') or ''
        if 'returned_by' not in data:
            data['returned_by'] = data.get('returnedBy') or data.get('returned_by') or 'Ketan Parmar (Shop Supervisor)'
        if 'received_by' not in data:
            data['received_by'] = data.get('receivedBy') or data.get('received_by') or 'Hitesh Rawal (Store Head)'
        if 'department' not in data:
            data['department'] = data.get('department') or 'Production'
        if 'return_date' not in data:
            data['return_date'] = data.get('returnDate') or data.get('return_date') or datetime.now().strftime('%Y-%m-%d')
        if 'warehouse_id' not in data:
            data['warehouse_id'] = data.get('warehouseId') or data.get('warehouse_id') or 'wh-main'
        if 'warehouse_name' not in data:
            data['warehouse_name'] = data.get('warehouseName') or data.get('warehouse_name') or 'Main Raw Material Warehouse'
        if 'total_return_value' not in data:
            data['total_return_value'] = data.get('totalReturnValue') or data.get('total_return_value') or 0
        if 'notes' not in data:
            data['notes'] = data.get('remarks') or data.get('notes') or ''
        if 'status' not in data:
            data['status'] = data.get('status') or 'Completed'

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        ret = serializer.save()

        # Inward usable returned material back into Stock Balance and log in Stock Ledger
        for itm in (ret.items or []):
            item_code = itm.get('itemCode') or itm.get('item_code')
            qty = float(itm.get('returnQty') or itm.get('returnQuantity') or itm.get('quantity', 0))
            rate = float(itm.get('unitPrice') or itm.get('unitRate') or itm.get('standardCost', 0))

            bal = StockBalance.objects.filter(item_code=item_code).first()
            if not bal:
                bal = StockBalance(
                    id=f"stk-{item_code.lower()}",
                    item_id=itm.get('itemId', item_code),
                    item_code=item_code,
                    item_name=itm.get('itemName', item_code),
                    warehouse_id=ret.warehouse_id,
                    warehouse_name=ret.warehouse_name,
                    quantity=0,
                    available_quantity=0,
                    unit_rate=rate,
                )
            bal.quantity += qty
            bal.available_quantity += qty
            bal.total_value = bal.quantity * (bal.unit_rate or rate)
            bal.save()

            StockLedgerEntry.objects.create(
                id=f"ledg-{ret.return_number.lower()}-{item_code.lower()}",
                date=ret.return_date,
                transaction_type='Material Return',
                reference_number=ret.return_number,
                item_id=bal.item_id,
                item_code=item_code,
                item_name=bal.item_name,
                warehouse_id=ret.warehouse_id,
                inward_quantity=qty,
                outward_quantity=0,
                closing_quantity=bal.quantity,
                unit_rate=bal.unit_rate or rate,
                total_amount=qty * (bal.unit_rate or rate),
                performed_by=ret.returned_by,
            )

        return Response(MaterialReturnSerializer(ret).data, status=status.HTTP_201_CREATED)


class StockLedgerEntryViewSet(viewsets.ModelViewSet):
    queryset = StockLedgerEntry.objects.all().order_by('-created_at')
    serializer_class = StockLedgerEntrySerializer
    permission_classes = [permissions.AllowAny]


class ScrapEntryViewSet(viewsets.ModelViewSet):
    queryset = ScrapEntry.objects.all().order_by('-date', '-id')
    serializer_class = ScrapEntrySerializer
    permission_classes = [permissions.AllowAny]


class StockTransferViewSet(viewsets.ModelViewSet):
    queryset = StockTransfer.objects.all().order_by('-created_at')
    serializer_class = StockTransferSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id') and not data.get('transfer_number') and not data.get('transferNumber'):
            code = f"TRN-2026-{StockTransfer.objects.count() + 1:04d}"
            data['id'] = code
            data['transfer_number'] = code
        elif not data.get('id'):
            data['id'] = data.get('transfer_number') or data.get('transferNumber')

        if 'transfer_number' not in data:
            data['transfer_number'] = data.get('transferNumber') or data.get('id')
        if 'transfer_date' not in data:
            data['transfer_date'] = data.get('transferDate') or datetime.now().strftime('%Y-%m-%d')
        if 'from_warehouse_id' not in data:
            data['from_warehouse_id'] = data.get('fromWarehouseId') or 'wh-main'
        if 'from_warehouse_name' not in data:
            data['from_warehouse_name'] = data.get('fromWarehouseName') or 'Main Raw Material Warehouse'
        if 'from_location_code' not in data:
            data['from_location_code'] = data.get('fromLocationCode') or ''
        if 'to_warehouse_id' not in data:
            data['to_warehouse_id'] = data.get('toWarehouseId') or 'wh-scrap'
        if 'to_warehouse_name' not in data:
            data['to_warehouse_name'] = data.get('toWarehouseName') or 'Scrap & Rejection Yard'
        if 'to_location_code' not in data:
            data['to_location_code'] = data.get('toLocationCode') or ''
        if 'reason' not in data:
            data['reason'] = data.get('reason') or ''
        if 'requested_by' not in data:
            data['requested_by'] = data.get('requestedBy') or 'Bhavin Shah (Production Manager)'
        if 'approved_by' not in data:
            data['approved_by'] = data.get('approvedBy') or 'Hitesh Rawal (Store Head)'
        if 'status' not in data:
            data['status'] = data.get('status') or 'Completed'

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        trn = serializer.save()

        # Update stock balances: deduct from source warehouse, add to destination warehouse
        for itm in (trn.items or []):
            item_code = itm.get('itemCode') or itm.get('item_code')
            qty = float(itm.get('quantity') or 0)
            if not item_code or qty <= 0:
                continue

            # Deduct from source
            src_bal = StockBalance.objects.filter(item_code=item_code, warehouse_id=trn.from_warehouse_id).first()
            if src_bal:
                src_bal.quantity = max(0, src_bal.quantity - qty)
                src_bal.available_quantity = max(0, src_bal.available_quantity - qty)
                src_bal.total_value = src_bal.quantity * (src_bal.unit_rate or 0)
                src_bal.save()

            # Add to destination
            dest_bal = StockBalance.objects.filter(item_code=item_code, warehouse_id=trn.to_warehouse_id).first()
            if not dest_bal:
                dest_bal = StockBalance(
                    id=f"stk-{item_code.lower()}-{trn.to_warehouse_id.lower()}",
                    item_id=itm.get('itemId', item_code),
                    item_code=item_code,
                    item_name=itm.get('itemName', item_code),
                    warehouse_id=trn.to_warehouse_id,
                    warehouse_name=trn.to_warehouse_name,
                    quantity=0,
                    available_quantity=0,
                    unit_rate=src_bal.unit_rate if src_bal else 0,
                )
            dest_bal.quantity += qty
            dest_bal.available_quantity += qty
            dest_bal.total_value = dest_bal.quantity * (dest_bal.unit_rate or 0)
            dest_bal.save()

            # Log in stock ledger
            StockLedgerEntry.objects.create(
                id=f"ledg-{trn.transfer_number.lower()}-{item_code.lower()}",
                date=trn.transfer_date,
                transaction_type='Stock Transfer',
                reference_number=trn.transfer_number,
                item_id=itm.get('itemId', item_code),
                item_code=item_code,
                item_name=itm.get('itemName', item_code),
                warehouse_id=trn.to_warehouse_id,
                inward_quantity=qty,
                outward_quantity=qty,
                closing_quantity=dest_bal.quantity,
                unit_rate=dest_bal.unit_rate,
                total_amount=qty * dest_bal.unit_rate,
                performed_by=trn.requested_by,
            )

        return Response(StockTransferSerializer(trn).data, status=status.HTTP_201_CREATED)


class StockAdjustmentViewSet(viewsets.ModelViewSet):
    queryset = StockAdjustment.objects.all().order_by('-created_at')
    serializer_class = StockAdjustmentSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id') and not data.get('adjustment_number') and not data.get('adjustmentNumber'):
            code = f"ADJ-2026-{StockAdjustment.objects.count() + 1:04d}"
            data['id'] = code
            data['adjustment_number'] = code
        elif not data.get('id'):
            data['id'] = data.get('adjustment_number') or data.get('adjustmentNumber')

        if 'adjustment_number' not in data:
            data['adjustment_number'] = data.get('adjustmentNumber') or data.get('id')
        if 'adjustment_date' not in data:
            data['adjustment_date'] = data.get('adjustmentDate') or datetime.now().strftime('%Y-%m-%d')
        if 'warehouse_id' not in data:
            data['warehouse_id'] = data.get('warehouseId') or 'wh-main'
        if 'warehouse_name' not in data:
            data['warehouse_name'] = data.get('warehouseName') or 'Main Raw Material Warehouse'
        if 'location_code' not in data:
            data['location_code'] = data.get('locationCode') or ''
        if 'item_id' not in data:
            data['item_id'] = data.get('itemId') or ''
        if 'item_code' not in data:
            data['item_code'] = data.get('itemCode') or ''
        if 'item_name' not in data:
            data['item_name'] = data.get('itemName') or ''
        if 'system_quantity' not in data:
            data['system_quantity'] = float(data.get('systemQuantity') or 0)
        if 'physical_quantity' not in data:
            data['physical_quantity'] = float(data.get('physicalQuantity') or 0)
        if 'difference_quantity' not in data:
            diff = float(data.get('differenceQuantity') if 'differenceQuantity' in data else (data['physical_quantity'] - data['system_quantity']))
            data['difference_quantity'] = diff
        if 'unit_price' not in data:
            data['unit_price'] = float(data.get('unitPrice') or 0)
        if 'adjustment_value' not in data:
            data['adjustment_value'] = float(data.get('adjustmentValue') or (data['difference_quantity'] * data['unit_price']))
        if 'reason' not in data:
            data['reason'] = data.get('reason') or 'Damaged Stock'
        if 'remarks' not in data:
            data['remarks'] = data.get('remarks') or ''
        if 'approved_by' not in data:
            data['approved_by'] = data.get('approvedBy') or 'Hitesh Rawal (Store Head)'
        if 'status' not in data:
            data['status'] = data.get('status') or 'Approved'

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        adj = serializer.save()

        # Update stock balance to match physical quantity
        item_code = adj.item_code
        if item_code:
            bal = StockBalance.objects.filter(item_code=item_code).first()
            if bal:
                bal.quantity = adj.physical_quantity
                bal.available_quantity = max(0, bal.quantity - bal.reserved_quantity)
                bal.total_value = bal.quantity * (bal.unit_rate or adj.unit_price)
                bal.save()

            # Record in stock ledger
            inward = adj.difference_quantity if adj.difference_quantity > 0 else 0
            outward = abs(adj.difference_quantity) if adj.difference_quantity < 0 else 0
            StockLedgerEntry.objects.create(
                id=f"ledg-{adj.adjustment_number.lower()}-{item_code.lower()}",
                date=adj.adjustment_date,
                transaction_type='Stock Adjustment',
                reference_number=adj.adjustment_number,
                item_id=adj.item_id,
                item_code=item_code,
                item_name=adj.item_name,
                warehouse_id=adj.warehouse_id,
                inward_quantity=inward,
                outward_quantity=outward,
                closing_quantity=adj.physical_quantity,
                unit_rate=adj.unit_price,
                total_amount=abs(adj.adjustment_value),
                performed_by=adj.approved_by,
            )

        return Response(StockAdjustmentSerializer(adj).data, status=status.HTTP_201_CREATED)

