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
)


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
        data = request.data.copy()
        pr_num = data.get('prNumber') or data.get('pr_number') or f"PR-2026-{PurchaseRequisition.objects.count() + 1:04d}"
        data['id'] = data.get('id') or pr_num
        data['pr_number'] = pr_num
        data['project_id'] = data.get('projectId') or data.get('project_id', '')
        data['job_code'] = data.get('jobId') or data.get('jobNumber') or data.get('job_code', '')
        data['requested_by'] = data.get('requestedBy') or data.get('requested_by') or 'Purchase Admin'
        data['department'] = data.get('department') or 'Purchase / Planning'
        data['request_date'] = data.get('requisitionDate') or data.get('prDate') or data.get('request_date') or datetime.now().strftime('%Y-%m-%d')
        data['required_by_date'] = data.get('requiredByDate') or data.get('required_by_date') or '2026-12-31'
        data['priority'] = data.get('priority') or 'High'
        data['status'] = data.get('status') or 'Submitted'
        data['items'] = data.get('items') or []
        data['total_estimated_cost'] = float(data.get('estimatedCost') or data.get('total_estimated_cost') or 0)
        data['remarks'] = data.get('remarks', '')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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


class SupplierQuotationViewSet(viewsets.ModelViewSet):
    queryset = SupplierQuotation.objects.all().order_by('-date')
    serializer_class = SupplierQuotationSerializer
    permission_classes = [permissions.AllowAny]


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
