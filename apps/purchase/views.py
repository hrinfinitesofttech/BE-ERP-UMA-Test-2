from datetime import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import (
    Supplier,
    SupplierContact,
    PurchaseRequisition,
    RequestForQuotation,
    SupplierQuotation,
    QuotationComparison,
    PurchaseOrder,
    PurchaseReturn,
    MaterialRequirement,
)
from .serializers import (
    SupplierSerializer,
    SupplierContactSerializer,
    PurchaseRequisitionSerializer,
    RequestForQuotationSerializer,
    SupplierQuotationSerializer,
    QuotationComparisonSerializer,
    PurchaseOrderSerializer,
    PurchaseReturnSerializer,
    MaterialRequirementSerializer,
)


class MaterialRequirementViewSet(viewsets.ModelViewSet):
    queryset = MaterialRequirement.objects.all().order_by('-created_at')
    serializer_class = MaterialRequirementSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            data['id'] = f"MRP-REQ-{MaterialRequirement.objects.count() + 1:05d}"
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by('name')
    serializer_class = SupplierSerializer
    permission_classes = [permissions.AllowAny]


class SupplierContactViewSet(viewsets.ModelViewSet):
    queryset = SupplierContact.objects.all().order_by('name')
    serializer_class = SupplierContactSerializer
    permission_classes = [permissions.AllowAny]


class PurchaseRequisitionViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequisition.objects.all().order_by('-request_date')
    serializer_class = PurchaseRequisitionSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        pr_num = data.get('prNumber') or data.get('pr_number') or data.get('id') or f"PR-2026-{PurchaseRequisition.objects.count() + 1:04d}"
        pr_id = data.get('id') or pr_num

        pr_obj, _ = PurchaseRequisition.objects.update_or_create(
            id=pr_id,
            defaults={
                'pr_number': pr_num,
                'project_id': data.get('projectId') or data.get('project_id', '') or 'PRJ-2026-0001',
                'job_code': data.get('jobId') or data.get('jobNumber') or data.get('job_code', '') or 'JOB-2026-001',
                'requested_by': data.get('requestedBy') or data.get('requested_by') or 'Purchase Admin',
                'department': data.get('department') or 'Purchase / Planning',
                'request_date': data.get('requisitionDate') or data.get('prDate') or data.get('request_date') or datetime.now().strftime('%Y-%m-%d'),
                'required_by_date': data.get('requiredByDate') or data.get('required_by_date') or data.get('requiredDate') or '2026-12-31',
                'priority': data.get('priority') or 'High',
                'status': data.get('status') or 'Submitted',
                'items': data.get('items') if isinstance(data.get('items'), list) else [],
                'total_estimated_cost': float(data.get('estimatedCost') or data.get('total_estimated_cost') or 0),
                'remarks': data.get('remarks', ''),
                'approved_by': data.get('approvedBy') or data.get('approved_by'),
            }
        )
        return Response(PurchaseRequisitionSerializer(pr_obj).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='convert-to-rfq')
    def convert_to_rfq(self, request, pk=None):
        pr = self.get_object()
        rfq_code = f"RFQ-2026-{RequestForQuotation.objects.count() + 1:04d}"
        rfq = RequestForQuotation.objects.create(
            id=rfq_code,
            rfq_number=rfq_code,
            pr_id=pr.id,
            rfq_date=datetime.now().strftime('%Y-%m-%d'),
            due_date=request.data.get('dueDate') or request.data.get('due_date', ''),
            suppliers=request.data.get('suppliers', []),
            items=pr.items,
            status='sent',
            terms_and_conditions='Payment terms: 30 days. Delivery: Vadodara Makarpura unit.',
        )
        pr.status = 'converted_to_rfq'
        pr.save(update_fields=['status'])
        return Response(RequestForQuotationSerializer(rfq).data, status=status.HTTP_201_CREATED)


class RequestForQuotationViewSet(viewsets.ModelViewSet):
    queryset = RequestForQuotation.objects.all().order_by('-rfq_date')
    serializer_class = RequestForQuotationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            rfq_num = data.get('rfqNumber') or data.get('rfq_number') or f"RFQ-2026-{RequestForQuotation.objects.count() + 1:04d}"
            data['id'] = rfq_num
            data['rfq_number'] = rfq_num
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupplierQuotationViewSet(viewsets.ModelViewSet):
    queryset = SupplierQuotation.objects.all().order_by('-date')
    serializer_class = SupplierQuotationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            sq_num = data.get('quotationNumber') or data.get('quotation_number') or f"SQ-2026-{SupplierQuotation.objects.count() + 1:04d}"
            data['id'] = sq_num
            data['quotation_number'] = sq_num
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuotationComparisonViewSet(viewsets.ModelViewSet):
    queryset = QuotationComparison.objects.all().order_by('-comparison_date')
    serializer_class = QuotationComparisonSerializer
    permission_classes = [permissions.AllowAny]


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all().order_by('-date')
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id') or not data.get('po_number') and not data.get('poNumber'):
            code = f"PO-2026-{PurchaseOrder.objects.count() + 1:04d}"
            data['id'] = code
            data['po_number'] = code
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_po(self, request, pk=None):
        po = self.get_object()
        po.status = 'approved'
        po.approved_by = request.data.get('approvedBy') or request.data.get('approved_by', 'Rajesh Patel')
        po.save(update_fields=['status', 'approved_by'])
        return Response(PurchaseOrderSerializer(po).data)


class PurchaseReturnViewSet(viewsets.ModelViewSet):
    queryset = PurchaseReturn.objects.all().order_by('-date')
    serializer_class = PurchaseReturnSerializer
    permission_classes = [permissions.AllowAny]
