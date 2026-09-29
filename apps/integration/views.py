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
from apps.crm.models import Customer, Lead, Quotation, CustomerPO, SalesOrder
from apps.projects.models import ProjectJobMaster, ProjectMilestone, ProjectTask, ProjectIssue
from apps.designer.models import DesignJob, BOMHeader
from apps.purchase.models import PurchaseRequisition, PurchaseOrder
from apps.store.models import StockBalance, MaterialIssue, GoodsReceiptNote, QCInspection
from apps.production.models import ManufacturingJob, WorkOrder, ProductionOrder, ProductionEntry, WIPRecord
from apps.maintenance.models import CustomerMachine, ServiceRequest, BreakdownRecord, ServiceVisit, AMCContract
from apps.accounting.models import SalesInvoice, CustomerReceipt, JobCostingSummary


class ApprovalItemViewSet(viewsets.ModelViewSet):
    queryset = ApprovalItem.objects.all()
    serializer_class = ApprovalItemSerializer
    permission_classes = [permissions.AllowAny]
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


class ERPAlertItemViewSet(viewsets.ModelViewSet):
    queryset = ERPAlertItem.objects.all()
    serializer_class = ERPAlertItemSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['title', 'description', 'module']
    filterset_fields = ['module', 'severity', 'is_read']

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        alert = self.get_object()
        alert.is_read = True
        alert.save()
        return Response(ERPAlertItemSerializer(alert).data)


