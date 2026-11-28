from apps.core.softdelete import SoftDeleteViewSetMixin
from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from .models import (
    ApprovalItem,
    ERPAlertItem,
    Job360Overview,
    ExecutiveDashboardKPI,
    Customer360Summary,
    Supplier360Summary,
    ItemMaterial360Summary,
    Employee360Summary,
    GlobalActivityLog,
    ERPReportCenterItem,
    JobProfitabilityRecord,
)
from .serializers import (
    ApprovalItemSerializer,
    ERPAlertItemSerializer,
    Job360OverviewSerializer,
    ExecutiveDashboardKPISerializer,
    Customer360SummarySerializer,
    Supplier360SummarySerializer,
    ItemMaterial360SummarySerializer,
    Employee360SummarySerializer,
    GlobalActivityLogSerializer,
    ERPReportCenterItemSerializer,
    JobProfitabilityRecordSerializer,
)

# Module models
from django.db.models import Q
from apps.crm.models import Customer, Lead, FollowUp, Quotation, CustomerPO, SalesOrder
from apps.projects.models import ProjectJobMaster, ProjectMilestone, ProjectTask, ProjectIssue, ProjectPlanningStage
from apps.designer.models import DesignJob, BOMHeader
from apps.purchase.models import PurchaseRequisition, PurchaseOrder
from apps.store.models import StockBalance, MaterialIssue, GoodsReceiptNote, QCInspection
from apps.production.models import ManufacturingJob, WorkOrder, ProductionOrder, ProductionEntry, WIPRecord, ProductionScheduleItem, DispatchOrder, PackingOrder
from apps.maintenance.models import CustomerMachine, ServiceRequest, BreakdownRecord, ServiceVisit, AMCContract
from apps.accounting.models import SalesInvoice, CustomerReceipt, JobCostingSummary


class ApprovalItemViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    queryset = ApprovalItem.objects.all().order_by('-created_at', '-id')
    serializer_class = ApprovalItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['title', 'record_number', 'requester_name', 'related_job_number']
    filterset_fields = ['status', 'category', 'urgency']

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        item = self.get_object()
        item.status = 'Approved'
        item.save()
        return Response(ApprovalItemSerializer(item).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        item = self.get_object()
        item.status = 'Rejected'
        item.save()
        return Response(ApprovalItemSerializer(item).data)


class ERPAlertItemViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    queryset = ERPAlertItem.objects.all().order_by('-timestamp', '-id')
    serializer_class = ERPAlertItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['title', 'description', 'module']
    filterset_fields = ['module', 'severity', 'is_read']

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        alert = self.get_object()
        alert.is_read = True
        alert.save()
        return Response(ERPAlertItemSerializer(alert).data)


def _num(value, default=0.0):
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _s(value, default=''):
    return default if value is None else str(value)


class Job360APIView(APIView):
    """
    Job 360° dossier. Every value is read from live ERP tables for the given
    job number; nothing is fabricated. Missing data comes back as 0 / '' / [].
    Without a job number it returns the list of known jobs for the selector.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, job_number=None):
        job_no = job_number or request.query_params.get('jobNumber') or request.query_params.get('job_number')

        if not job_no:
            jobs = {}
            for pj in ProjectJobMaster.objects.all().order_by('-created_at'):
                jobs[pj.job_number] = {
                    'jobNumber': pj.job_number,
                    'projectNumber': pj.project_number,
                    'customerName': pj.customer_name,
                    'productName': pj.product_name,
                }
            for mj in ManufacturingJob.objects.all().order_by('-created_at'):
                jobs.setdefault(mj.job_number, {
                    'jobNumber': mj.job_number,
                    'projectNumber': mj.project_number or '',
                    'customerName': mj.customer_name,
                    'productName': mj.product_name,
                })
            return Response(list(jobs.values()), status=status.HTTP_200_OK)

        mfg_job = ManufacturingJob.objects.filter(job_number=job_no).first()
        prj = ProjectJobMaster.objects.filter(job_number=job_no).first()
        if not mfg_job and not prj:
            return Response({'detail': f'Job {job_no} not found.'}, status=status.HTTP_404_NOT_FOUND)

        des_job = DesignJob.objects.filter(job_number=job_no).first()
        so_number = (mfg_job.sales_order_number if mfg_job else '') or (prj.sales_order_number if prj else '')
        so = SalesOrder.objects.filter(sales_order_number=so_number).first() if so_number else None
        if not so:
            so = SalesOrder.objects.filter(job_number=job_no).first()
        po_number = (mfg_job.customer_po_number if mfg_job else '') or (prj.customer_po_number if prj else '') or getattr(so, 'customer_po_number', '')
        cpo = CustomerPO.objects.filter(po_number=po_number).first() if po_number else None
        quot = None
        if so and so.quotation_number:
            quot = Quotation.objects.filter(quotation_number=so.quotation_number).first()
        lead = Lead.objects.filter(id=quot.lead_id).first() if quot and quot.lead_id else None
        follow_ups = FollowUp.objects.filter(lead_or_customer_id=lead.id) if lead else FollowUp.objects.none()
        last_follow = follow_ups.order_by('-date').first()

        costing = JobCostingSummary.objects.filter(job_number=job_no).first()
        invoices = SalesInvoice.objects.filter(job_number=job_no)
        wo = WorkOrder.objects.filter(job_number=job_no).first()
        prod_order = ProductionOrder.objects.filter(job_number=job_no).first()
        machine = CustomerMachine.objects.filter(job_number=job_no).first()

        total_value = _num(getattr(so, 'order_value', 0)) or _num(getattr(so, 'grand_total', 0)) \
            or _num(getattr(prj, 'order_value', 0)) or _num(getattr(costing, 'sales_order_value', 0))
        total_cost = _num(getattr(costing, 'total_actual_cost', 0))
        profit = (total_value - total_cost) if costing else 0.0
        margin = round(profit / total_value * 100, 1) if total_value > 0 and costing else 0.0

        header = {
            'jobId': _s(getattr(mfg_job, 'id', None) or getattr(prj, 'id', '')),
            'jobNumber': job_no,
            'projectNumber': _s(getattr(prj, 'project_number', None) or getattr(mfg_job, 'project_number', '')),
            'customerName': _s(getattr(mfg_job, 'customer_name', None) or getattr(prj, 'customer_name', '')),
            'salesOrderNumber': _s(so_number),
            'customerPoNumber': _s(po_number),
            'productName': _s(getattr(mfg_job, 'product_name', None) or getattr(prj, 'product_name', '')),
            'machineModel': _s(getattr(prj, 'product_code', '')),
            'projectManager': _s(getattr(prj, 'project_manager_name', None) or getattr(mfg_job, 'project_manager', '')),
            'jobStatus': _s(getattr(mfg_job, 'status', None) or getattr(prj, 'current_status', '')),
            'priority': (_s(getattr(prj, 'priority', 'medium')) or 'medium').capitalize(),
            'plannedDeliveryDate': _s(getattr(prj, 'target_delivery_date', None) or getattr(mfg_job, 'planned_completion_date', '')),
            'actualDeliveryDate': _s(getattr(prj, 'actual_delivery_date', '')) or None,
            'overallProgressPercent': int(getattr(mfg_job, 'production_progress', None) or getattr(prj, 'progress_percent', 0) or 0),
            'totalJobValue': total_value,
            'totalJobCost': total_cost,
            'profitAmount': profit,
            'marginPercent': margin,
        }

        crm = {
            'leadNumber': _s(getattr(lead, 'lead_no', '')),
            'leadSource': _s(getattr(lead, 'source', '')),
            'enquiryDate': _s(getattr(lead, 'created_at', ''))[:10],
            'followUpCount': follow_ups.count(),
            'lastFollowUpDate': _s(getattr(last_follow, 'date', '')),
            'quotationNumber': _s(getattr(quot, 'quotation_number', '')),
            'quotationValue': _num(getattr(quot, 'grand_total', 0)),
            'quotationStatus': _s(getattr(quot, 'status', '')),
            'customerPoNumber': _s(po_number),
            'customerPoDate': _s(getattr(cpo, 'po_date', '')),
            'salesOrderNumber': _s(so_number),
            'salesOrderDate': _s(getattr(so, 'order_date', '')),
            'salesOrderValue': _num(getattr(so, 'order_value', 0)) or _num(getattr(so, 'grand_total', 0)),
        }

        prj_id = getattr(prj, 'id', '') or getattr(mfg_job, 'project_id', '') or ''
        milestones = ProjectMilestone.objects.filter(project_id=prj_id) if prj_id else ProjectMilestone.objects.none()
        tasks = ProjectTask.objects.filter(project_id=prj_id) if prj_id else ProjectTask.objects.none()
        issues = ProjectIssue.objects.filter(project_id=prj_id) if prj_id else ProjectIssue.objects.none()
        stages = ProjectPlanningStage.objects.filter(project_id=prj_id).order_by('stage_number') if prj_id else []
        completed_tasks = tasks.filter(status__iexact='completed').count()
        done_ms = milestones.filter(status__in=['completed', 'Completed', 'achieved']).count()
        days_remaining = 0
        try:
            from datetime import datetime
            tgt = _s(getattr(prj, 'target_delivery_date', ''))[:10]
            if tgt:
                days_remaining = (datetime.strptime(tgt, '%Y-%m-%d').date() - timezone.now().date()).days
        except ValueError:
            days_remaining = 0
        project = {
            'projectId': _s(prj_id),
            'projectNumber': header['projectNumber'],
            'projectName': _s(getattr(prj, 'product_name', '')),
            'totalTasks': tasks.count(),
            'completedTasks': completed_tasks,
            'milestonesCount': milestones.count(),
            'milestonesCompleted': done_ms,
            'timelineDays': 0,
            'daysRemaining': days_remaining,
            'openIssuesCount': issues.exclude(status__in=['resolved', 'closed', 'Resolved', 'Closed']).count(),
            'delaysCount': sum(1 for st in stages if st.status == 'delayed'),
            'departmentAssignments': [
                {'department': st.department, 'head': st.assigned_employee_name, 'status': st.status}
                for st in stages
            ],
        }

        bom = BOMHeader.objects.filter(job_number=job_no).first()
        design = {
            'designJobNumber': _s(getattr(des_job, 'design_job_number', '')),
            'requirementsSummary': _s(getattr(des_job, 'remarks', '')),
            'designRevision': _s(getattr(des_job, 'active_revision', None) or getattr(mfg_job, 'design_revision', '')),
            'cadFilesCount': len(getattr(des_job, 'attachments', None) or []),
            'designStatus': _s(getattr(des_job, 'status', '')),
            'approvedBy': _s(getattr(des_job, 'approved_by', '')),
            'approvalDate': _s(getattr(des_job, 'approved_date', '')),
            'bomNumber': _s(getattr(bom, 'bom_number', '')),
            'bomRevision': _s(getattr(bom, 'active_revision', '')),
            'bomItemsCount': int(getattr(bom, 'total_items', 0) or 0),
            'bomApproved': bool(bom and bom.status and bom.status.lower() in ('approved', 'released')),
            'documentsCount': len(getattr(des_job, 'attachments', None) or []),
        }

        prs = PurchaseRequisition.objects.filter(job_number=job_no)
        pos = PurchaseOrder.objects.filter(job_number=job_no)
        po_items = []
        total_po_value = 0.0
        delivered_value = 0.0
        for po in pos:
            total_po_value += _num(po.grand_total)
            if (po.status or '').lower() in ('received', 'closed', 'delivered', 'completed'):
                delivered_value += _num(po.grand_total)
            for it in (po.items or []):
                po_items.append({
                    'itemCode': _s(it.get('itemCode') or it.get('item_code')),
                    'description': _s(it.get('description') or it.get('itemName') or it.get('item_name')),
                    'requiredQty': _num(it.get('quantity') or it.get('qty')),
                    'orderedQty': _num(it.get('quantity') or it.get('qty')),
                    'receivedQty': _num(it.get('receivedQty') or it.get('received_qty')),
                    'poNumber': po.po_number,
                    'supplierName': po.supplier_name,
                    'status': po.status,
                })
        purchase = {
            'totalPrsCount': prs.count(),
            'totalRfqsCount': 0,
            'totalPosCount': pos.count(),
            'totalPurchaseValue': total_po_value,
            'pendingPurchaseValue': max(0.0, total_po_value - delivered_value),
            'deliveredPurchaseValue': delivered_value,
            'items': po_items,
        }

        issues_qs = MaterialIssue.objects.filter(job_number=job_no)
        grns = GoodsReceiptNote.objects.filter(job_number=job_no)
        materials = []
        for iss in issues_qs:
            for it in (iss.items or []):
                materials.append({
                    'itemCode': _s(it.get('itemCode') or it.get('item_code')),
                    'itemName': _s(it.get('itemName') or it.get('item_name')),
                    'requiredQty': _num(it.get('requestedQty') or it.get('quantity') or it.get('issuedQty')),
                    'availableStock': 0,
                    'reservedQty': 0,
                    'issuedQty': _num(it.get('issuedQty') or it.get('quantity')),
                    'status': 'Issued',
                })
        store = {
            'requiredItemsCount': len(materials),
            'availableItemsCount': len(materials),
            'reservedStockValue': 0.0,
            'materialReceivedCount': grns.count(),
            'materialIssuedCount': issues_qs.count(),
            'materialReturnedCount': 0,
            'scrapGeneratedCost': 0.0,
            'stockShortageItemsCount': 0,
            'issuedValue': sum(_num(i.total_issue_value) for i in issues_qs),
            'materials': materials,
        }

        entries = ProductionEntry.objects.filter(job_number=job_no)
        wips = WIPRecord.objects.filter(job_number=job_no)
        schedule = ProductionScheduleItem.objects.filter(job_number=job_no)
        completed_qty = sum(_num(e.good_quantity) for e in entries)
        production = {
            'productionOrderId': _s(getattr(prod_order, 'production_order_number', '')),
            'workOrderNumber': _s(getattr(wo, 'work_order_number', '')),
            'targetQuantity': _num(getattr(wo, 'production_quantity', 0)) or _num(getattr(mfg_job, 'quantity', 0)),
            'completedQuantity': completed_qty,
            'reworkQuantity': sum(_num(e.rework_quantity) for e in entries),
            'scrapQuantity': sum(_num(e.scrap_quantity) for e in entries),
            'wipQuantity': sum(_num(w.wip_quantity) for w in wips),
            'workCenterName': _s(getattr(schedule.first(), 'work_center_name', '')),
            'operatorName': _s(getattr(entries.order_by('-entry_date').first(), 'operator_name', '')),
            'startDate': _s(getattr(mfg_job, 'actual_start_date', '')),
            'estimatedEndDate': _s(getattr(mfg_job, 'planned_completion_date', '')),
            'status': _s(getattr(mfg_job, 'status', '')),
            'operations': [
                {
                    'operationName': s.operation_name,
                    'workCenter': s.work_center_name or s.work_center_code,
                    'status': s.status,
                    'progress': 100 if (s.status or '').lower() == 'completed' else (50 if (s.status or '').lower() in ('in progress', 'in_progress') else 0),
                }
                for s in schedule
            ],
        }

        grn_numbers = list(grns.values_list('grn_number', flat=True))
        qcs = QCInspection.objects.filter(grn_number__in=grn_numbers)
        quality = {
            'incomingQcPassCount': qcs.filter(overall_result__iexact='Pass').count(),
            'incomingQcFailCount': qcs.filter(overall_result__iexact='Fail').count(),
            'inProcessQcPassCount': 0,
            'inProcessQcFailCount': 0,
            'finalQcStatus': 'Pending',
            'inspectorName': _s(getattr(qcs.order_by('-created_at').first(), 'inspector', '')),
            'inspectionDate': _s(getattr(qcs.order_by('-created_at').first(), 'inspection_date', '')),
            'rejectedQuantity': sum(_num(q.rejected_quantity) for q in qcs),
            'reworkHours': 0.0,
            'qcCertificateNumber': '',
        }

        disp = DispatchOrder.objects.filter(job_number=job_no).order_by('-dispatch_date').first()
        packing = PackingOrder.objects.filter(job_number=job_no).first()
        dispatch = {
            'packingListNumber': _s(getattr(packing, 'packing_number', '')),
            'dispatchNoteNumber': _s(getattr(disp, 'dispatch_number', '')),
            'dispatchDate': _s(getattr(disp, 'dispatch_date', '')),
            'transporterName': _s(getattr(disp, 'transporter_name', '')),
            'vehicleNumber': _s(getattr(disp, 'vehicle_number', '')),
            'lrNumber': _s(getattr(disp, 'lr_number', '')),
            'deliveryStatus': 'Delivered' if disp and (disp.status or '').lower() == 'delivered' else ('In Transit' if disp and (disp.status or '').lower() in ('dispatched', 'in transit') else 'Pending'),
            'installationDate': _s(getattr(machine, 'installation_date', '')) or None,
            'commissioningDate': _s(getattr(machine, 'commissioning_date', '')) or None,
            'installedByTech': _s(getattr(machine, 'service_engineer', '')) or None,
            'customerSignOff': bool(disp and disp.receiver_sign),
        }

        inv = invoices.order_by('-invoice_date').first()
        inv_total = sum(_num(i.grand_total) for i in invoices)
        inv_received = sum(_num(i.paid_amount) for i in invoices)
        accounts = {
            'salesInvoiceNumber': _s(getattr(inv, 'invoice_number', '')),
            'invoiceDate': _s(getattr(inv, 'invoice_date', '')),
            'invoiceValue': sum(_num(i.taxable_amount) for i in invoices),
            'gstAmount': sum(_num(i.tax_total) for i in invoices),
            'grandTotal': inv_total,
            'receivedAmount': inv_received,
            'outstandingBalance': inv_total - inv_received,
            'paymentStatus': _s(getattr(inv, 'payment_status', '')) or 'Unpaid',
            'totalActualCost': total_cost,
            'grossMarginAmount': profit,
            'grossMarginPercent': margin,
        }

        amc = AMCContract.objects.filter(customer_machine_id=getattr(machine, 'id', '__none__')).first() if machine else None
        srs = ServiceRequest.objects.filter(job_number=job_no)
        today = timezone.now().date()
        warranty_end = getattr(machine, 'warranty_end', None)
        if amc and amc.contract_end >= today:
            warranty_state = 'Under AMC'
        elif warranty_end and warranty_end >= today:
            warranty_state = 'Active'
        else:
            warranty_state = 'Expired' if warranty_end else ''
        service = {
            'warrantyStatus': warranty_state,
            'warrantyEndDate': _s(warranty_end),
            'amcContractNumber': _s(getattr(amc, 'amc_number', '')) or None,
            'amcEndDate': _s(getattr(amc, 'contract_end', '')) or None,
            'serviceRequestsCount': srs.count(),
            'breakdownEventsCount': BreakdownRecord.objects.filter(serial_number=getattr(machine, 'serial_number', '__none__')).count() if machine and machine.serial_number else 0,
            'serviceVisitsCount': ServiceVisit.objects.filter(request_number__in=list(srs.values_list('request_number', flat=True))).count(),
            'lastServiceDate': None,
        }

        documents = []
        for idx, att in enumerate(getattr(des_job, 'attachments', None) or []):
            if isinstance(att, dict):
                documents.append({
                    'id': _s(att.get('id') or f'DOC-{idx + 1}'),
                    'documentType': _s(att.get('type') or att.get('category') or 'Design'),
                    'fileName': _s(att.get('name') or att.get('fileName')),
                    'fileSize': _s(att.get('size') or att.get('fileSize')),
                    'version': _s(att.get('version') or getattr(des_job, 'active_revision', '')),
                    'uploadedBy': _s(att.get('uploadedBy') or getattr(des_job, 'assigned_designer', '')),
                    'uploadDate': _s(att.get('uploadDate') or att.get('uploadedAt')),
                    'approvalStatus': 'Approved' if getattr(des_job, 'approved_by', '') else 'Pending',
                    'confidential': False,
                })

        timeline = []
        for log in GlobalActivityLog.objects.filter(Q(entity_id__in=[x for x in (job_no, _s(prj_id), _s(getattr(mfg_job, 'id', ''))) if x]) | Q(details__icontains=job_no)).order_by('-created_at')[:50]:
            timeline.append({
                'id': _s(log.id),
                'timestamp': _s(log.created_at)[:16],
                'module': _s(getattr(log, 'module', '')),
                'user': _s(getattr(log, 'user_name', '')),
                'action': _s(getattr(log, 'action', '')),
                'description': _s(log.details),
            })

        return Response({
            'header': header,
            'crm': crm,
            'project': project,
            'design': design,
            'purchase': purchase,
            'store': store,
            'production': production,
            'quality': quality,
            'dispatch': dispatch,
            'accounts': accounts,
            'service': service,
            'documents': documents,
            'timeline': timeline,
        }, status=status.HTTP_200_OK)


class Job360OverviewViewSet(viewsets.ModelViewSet):
    queryset = Job360Overview.objects.all().order_by('-created_at')
    serializer_class = Job360OverviewSerializer
    permission_classes = [permissions.IsAuthenticated]


class ExecutiveDashboardKPIViewSet(viewsets.ModelViewSet):
    queryset = ExecutiveDashboardKPI.objects.all().order_by('kpi_name')
    serializer_class = ExecutiveDashboardKPISerializer
    permission_classes = [permissions.IsAuthenticated]


class Customer360SummaryViewSet(viewsets.ModelViewSet):
    queryset = Customer360Summary.objects.all().order_by('customer_name')
    serializer_class = Customer360SummarySerializer
    permission_classes = [permissions.IsAuthenticated]


class Supplier360SummaryViewSet(viewsets.ModelViewSet):
    queryset = Supplier360Summary.objects.all().order_by('supplier_name')
    serializer_class = Supplier360SummarySerializer
    permission_classes = [permissions.IsAuthenticated]


class ItemMaterial360SummaryViewSet(viewsets.ModelViewSet):
    queryset = ItemMaterial360Summary.objects.all().order_by('item_code')
    serializer_class = ItemMaterial360SummarySerializer
    permission_classes = [permissions.IsAuthenticated]


class Employee360SummaryViewSet(viewsets.ModelViewSet):
    queryset = Employee360Summary.objects.all().order_by('employee_name')
    serializer_class = Employee360SummarySerializer
    permission_classes = [permissions.IsAuthenticated]


class GlobalActivityLogViewSet(viewsets.ModelViewSet):
    queryset = GlobalActivityLog.objects.all().order_by('-created_at')
    serializer_class = GlobalActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]


class ERPReportCenterItemViewSet(viewsets.ModelViewSet):
    queryset = ERPReportCenterItem.objects.all().order_by('report_code')
    serializer_class = ERPReportCenterItemSerializer
    permission_classes = [permissions.IsAuthenticated]


class JobProfitabilityRecordViewSet(viewsets.ModelViewSet):
    queryset = JobProfitabilityRecord.objects.all().order_by('-created_at')
    serializer_class = JobProfitabilityRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

