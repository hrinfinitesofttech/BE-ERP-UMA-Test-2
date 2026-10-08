from datetime import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.core.approval_security import (
    validate_approval_permission,
    validate_approval_transition,
    validate_edit_safety,
    log_approval_audit,
)


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


from django.db.models import Q
from django.http import Http404


class PurchaseRequisitionViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequisition.objects.all().order_by('-created_at', '-id')
    serializer_class = PurchaseRequisitionSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        pk = self.kwargs.get('pk')
        obj = PurchaseRequisition.objects.filter(Q(id=pk) | Q(pr_number=pk)).first()
        if not obj:
            raise Http404(f"Purchase Requisition '{pk}' not found")
        return obj

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

    def update(self, request, *args, **kwargs):
        pr = self.get_object()
        safe, err_resp = validate_edit_safety(pr, request.data)
        if not safe:
            return err_resp
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'status' in data:
            pr.status = data['status']
        if 'approvedBy' in data or 'approved_by' in data:
            pr.approved_by = data.get('approvedBy') or data.get('approved_by')
        if 'remarks' in data:
            pr.remarks = data['remarks']
        if 'priority' in data:
            pr.priority = data['priority']
        if 'items' in data and isinstance(data['items'], list):
            pr.items = data['items']
        if 'estimatedCost' in data or 'total_estimated_cost' in data:
            pr.total_estimated_cost = float(data.get('estimatedCost') or data.get('total_estimated_cost') or pr.total_estimated_cost)
        pr.save()
        return Response(PurchaseRequisitionSerializer(pr).data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post', 'patch'], url_path='approve')
    def approve(self, request, pk=None):
        pr = self.get_object()
        
        # 1. Authorization check
        allowed, err_resp, user_info = validate_approval_permission(
            request,
            allowed_departments=['Purchase', 'Procurement', 'Stores', 'Production', 'Planning', 'Management'],
            allowed_roles=['Purchase Manager', 'Store Manager', 'Production Manager', 'Manager', 'Director', 'Admin']
        )
        if not allowed:
            return err_resp

        # 2. Transition guard
        valid_trans, trans_resp = validate_approval_transition(pr.status, 'approve')
        if not valid_trans:
            return trans_resp

        approver = user_info['name'] or request.data.get('approvedBy') or request.data.get('approved_by') or 'Purchase Admin'
        notes = request.data.get('comment') or request.data.get('approvalNotes') or 'Requisition approved'

        pr.status = 'Approved'
        pr.approved_by = approver
        if notes:
            pr.remarks = f"{pr.remarks} | Approved: {notes}".strip(' |')
        pr.save()

        log_approval_audit(user_info, 'APPROVE', 'Purchase', 'PurchaseRequisition', pr.id, notes)
        return Response(PurchaseRequisitionSerializer(pr).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'patch'], url_path='reject')
    def reject(self, request, pk=None):
        pr = self.get_object()
        
        # 1. Authorization check
        allowed, err_resp, user_info = validate_approval_permission(
            request,
            allowed_departments=['Purchase', 'Procurement', 'Stores', 'Production', 'Planning', 'Management'],
            allowed_roles=['Purchase Manager', 'Store Manager', 'Production Manager', 'Manager', 'Director', 'Admin']
        )
        if not allowed:
            return err_resp

        # 2. Transition guard
        valid_trans, trans_resp = validate_approval_transition(pr.status, 'reject')
        if not valid_trans:
            return trans_resp

        reason = request.data.get('reason') or request.data.get('rejectionReason') or request.data.get('remarks') or 'Requisition rejected'
        pr.status = 'Rejected'
        pr.remarks = f"{pr.remarks} | Rejected: {reason}".strip(' |')
        pr.save()

        log_approval_audit(user_info, 'REJECT', 'Purchase', 'PurchaseRequisition', pr.id, reason)
        return Response(PurchaseRequisitionSerializer(pr).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'patch'], url_path='disapprove')
    def disapprove(self, request, pk=None):
        return self.reject(request, pk=pk)


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
    queryset = RequestForQuotation.objects.all().order_by('-created_at', '-id')
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
    queryset = SupplierQuotation.objects.all().order_by('-created_at', '-id')
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
    queryset = QuotationComparison.objects.all().order_by('-created_at', '-id')
    serializer_class = QuotationComparisonSerializer
    permission_classes = [permissions.AllowAny]


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all().order_by('-created_at', '-id')
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        pk = self.kwargs.get('pk')
        obj = PurchaseOrder.objects.filter(Q(id=pk) | Q(po_number=pk)).first()
        if not obj:
            raise Http404(f"Purchase Order '{pk}' not found")
        return obj

    def create(self, request, *args, **kwargs):
        import threading
        if not hasattr(self.__class__, '_create_lock'):
            self.__class__._create_lock = threading.Lock()

        with self.__class__._create_lock:
            data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            po_num = data.get('poNumber') or data.get('po_number') or data.get('id')
            if not po_num:
                count = PurchaseOrder.objects.count() + 1
                po_num = f"PO-2026-{count:04d}"
                while PurchaseOrder.objects.filter(Q(id=po_num) | Q(po_number=po_num)).exists():
                    count += 1
                    po_num = f"PO-2026-{count:04d}"
            po_id = data.get('id') or po_num
            data['id'] = po_id
            data['po_number'] = po_num

            existing = PurchaseOrder.objects.filter(Q(id=po_id) | Q(po_number=po_num)).first()
            if existing:
                serializer = self.get_serializer(existing, data=data, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data, status=status.HTTP_200_OK)

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        safe, err_resp = validate_edit_safety(instance, request.data)
        if not safe:
            return err_resp
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post', 'patch'], url_path='approve')
    def approve_po(self, request, pk=None):
        po = self.get_object()
        
        # 1. Authorization check
        allowed, err_resp, user_info = validate_approval_permission(
            request,
            allowed_departments=['Purchase', 'Procurement', 'Management'],
            allowed_roles=['Purchase Manager', 'Manager', 'Director', 'Admin']
        )
        if not allowed:
            return err_resp

        # 2. Transition guard
        valid_trans, trans_resp = validate_approval_transition(po.status, 'approve')
        if not valid_trans:
            return trans_resp

        approver = user_info['name'] or request.data.get('approvedBy') or request.data.get('approved_by') or 'Purchase Manager'
        comment = request.data.get('comment') or request.data.get('approvalNotes') or 'PO Approved'

        po.status = 'Approved'
        po.approved_by = approver
        if comment:
            po.remarks = f"{po.remarks} | Approved: {comment}".strip(' |')
        po.save(update_fields=['status', 'approved_by', 'remarks'])

        log_approval_audit(user_info, 'APPROVE', 'Purchase', 'PurchaseOrder', po.id, comment)
        return Response(PurchaseOrderSerializer(po).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'patch'], url_path='reject')
    def reject_po(self, request, pk=None):
        po = self.get_object()
        
        # 1. Authorization check
        allowed, err_resp, user_info = validate_approval_permission(
            request,
            allowed_departments=['Purchase', 'Procurement', 'Management'],
            allowed_roles=['Purchase Manager', 'Manager', 'Director', 'Admin']
        )
        if not allowed:
            return err_resp

        # 2. Transition guard
        valid_trans, trans_resp = validate_approval_transition(po.status, 'reject')
        if not valid_trans:
            return trans_resp

        reason = request.data.get('reason') or request.data.get('rejectionReason') or request.data.get('remarks') or 'PO Rejected'
        po.status = 'Rejected'
        if reason:
            po.remarks = f"{po.remarks} | Rejected: {reason}".strip(' |')
        po.save(update_fields=['status', 'remarks'])

        log_approval_audit(user_info, 'REJECT', 'Purchase', 'PurchaseOrder', po.id, reason)
        return Response(PurchaseOrderSerializer(po).data, status=status.HTTP_200_OK)



class PurchaseReturnViewSet(viewsets.ModelViewSet):
    queryset = PurchaseReturn.objects.all().order_by('-created_at', '-id')
    serializer_class = PurchaseReturnSerializer
    permission_classes = [permissions.AllowAny]