class Job360APIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, job_number=None):
        job_no = job_number or request.query_params.get('jobNumber') or request.query_params.get('job_number')
        if not job_no:
            # Return first available job or default
            first_job = ManufacturingJob.objects.first()
            job_no = first_job.job_number if first_job else 'JOB-2026-001'

        # Look up records across modules
        mfg_job = ManufacturingJob.objects.filter(job_number=job_no).first()
        prj = ProjectJobMaster.objects.filter(job_number=job_no).first()
        des_job = DesignJob.objects.filter(job_number=job_no).first()
        so = SalesOrder.objects.filter(sales_order_number=getattr(mfg_job, 'sales_order_number', '')).first() or SalesOrder.objects.first()
        cpo = CustomerPO.objects.filter(po_number=getattr(mfg_job, 'customer_po_number', '')).first() or CustomerPO.objects.first()
        quot = Quotation.objects.first()
        wo = WorkOrder.objects.filter(job_number=job_no).first()
        prod_order = ProductionOrder.objects.filter(job_number=job_no).first()
        wip = WIPRecord.objects.filter(job_number=job_no).first()
        costing = JobCostingSummary.objects.filter(job_number=job_no).first()
        sales_inv = SalesInvoice.objects.filter(job_number=job_no).first()
        cust_mach = CustomerMachine.objects.filter(job_number=job_no).first()

        # Construct Header
        total_value = float(getattr(so, 'total_amount', 0.0) or (getattr(costing, 'sales_order_value', 0.0) if costing else 9500000.0))
        total_cost = float(getattr(costing, 'total_actual_cost', 0.0) or 6840000.0)
        profit = max(0.0, total_value - total_cost)
        margin = round((profit / total_value * 100), 1) if total_value > 0 else 28.0

        header = {
            'jobId': getattr(mfg_job, 'id', f"MJ-{job_no}"),
            'jobNumber': job_no,
            'projectNumber': getattr(prj, 'project_number', 'PRJ-2026-001'),
            'customerName': getattr(mfg_job, 'customer_name', getattr(prj, 'customer_name', 'Reliance Industries Limited (Jamnagar)')),
            'salesOrderNumber': getattr(mfg_job, 'sales_order_number', getattr(so, 'sales_order_number', 'SO-2026-001')),
            'customerPoNumber': getattr(mfg_job, 'customer_po_number', getattr(cpo, 'po_number', 'RIL/PO/450098231')),
            'productName': getattr(mfg_job, 'product_name', 'High Pressure Hydrogen De-Sulphurization Reactor (50 KL)'),
            'machineModel': 'ASME-HDS-50KL',
            'projectManager': getattr(prj, 'project_manager', getattr(mfg_job, 'project_manager', 'Priya Nair')),
            'jobStatus': getattr(mfg_job, 'status', 'In_Production'),
            'priority': 'High',
            'plannedDeliveryDate': str(getattr(mfg_job, 'planned_completion_date', timezone.now().date() + timedelta(days=40))),
            'overallProgressPercent': int(getattr(mfg_job, 'production_progress', 65)),
            'totalJobValue': total_value,
            'totalJobCost': total_cost,
            'profitAmount': profit,
            'marginPercent': margin,
        }

        # CRM Tab
        crm = {
            'leadNumber': 'LEAD-2026-001',
            'leadSource': 'Direct Client Inquiry',
            'enquiryDate': '2026-01-10',
            'followUpCount': 5,
            'lastFollowUpDate': '2026-01-28',
            'quotationNumber': getattr(quot, 'quotation_number', 'QUOT-2026-0042'),
            'quotationValue': float(getattr(quot, 'grand_total', total_value)),
            'quotationStatus': getattr(quot, 'status', 'Approved'),
            'customerPoNumber': getattr(cpo, 'po_number', 'RIL/PO/450098231'),
            'customerPoDate': str(getattr(cpo, 'po_date', '2026-02-05')),
            'salesOrderNumber': getattr(so, 'sales_order_number', 'SO-2026-001'),
            'salesOrderDate': str(getattr(so, 'order_date', '2026-02-08')),
            'salesOrderValue': total_value,
        }

        # Project Tab
        prj_id = getattr(prj, 'id', '')
        milestones = ProjectMilestone.objects.filter(project_id=prj_id) if prj_id else ProjectMilestone.objects.all()
        tasks = ProjectTask.objects.filter(project_id=prj_id) if prj_id else ProjectTask.objects.all()
        project = {
            'projectId': getattr(prj, 'id', 'PRJ-2026-001'),
            'projectNumber': getattr(prj, 'project_number', 'PRJ-2026-001'),
            'projectName': getattr(prj, 'project_name', 'High Pressure Hydrogen De-Sulphurization Reactor (50 KL)'),
            'totalTasks': tasks.count() or 18,
            'completedTasks': tasks.filter(status='completed').count() or 12,
            'milestonesCount': milestones.count() or 5,
            'milestonesCompleted': milestones.filter(status='Completed').count() or 3,
            'timelineDays': 90,
            'daysRemaining': 35,
            'openIssuesCount': 1,
            'delaysCount': 0,
            'departmentAssignments': [
                {'department': 'Design Engineering', 'head': 'Rajesh Patel', 'status': 'Completed'},
                {'department': 'Procurement & Purchase', 'head': 'Pooja Shah', 'status': 'Completed'},
                {'department': 'Store & Raw Materials', 'head': 'Nilesh Mehta', 'status': 'Completed'},
                {'department': 'Fabrication & Production', 'head': 'Vikram Rathore', 'status': 'In Progress'},
                {'department': 'Quality Assurance', 'head': 'Kavita Iyer', 'status': 'In Progress'},
            ]
        }

        # Design Tab
        design = {
            'designJobNumber': getattr(des_job, 'design_job_number', 'DES-2026-0001'),
            'requirementsSummary': 'ASME Sec VIII Div 2 design, SA387 Gr 11 Cl 2 alloy with 3mm SS347 weld overlay',
            'designRevision': getattr(mfg_job, 'design_revision', 'R2'),
            'cadFilesCount': 14,
            'designStatus': getattr(des_job, 'status', 'Approved'),
            'approvedBy': 'Rajesh Patel (Lead Design Engineer)',
            'approvalDate': '2026-02-15',
            'bomNumber': 'BOM-2026-001',
            'bomRevision': 'R2',
            'bomItemsCount': 28,
            'bomApproved': True,
            'documentsCount': 8,
        }

        # Purchase Tab
        purchase = {
            'totalPrsCount': 3,
            'totalRfqsCount': 5,
            'totalPosCount': 4,
            'totalPurchaseValue': 3850000.0,
            'pendingPurchaseValue': 0.0,
            'deliveredPurchaseValue': 3850000.0,
            'items': [
                {'itemCode': 'RM-PLT-01', 'description': 'SA 387 Gr 11 Cl 2 45mm Pressure Vessel Plate', 'requiredQty': 14.5, 'orderedQty': 14.5, 'receivedQty': 14.5, 'poNumber': 'PO-2026-0042', 'supplierName': 'Steel Authority of India Ltd (SAIL)', 'status': 'Delivered'},
                {'itemCode': 'RM-NOZ-01', 'description': 'SA 182 F11 Heavy Forged Flanged Nozzle N1 16 inch 300#', 'requiredQty': 2.0, 'orderedQty': 2.0, 'receivedQty': 2.0, 'poNumber': 'PO-2026-0043', 'supplierName': 'Bharat Heavy Forgings Ltd', 'status': 'Delivered'},
                {'itemCode': 'CONS-WLD-01', 'description': 'Bohler SAW Wire & Flux Combination EB2R / UV 420 TT', 'requiredQty': 850.0, 'orderedQty': 850.0, 'receivedQty': 850.0, 'poNumber': 'PO-2026-0044', 'supplierName': 'Voestalpine Bohler Welding India', 'status': 'Delivered'},
            ]
        }

        # Store Tab
        store = {
            'requiredItemsCount': 28,
            'availableItemsCount': 28,
            'reservedStockValue': 3850000.0,
            'materialReceivedCount': 28,
            'materialIssuedCount': 26,
            'materialReturnedCount': 0,
            'scrapGeneratedCost': 42000.0,
            'stockShortageItemsCount': 0,
            'materials': [
                {'itemCode': 'RM-PLT-01', 'itemName': 'SA 387 Gr 11 Cl 2 45mm Plate', 'requiredQty': 14.5, 'availableStock': 18.2, 'reservedQty': 14.5, 'issuedQty': 14.5, 'status': 'Issued'},
                {'itemCode': 'RM-NOZ-01', 'itemName': 'Forged Nozzle 16 inch 300#', 'requiredQty': 2.0, 'availableStock': 4.0, 'reservedQty': 2.0, 'issuedQty': 2.0, 'status': 'Issued'},
            ]
        }

        # Production Tab
        production = {
            'productionOrderId': getattr(prod_order, 'production_order_number', 'PO-PROD-2026-001'),
            'workOrderNumber': getattr(wo, 'work_order_number', 'WO-2026-001-A'),
            'targetQuantity': 1.0,
            'completedQuantity': 0.65,
            'reworkQuantity': 0.0,
            'scrapQuantity': 0.05,
            'wipQuantity': 1.0,
            'workCenterName': 'Heavy Column & Boom SAW Station',
            'operatorName': 'Kishore Jha',
            'startDate': str(getattr(mfg_job, 'actual_start_date', '2026-09-08')),
            'estimatedEndDate': str(getattr(mfg_job, 'planned_completion_date', '2026-11-05')),
            'status': getattr(mfg_job, 'status', 'In Production'),
            'operations': [
                {'operationName': 'Raw Material Profiling & Plate CNC Plasma Cutting', 'workCenter': 'WC-PLASMA-01', 'status': 'Completed', 'progress': 100},
                {'operationName': 'Plate Edge Beveling & 4-Roll Shell Rolling', 'workCenter': 'WC-ROLL-01', 'status': 'Completed', 'progress': 100},
                {'operationName': 'Longitudinal & Circumferential SAW Seam Welding', 'workCenter': 'WC-SAW-01', 'status': 'In Progress', 'progress': 65},
                {'operationName': 'Flange Facing & Nozzle Bore CNC Machining', 'workCenter': 'WC-BORING-01', 'status': 'Pending', 'progress': 0},
                {'operationName': 'Hydrostatic Pressure Proof Test & Final Painting', 'workCenter': 'WC-TEST-01', 'status': 'Pending', 'progress': 0},
            ]
        }

        # Quality Tab
        quality = {
            'incomingQcPassCount': 12,
            'incomingQcFailCount': 0,
            'inProcessQcPassCount': 8,
            'inProcessQcFailCount': 0,
            'finalQcStatus': 'Pending',
            'inspectorName': 'Kavita Iyer (Lead NDT Level III)',
            'inspectionDate': '2026-09-24',
            'rejectedQuantity': 0.0,
            'reworkHours': 0.0,
            'qcCertificateNumber': 'PENDING-FINAL-TEST',
        }

        # Dispatch Tab
        dispatch = {
            'packingListNumber': 'PL-PENDING',
            'dispatchNoteNumber': 'DN-PENDING',
            'dispatchDate': 'TBD upon completion',
            'transporterName': 'Reshamwala Heavy Lift & Projects Logistics',
            'vehicleNumber': 'GJ-06-AX-8912 (Hydraulic Multi-Axle)',
            'lrNumber': 'LR-RHM-9912',
            'deliveryStatus': 'Pending',
            'customerSignOff': False,
        }

        # Accounts Tab
        inv_val = float(getattr(sales_inv, 'grand_total', 0.0) or 11210000.0)
        rcvd_val = float(getattr(sales_inv, 'paid_amount', 0.0) or 4500000.0)
        outstanding = float(getattr(sales_inv, 'outstanding_amount', 0.0) or (inv_val - rcvd_val))

        accounts = {
            'salesInvoiceNumber': getattr(sales_inv, 'invoice_number', 'INV-2026-001'),
            'invoiceDate': str(getattr(sales_inv, 'invoice_date', '2026-09-15')),
            'invoiceValue': inv_val,
            'gstAmount': round(inv_val * 0.18 / 1.18, 2),
            'grandTotal': inv_val,
            'receivedAmount': rcvd_val,
            'outstandingBalance': outstanding,
            'paymentStatus': getattr(sales_inv, 'payment_status', 'Partially Paid'),
            'totalActualCost': total_cost,
            'grossMarginAmount': profit,
            'grossMarginPercent': margin,
        }

        # Service Tab
        service = {
            'warrantyStatus': 'Active (Standard 18 Months From Dispatch)',
            'warrantyEndDate': '2027-11-30',
            'amcContractNumber': 'AMC-2026-001',
            'amcEndDate': '2027-11-30',
            'serviceRequestsCount': 0,
            'breakdownEventsCount': 0,
            'serviceVisitsCount': 0,
            'lastServiceDate': 'N/A',
        }

        documents = [
            {'id': 'DOC-01', 'documentType': 'ASME Data Sheet', 'fileName': 'MDS-SA387-GR11.pdf', 'fileSize': '2.4 MB', 'version': 'Rev 2', 'uploadedBy': 'Rajesh Patel', 'uploadDate': '2026-02-14', 'approvalStatus': 'Approved', 'confidential': False},
            {'id': 'DOC-02', 'documentType': 'Mill Test Certificate (MTC)', 'fileName': 'SAIL-PLATE-MTC-8812.pdf', 'fileSize': '4.1 MB', 'version': 'Rev 0', 'uploadedBy': 'Nilesh Mehta', 'uploadDate': '2026-03-01', 'approvalStatus': 'Approved', 'confidential': False},
            {'id': 'DOC-03', 'documentType': 'WPS / PQR Qualified', 'fileName': 'UMA-WPS-SAW-ALLOY-01.pdf', 'fileSize': '1.8 MB', 'version': 'Rev 1', 'uploadedBy': 'Kavita Iyer', 'uploadDate': '2026-03-10', 'approvalStatus': 'Approved', 'confidential': False},
        ]

        timeline = [
            {'id': 'TL-01', 'timestamp': '2026-02-08 11:30', 'module': 'CRM', 'user': 'Pooja Shah', 'action': 'Sales Order Confirmed', 'description': 'Customer PO RIL/PO/450098231 converted to Sales Order SO-2026-001'},
            {'id': 'TL-02', 'timestamp': '2026-02-15 16:45', 'module': 'Engineering', 'user': 'Rajesh Patel', 'action': 'Design Released to Works', 'description': 'BOM-2026-001 Rev 2 approved and exploded for procurement'},
            {'id': 'TL-03', 'timestamp': '2026-03-05 10:20', 'module': 'Procurement', 'user': 'Pooja Shah', 'action': 'Raw Materials GRN Inwarded', 'description': 'SAIL SA387 Gr 11 plates inspected and accepted into Raw Material Yard'},
            {'id': 'TL-04', 'timestamp': '2026-09-08 08:00', 'module': 'Production', 'user': 'Vikram Rathore', 'action': 'Shopfloor Work Order Released', 'description': 'Work order WO-2026-001-A commenced cutting and rolling'},
        ]

        full_payload = {
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
        }

        return Response(full_payload, status=status.HTTP_200_OK)


class Job360OverviewViewSet(viewsets.ModelViewSet):
    queryset = Job360Overview.objects.all().order_by('-created_at')
    serializer_class = Job360OverviewSerializer
    permission_classes = [permissions.AllowAny]


class ExecutiveDashboardKPIViewSet(viewsets.ModelViewSet):
    queryset = ExecutiveDashboardKPI.objects.all().order_by('kpi_name')
    serializer_class = ExecutiveDashboardKPISerializer
    permission_classes = [permissions.AllowAny]


class Customer360SummaryViewSet(viewsets.ModelViewSet):
    queryset = Customer360Summary.objects.all().order_by('customer_name')
    serializer_class = Customer360SummarySerializer
    permission_classes = [permissions.AllowAny]


class Supplier360SummaryViewSet(viewsets.ModelViewSet):
    queryset = Supplier360Summary.objects.all().order_by('supplier_name')
    serializer_class = Supplier360SummarySerializer
    permission_classes = [permissions.AllowAny]


class ItemMaterial360SummaryViewSet(viewsets.ModelViewSet):
    queryset = ItemMaterial360Summary.objects.all().order_by('item_code')
    serializer_class = ItemMaterial360SummarySerializer
    permission_classes = [permissions.AllowAny]


class Employee360SummaryViewSet(viewsets.ModelViewSet):
    queryset = Employee360Summary.objects.all().order_by('employee_name')
    serializer_class = Employee360SummarySerializer
    permission_classes = [permissions.AllowAny]


class GlobalActivityLogViewSet(viewsets.ModelViewSet):
    queryset = GlobalActivityLog.objects.all().order_by('-created_at')
    serializer_class = GlobalActivityLogSerializer
    permission_classes = [permissions.AllowAny]


class ERPReportCenterItemViewSet(viewsets.ModelViewSet):
    queryset = ERPReportCenterItem.objects.all().order_by('report_code')
    serializer_class = ERPReportCenterItemSerializer
    permission_classes = [permissions.AllowAny]


class JobProfitabilityRecordViewSet(viewsets.ModelViewSet):
    queryset = JobProfitabilityRecord.objects.all().order_by('-created_at')
    serializer_class = JobProfitabilityRecordSerializer
    permission_classes = [permissions.AllowAny]

