import uuid
from datetime import datetime
from django.db.models import Q
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import (
    ManufacturingJob, ProductionPlan, WorkCenter, RoutingOperation,
    WorkOrder, ProductionOrder, ProductionScheduleItem, ProductionEntry,
    WIPRecord, ProductionHold, ReworkOrder, ProductionScrap, FinishedGoodsItem,
    ProductionMaterialRequest, DispatchOrder, PackingOrder
)
from .serializers import (
    ManufacturingJobSerializer, ProductionPlanSerializer, WorkCenterSerializer,
    RoutingOperationSerializer, WorkOrderSerializer, ProductionOrderSerializer,
    ProductionScheduleItemSerializer, ProductionEntrySerializer, WIPRecordSerializer,
    ProductionHoldSerializer, ReworkOrderSerializer, ProductionScrapSerializer,
    FinishedGoodsItemSerializer, ProductionMaterialRequestSerializer, DispatchOrderSerializer,
    PackingOrderSerializer
)


class ManufacturingJobViewSet(viewsets.ModelViewSet):
    queryset = ManufacturingJob.objects.all().order_by('-created_at', '-id')
    serializer_class = ManufacturingJobSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['job_number', 'product_name', 'customer_name', 'project_number']
    filterset_fields = ['status', 'customer_id', 'project_id']

    @action(detail=True, methods=['post'], url_path='update-progress')
    def update_progress(self, request, pk=None):
        job = self.get_object()
        progress = request.data.get('progress') or request.data.get('production_progress') or request.data.get('productionProgress')
        if progress is not None:
            job.production_progress = int(progress)
            if job.production_progress >= 100:
                job.status = 'Completed'
            elif job.production_progress > 0 and job.status == 'Pending':
                job.status = 'In Production'
            job.save()
        return Response(ManufacturingJobSerializer(job).data)


class ProductionPlanViewSet(viewsets.ModelViewSet):
    queryset = ProductionPlan.objects.all().order_by('-created_at', '-id')
    serializer_class = ProductionPlanSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['plan_number', 'job_number', 'product_name']
    filterset_fields = ['status', 'job_id']


class WorkCenterViewSet(viewsets.ModelViewSet):
    queryset = WorkCenter.objects.all()
    serializer_class = WorkCenterSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['work_center_code', 'work_center_name', 'machine_name']
    filterset_fields = ['status', 'department']


class RoutingOperationViewSet(viewsets.ModelViewSet):
    queryset = RoutingOperation.objects.all().order_by('sequence')
    serializer_class = RoutingOperationSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['operation_name', 'work_center_name']
    filterset_fields = ['status', 'department']

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        count = RoutingOperation.objects.count() + 1
        op_num = data.get('operation_number') or data.get('operationNumber') or count * 10
        op_id = data.get('id') or f"OP-{op_num}"
        
        data['id'] = op_id
        data['operation_number'] = int(op_num)
        data['operation_name'] = data.get('operation_name') or data.get('operationName', 'Routing Operation')
        data['sequence'] = int(data.get('sequence') or data.get('sequence_number') or count)
        data['work_center_code'] = data.get('work_center_code') or data.get('workCenterCode', '')
        data['work_center_name'] = data.get('work_center_name') or data.get('workCenterName', '')
        data['machine_name'] = data.get('machine_name') or data.get('machineName', '')
        data['department'] = data.get('department', 'Production')
        data['planned_setup_minutes'] = int(data.get('planned_setup_minutes') or data.get('plannedSetupMinutes') or 0)
        data['planned_processing_minutes'] = int(data.get('planned_processing_minutes') or data.get('plannedProcessingMinutes') or 0)
        data['total_planned_minutes'] = int(data.get('total_planned_minutes') or data.get('totalPlannedMinutes') or (data['planned_setup_minutes'] + data['planned_processing_minutes']))
        data['assigned_operator'] = data.get('assigned_operator') or data.get('assignedOperator', '')
        data['qc_required'] = bool(data.get('qc_required') if 'qc_required' in data else data.get('qcRequired', True))
        data['instructions'] = data.get('instructions', '')
        data['status'] = data.get('status', 'Ready')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all().order_by('-created_at', '-id')
    serializer_class = WorkOrderSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['work_order_number', 'job_number', 'customer_name', 'product_name']
    filterset_fields = ['status', 'priority', 'job_id']

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        wo_num = data.get('work_order_number') or data.get('workOrderNumber') or f"WO-2026-{uuid.uuid4().hex[:4].upper()}"
        wo_id = data.get('id') or wo_num

        # Upsert if already exists
        order = WorkOrder.objects.filter(Q(id=wo_id) | Q(work_order_number=wo_num)).first()
        if order:
            order.status = data.get('status', order.status)
            if 'product_name' in data or 'productName' in data:
                order.product_name = data.get('product_name') or data.get('productName')
            order.save()
            return Response(WorkOrderSerializer(order).data, status=status.HTTP_200_OK)

        # Normalize dates
        for dfield in ['planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date',
                       'plannedStartDate', 'plannedEndDate', 'actualStartDate', 'actualEndDate']:
            if dfield in data and not data[dfield]:
                data[dfield] = None

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            order = WorkOrder.objects.create(
                id=wo_id,
                work_order_number=wo_num,
                job_number=data.get('job_number') or data.get('jobNumber', ''),
                project_id=data.get('project_id') or data.get('projectId', ''),
                customer_name=data.get('customer_name') or data.get('customerName', ''),
                product_name=data.get('product_name') or data.get('productName', 'Product'),
                production_quantity=data.get('production_quantity') or data.get('productionQuantity', 1),
                status=data.get('status', 'Planned'),
                priority=data.get('priority', 'High')
            )
            return Response(WorkOrderSerializer(order).data, status=status.HTTP_201_CREATED)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post', 'get', 'patch'], url_path='release')
    def release_order(self, request, pk=None):
        order = WorkOrder.objects.filter(Q(id=pk) | Q(work_order_number=pk)).first()
        if not order:
            # Auto-create if releasing directly from client state
            data = request.data if isinstance(request.data, dict) else {}
            wo_num = data.get('work_order_number') or data.get('workOrderNumber') or pk
            order = WorkOrder.objects.create(
                id=pk,
                work_order_number=wo_num,
                job_number=data.get('job_number') or data.get('jobNumber', ''),
                project_id=data.get('project_id') or data.get('projectId', ''),
                customer_name=data.get('customer_name') or data.get('customerName', ''),
                product_name=data.get('product_name') or data.get('productName', 'Product'),
                production_quantity=data.get('production_quantity') or data.get('productionQuantity', 1),
                status='Released',
                priority=data.get('priority', 'High'),
                remarks=data.get('remarks', 'Released to shop floor')
            )
        else:
            order.status = 'Released'
            order.save()
        return Response({
            'message': f'Work Order {order.work_order_number} released',
            'status': order.status,
            'workOrder': WorkOrderSerializer(order).data
        })


class ProductionOrderViewSet(viewsets.ModelViewSet):
    queryset = ProductionOrder.objects.all().order_by('-created_at', '-id')
    serializer_class = ProductionOrderSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['production_order_number', 'job_number', 'work_order_number']
    filterset_fields = ['status', 'work_order_id']

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        po_num = data.get('production_order_number') or data.get('productionOrderNumber')
        if not po_num:
            count = ProductionOrder.objects.count() + 1
            po_num = f"PO-PROD-{datetime.now().year}-{count:03d}"
        
        data['id'] = data.get('id') or po_num
        data['production_order_number'] = po_num
        data['work_order_id'] = data.get('work_order_id') or data.get('workOrderId', '')
        data['work_order_number'] = data.get('work_order_number') or data.get('workOrderNumber', '')
        data['job_id'] = data.get('job_id') or data.get('jobId', '')
        data['job_number'] = data.get('job_number') or data.get('jobNumber', '')
        data['product_name'] = data.get('product_name') or data.get('productName', 'Manufactured Component')
        data['quantity'] = data.get('quantity') or 1
        data['bom_revision'] = data.get('bom_revision') or data.get('bomRevision', 'REV-01')
        data['design_revision'] = data.get('design_revision') or data.get('designRevision', 'REV-01')
        data['planned_start_date'] = data.get('planned_start_date') or data.get('plannedStartDate')
        data['planned_end_date'] = data.get('planned_end_date') or data.get('plannedEndDate')
        data['production_manager'] = data.get('production_manager') or data.get('productionManager', 'Production Head')
        data['status'] = data.get('status', 'In Progress')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ProductionScheduleItemViewSet(viewsets.ModelViewSet):
    queryset = ProductionScheduleItem.objects.all().order_by('-id')
    serializer_class = ProductionScheduleItemSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['schedule_number', 'job_number', 'work_order_number', 'operation_name']
    filterset_fields = ['status', 'work_center_code']

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        sch_num = data.get('schedule_number') or data.get('scheduleNumber') or f"SCH-{datetime.now().year}-{ProductionScheduleItem.objects.count() + 1:04d}"
        
        data['id'] = data.get('id') or sch_num
        data['schedule_number'] = sch_num
        data['job_id'] = data.get('job_id') or data.get('jobId', '')
        data['job_number'] = data.get('job_number') or data.get('jobNumber', '')
        data['work_order_number'] = data.get('work_order_number') or data.get('workOrderNumber', '')
        data['operation_name'] = data.get('operation_name') or data.get('operationName', '')
        data['work_center_code'] = data.get('work_center_code') or data.get('workCenterCode', '')
        data['work_center_name'] = data.get('work_center_name') or data.get('workCenterName', '')
        data['machine_name'] = data.get('machine_name') or data.get('machineName', '')
        data['assigned_operator'] = data.get('assigned_operator') or data.get('assignedOperator', '')
        
        # Datetime normalization
        for field in ['planned_start', 'plannedStart', 'planned_end', 'plannedEnd', 'actual_start', 'actualStart', 'actual_end', 'actualEnd']:
            if field in data and not data[field]:
                data[field] = None

        if 'planned_start' not in data and 'plannedStart' in data:
            data['planned_start'] = data['plannedStart'] or None
        if 'planned_end' not in data and 'plannedEnd' in data:
            data['planned_end'] = data['plannedEnd'] or None

        data['delay_hours'] = data.get('delay_hours') or data.get('delayHours', 0)
        data['status'] = data.get('status', 'Scheduled')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductionEntryViewSet(viewsets.ModelViewSet):
    queryset = ProductionEntry.objects.all().order_by('-entry_date', '-id')
    serializer_class = ProductionEntrySerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['production_entry_number', 'job_number', 'work_order_number', 'operation_name', 'operator_name']
    filterset_fields = ['job_id', 'entry_date']

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        entry_num = data.get('production_entry_number') or data.get('productionEntryNumber') or f"PENTRY-{datetime.now().year}-{ProductionEntry.objects.count() + 1:04d}"
        
        data['id'] = data.get('id') or entry_num
        data['production_entry_number'] = entry_num
        data['entry_date'] = data.get('entry_date') or data.get('entryDate') or datetime.now().strftime('%Y-%m-%d')
        data['job_id'] = data.get('job_id') or data.get('jobId', '')
        data['job_number'] = data.get('job_number') or data.get('jobNumber', '')
        data['work_order_number'] = data.get('work_order_number') or data.get('workOrderNumber', '')
        data['production_order_number'] = data.get('production_order_number') or data.get('productionOrderNumber', '')
        data['operation_name'] = data.get('operation_name') or data.get('operationName', '')
        data['work_center_name'] = data.get('work_center_name') or data.get('workCenterName', '')
        data['machine_name'] = data.get('machine_name') or data.get('machineName', '')
        data['operator_name'] = data.get('operator_name') or data.get('operatorName', '')
        data['start_time'] = data.get('start_time') or data.get('startTime', '08:00 AM')
        data['end_time'] = data.get('end_time') or data.get('endTime', '05:00 PM')
        
        data['planned_quantity'] = data.get('planned_quantity') or data.get('plannedQuantity', 0)
        data['produced_quantity'] = data.get('produced_quantity') or data.get('producedQuantity', 0)
        data['rejected_quantity'] = data.get('rejected_quantity') or data.get('rejectedQuantity', 0)
        data['rework_quantity'] = data.get('rework_quantity') or data.get('reworkQuantity', 0)
        data['scrap_quantity'] = data.get('scrap_quantity') or data.get('scrapQuantity', 0)
        
        produced = float(data['produced_quantity'])
        rejected = float(data['rejected_quantity'])
        scrap = float(data['scrap_quantity'])
        data['good_quantity'] = data.get('good_quantity') or data.get('goodQuantity') or max(0, produced - rejected - scrap)
        
        data['downtime_minutes'] = data.get('downtime_minutes') or data.get('downtimeMinutes', 0)
        data['downtime_reason'] = data.get('downtime_reason') or data.get('downtimeReason', '')
        data['remarks'] = data.get('remarks', '')
        data['created_by'] = data.get('created_by') or data.get('createdBy', data['operator_name'])

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WIPRecordViewSet(viewsets.ModelViewSet):
    queryset = WIPRecord.objects.all().order_by('-start_date', '-id')
    serializer_class = WIPRecordSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['job_number', 'work_order_number', 'current_operation_name']
    filterset_fields = ['status', 'location']

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data['id'] = data.get('id') or f"WIP-{datetime.now().year}-{WIPRecord.objects.count() + 1:04d}"
        data['job_id'] = data.get('job_id') or data.get('jobId', '')
        data['job_number'] = data.get('job_number') or data.get('jobNumber', '')
        data['work_order_number'] = data.get('work_order_number') or data.get('workOrderNumber', '')
        data['production_order_number'] = data.get('production_order_number') or data.get('productionOrderNumber', '')
        data['current_operation_name'] = data.get('current_operation_name') or data.get('currentOperationName', '')
        data['completed_operations_count'] = data.get('completed_operations_count') or data.get('completedOperationsCount', 0)
        data['total_operations_count'] = data.get('total_operations_count') or data.get('totalOperationsCount', 0)
        data['wip_quantity'] = data.get('wip_quantity') or data.get('wipQuantity', 0)
        data['responsible_department'] = data.get('responsible_department') or data.get('responsibleDepartment', '')
        data['start_date'] = data.get('start_date') or data.get('startDate') or datetime.now().strftime('%Y-%m-%d')
        data['expected_completion_date'] = data.get('expected_completion_date') or data.get('expectedCompletionDate') or None
        data['delay_days'] = data.get('delay_days') or data.get('delayDays', 0)
        data['status'] = data.get('status', 'In Progress')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductionHoldViewSet(viewsets.ModelViewSet):
    queryset = ProductionHold.objects.all().order_by('-start_date', '-id')
    serializer_class = ProductionHoldSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['hold_number', 'job_number', 'reason']
    filterset_fields = ['status']

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        hold_num = data.get('hold_number') or data.get('holdNumber') or f"HLD-{datetime.now().year}-{ProductionHold.objects.count() + 1:03d}"
        data['id'] = data.get('id') or hold_num
        data['hold_number'] = hold_num
        data['job_id'] = data.get('job_id') or data.get('jobId', '')
        data['job_number'] = data.get('job_number') or data.get('jobNumber', '')
        data['work_order_number'] = data.get('work_order_number') or data.get('workOrderNumber', '')
        data['operation_name'] = data.get('operation_name') or data.get('operationName', '')
        data['reason'] = data.get('reason') or 'Material Shortage'
        data['description'] = data.get('description', '')
        data['start_date'] = data.get('start_date') or data.get('startDate') or datetime.now().strftime('%Y-%m-%d')
        
        exp_resume = data.get('expected_resume_date') or data.get('expectedResumeDate')
        data['expected_resume_date'] = exp_resume if exp_resume else None
        
        data['approved_by'] = data.get('approved_by') or data.get('approvedBy', '')
        
        resume_d = data.get('resume_date') or data.get('resumeDate')
        data['resume_date'] = resume_d if resume_d else None
        
        data['status'] = data.get('status', 'Active Hold')
        data['remarks'] = data.get('remarks', '')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='resume')
    def resume_hold(self, request, pk=None):
        hold = ProductionHold.objects.filter(Q(id=pk) | Q(hold_number=pk)).first()
        if not hold:
            return Response({'error': 'Hold record not found'}, status=status.HTTP_404_NOT_FOUND)
        hold.status = 'Resumed'
        hold.resume_date = timezone.now().date()
        hold.save()
        return Response({'message': f'Production Hold {hold.hold_number} resumed', 'status': hold.status})



class ReworkOrderViewSet(viewsets.ModelViewSet):
    queryset = ReworkOrder.objects.all().order_by('-start_date', '-id')
    serializer_class = ReworkOrderSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['rework_number', 'job_number', 'item_name', 'work_order_number']
    filterset_fields = ['status']

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        rwk_num = data.get('rework_number') or data.get('reworkNumber') or f"RWK-{datetime.now().year}-{ReworkOrder.objects.count() + 1:03d}"
        
        data['id'] = data.get('id') or rwk_num
        data['rework_number'] = rwk_num
        data['job_id'] = data.get('job_id') or data.get('jobId', '')
        data['job_number'] = data.get('job_number') or data.get('jobNumber', '')
        data['work_order_number'] = data.get('work_order_number') or data.get('workOrderNumber', '')
        data['production_entry_number'] = data.get('production_entry_number') or data.get('productionEntryNumber', '')
        data['operation_name'] = data.get('operation_name') or data.get('operationName', '')
        data['item_code'] = data.get('item_code') or data.get('itemCode', 'ITEM-001')
        data['item_name'] = data.get('item_name') or data.get('itemName', 'Component Assembly')
        data['quantity'] = data.get('quantity') or 1
        data['uom'] = data.get('uom', 'Set')
        data['reason'] = data.get('reason', 'Welding Defect')
        data['responsible_department'] = data.get('responsible_department') or data.get('responsibleDepartment', 'Production')
        data['rework_instructions'] = data.get('rework_instructions') or data.get('reworkInstructions', '')
        data['assigned_operator'] = data.get('assigned_operator') or data.get('assignedOperator', '')
        data['start_date'] = data.get('start_date') or data.get('startDate') or datetime.now().strftime('%Y-%m-%d')
        data['completion_date'] = data.get('completion_date') or data.get('completionDate') or None
        data['status'] = data.get('status', 'Open')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductionScrapViewSet(viewsets.ModelViewSet):
    queryset = ProductionScrap.objects.all().order_by('-entry_date', '-id')
    serializer_class = ProductionScrapSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['scrap_number', 'job_number', 'material_name', 'work_order_number']
    filterset_fields = ['scrap_type']

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        scrap_num = data.get('scrap_number') or data.get('scrapNumber') or f"PSCRAP-{datetime.now().year}-{ProductionScrap.objects.count() + 1:03d}"
        
        data['id'] = data.get('id') or scrap_num
        data['scrap_number'] = scrap_num
        data['entry_date'] = data.get('entry_date') or data.get('entryDate') or datetime.now().strftime('%Y-%m-%d')
        data['job_id'] = data.get('job_id') or data.get('jobId', '')
        data['job_number'] = data.get('job_number') or data.get('jobNumber', '')
        data['work_order_number'] = data.get('work_order_number') or data.get('workOrderNumber', '')
        data['production_order_number'] = data.get('production_order_number') or data.get('productionOrderNumber', '')
        data['operation_name'] = data.get('operation_name') or data.get('operationName', '')
        data['material_code'] = data.get('material_code') or data.get('materialCode', 'SCRAP-001')
        data['material_name'] = data.get('material_name') or data.get('materialName', 'Metal Offcut Scrap')
        data['quantity'] = data.get('quantity') or 0
        data['uom'] = data.get('uom', 'Kg')
        data['reason'] = data.get('reason', '')
        data['scrap_type'] = data.get('scrap_type') or data.get('scrapType', 'Cutting Scrap')
        data['operator_name'] = data.get('operator_name') or data.get('operatorName', '')
        data['estimated_value'] = data.get('estimated_value') or data.get('estimatedValue', 0)
        data['remarks'] = data.get('remarks', '')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FinishedGoodsItemViewSet(viewsets.ModelViewSet):
    queryset = FinishedGoodsItem.objects.all().order_by('-created_at', '-id')
    serializer_class = FinishedGoodsItemSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['finished_goods_number', 'job_number', 'product_name']
    filterset_fields = ['status', 'qc_status', 'warehouse_id']

    @action(detail=True, methods=['post'], url_path='qc-pass')
    def qc_pass(self, request, pk=None):
        fg = self.get_object()
        fg.qc_status = 'QC Passed'
        fg.status = 'Ready for Dispatch'
        fg.save()
        return Response({'message': f'Finished Good {fg.finished_goods_number} passed QC', 'qcStatus': fg.qc_status, 'status': fg.status})


class ProductionMaterialRequestViewSet(viewsets.ModelViewSet):
    queryset = ProductionMaterialRequest.objects.all().order_by('-created_at', '-id')
    serializer_class = ProductionMaterialRequestSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['request_number', 'job_number', 'work_order_number', 'requested_by', 'issued_to']
    filterset_fields = ['status', 'production_stage', 'warehouse_id']

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        req_num = data.get('request_number') or data.get('requestNumber') or data.get('issue_number') or data.get('issueNumber') or f"ISS-{datetime.now().year}-{ProductionMaterialRequest.objects.count() + 1:04d}"
        
        data['id'] = data.get('id') or req_num
        data['request_number'] = req_num
        data['job_number'] = data.get('job_number') or data.get('jobNumber') or data.get('job_id') or data.get('jobId', '')
        data['job_id'] = data['job_number']
        data['work_order_number'] = data.get('work_order_number') or data.get('workOrderNumber') or data.get('work_order_id') or ''
        data['bom_number'] = data.get('bom_number') or data.get('bomNumber', 'BOM-2026-001')
        data['bom_revision'] = data.get('bom_revision') or data.get('bomRevision', 'Rev-01')
        data['production_stage'] = data.get('production_stage') or data.get('productionStage', 'Fabrication & Welding')
        data['requested_by'] = data.get('requested_by') or data.get('requestedBy') or data.get('issued_to') or data.get('issuedTo', 'Production Head')
        data['issued_to'] = data.get('issued_to') or data.get('issuedTo') or data['requested_by']
        data['issued_by'] = data.get('issued_by') or data.get('issuedBy', 'Store Supervisor')
        data['request_date'] = data.get('request_date') or data.get('requestDate') or data.get('issue_date') or data.get('issueDate') or datetime.now().strftime('%Y-%m-%d')
        data['warehouse_id'] = data.get('warehouse_id') or data.get('warehouseId', 'WH-001')
        data['warehouse_name'] = data.get('warehouse_name') or data.get('warehouseName', 'Raw Material Yard & Plate Store')
        data['total_value'] = data.get('total_value') or data.get('totalValue') or data.get('total_issue_value') or data.get('totalIssueValue', 0)
        data['items'] = data.get('items', [])
        data['status'] = data.get('status', 'Fully Issued')
        data['remarks'] = data.get('remarks') or data.get('notes', '')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DispatchOrderViewSet(viewsets.ModelViewSet):
    queryset = DispatchOrder.objects.all().order_by('-created_at', '-id')
    serializer_class = DispatchOrderSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['dispatch_number', 'job_number', 'work_order_number', 'customer_name', 'product_name', 'vehicle_number', 'lr_number']
    filterset_fields = ['status', 'customer_id', 'job_id']

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        disp_num = (
            data.get('dispatch_number')
            or data.get('dispatchNumber')
            or f"DISP-{datetime.now().year}-{DispatchOrder.objects.count() + 1:04d}"
        )
        data['id'] = data.get('id') or disp_num
        data['dispatch_number'] = disp_num
        data['dispatch_date'] = data.get('dispatch_date') or data.get('dispatchDate') or datetime.now().strftime('%Y-%m-%d')
        data['job_id'] = data.get('job_id') or data.get('jobId', '')
        data['job_number'] = data.get('job_number') or data.get('jobNumber', '')
        data['work_order_number'] = data.get('work_order_number') or data.get('workOrderNumber', '')
        data['finished_goods_number'] = data.get('finished_goods_number') or data.get('finishedGoodsNumber', '')
        data['customer_id'] = data.get('customer_id') or data.get('customerId', '')
        data['customer_name'] = data.get('customer_name') or data.get('customerName', 'Customer')
        data['customer_address'] = data.get('customer_address') or data.get('customerAddress', '')
        data['destination_city'] = data.get('destination_city') or data.get('destinationCity', '')
        data['product_name'] = data.get('product_name') or data.get('productName', 'Heavy Process Equipment')
        data['specification'] = data.get('specification', '')
        data['quantity'] = float(data.get('quantity', 1))
        data['uom'] = data.get('uom', 'Nos')
        data['serial_number'] = data.get('serial_number') or data.get('serialNumber', '')
        data['batch_number'] = data.get('batch_number') or data.get('batchNumber', '')
        data['weight_mt'] = float(data.get('weight_mt') or data.get('weightMT', 0))
        data['transporter_name'] = data.get('transporter_name') or data.get('transporterName', '')
        data['vehicle_number'] = data.get('vehicle_number') or data.get('vehicleNumber', '')
        data['lr_number'] = data.get('lr_number') or data.get('lrNumber', '')
        data['driver_name'] = data.get('driver_name') or data.get('driverName', '')
        data['driver_mobile'] = data.get('driver_mobile') or data.get('driverMobile', '')
        data['e_way_bill_number'] = data.get('e_way_bill_number') or data.get('eWayBillNumber', '')
        data['invoice_number'] = data.get('invoice_number') or data.get('invoiceNumber', '')
        data['packaging_type'] = data.get('packaging_type') or data.get('packagingType', 'Wooden Saddle & Tarpaulin')
        data['dispatch_type'] = data.get('dispatch_type') or data.get('dispatchType', 'Road Freight (Trailer)')
        data['qc_clearance_by'] = data.get('qc_clearance_by') or data.get('qcClearanceBy', 'Quality Manager')
        data['dispatched_by'] = data.get('dispatched_by') or data.get('dispatchedBy', 'Dispatch Officer')
        data['status'] = data.get('status', 'Ready for Dispatch')
        data['remarks'] = data.get('remarks', '')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='mark-dispatched')
    def mark_dispatched(self, request, pk=None):
        dispatch = self.get_object()
        dispatch.status = 'In Transit'
        dispatch.save()
        return Response(DispatchOrderSerializer(dispatch).data)

    @action(detail=True, methods=['post'], url_path='mark-delivered')
    def mark_delivered(self, request, pk=None):
        dispatch = self.get_object()
        dispatch.status = 'Delivered to Site'
        dispatch.save()
        return Response(DispatchOrderSerializer(dispatch).data)


class PackingOrderViewSet(viewsets.ModelViewSet):
    queryset = PackingOrder.objects.all().order_by('-created_at', '-id')
    serializer_class = PackingOrderSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['packing_number', 'customer_name', 'job_number', 'sales_order_number', 'product_name']
    filterset_fields = ['status', 'customer_id', 'job_id', 'sales_order_id']

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        pack_num = (
            data.get('packing_number')
            or data.get('packingNumber')
            or f"PACK-{datetime.now().year}-{PackingOrder.objects.count() + 1:04d}"
        )
        data['id'] = data.get('id') or pack_num
        data['packing_number'] = pack_num
        data['packing_date'] = data.get('packing_date') or data.get('packingDate') or datetime.now().strftime('%Y-%m-%d')
        data['customer_id'] = data.get('customer_id') or data.get('customerId', '')
        data['customer_name'] = data.get('customer_name') or data.get('customerName', 'Valued Customer')
        data['sales_order_id'] = data.get('sales_order_id') or data.get('salesOrderId', '')
        data['sales_order_number'] = data.get('sales_order_number') or data.get('salesOrderNumber', '')
        data['job_id'] = data.get('job_id') or data.get('jobId', '')
        data['job_number'] = data.get('job_number') or data.get('jobNumber', '')
        data['project_id'] = data.get('project_id') or data.get('projectId', '')
        data['project_number'] = data.get('project_number') or data.get('projectNumber', '')
        data['qc_inspection_number'] = data.get('qc_inspection_number') or data.get('qcInspectionNumber', '')
        data['finished_goods_number'] = data.get('finished_goods_number') or data.get('finishedGoodsNumber', '')
        data['product_name'] = data.get('product_name') or data.get('productName', 'Heavy Process Equipment')
        data['specification'] = data.get('specification', '')
        total_qty = float(data.get('total_quantity') or data.get('totalQuantity', 1))
        packed_qty = float(data.get('packed_quantity') or data.get('packedQuantity', 1))
        data['total_quantity'] = total_qty
        data['packed_quantity'] = packed_qty
        data['remaining_quantity'] = float(data.get('remaining_quantity') or data.get('remainingQuantity') or max(0, total_qty - packed_qty))
        data['uom'] = data.get('uom', 'Nos')
        data['package_type'] = data.get('package_type') or data.get('packageType', 'Heavy Duty Wooden Crate')
        data['package_dimensions'] = data.get('package_dimensions') or data.get('packageDimensions', '')
        data['gross_weight_kg'] = float(data.get('gross_weight_kg') or data.get('grossWeightKg', 0))
        data['net_weight_kg'] = float(data.get('net_weight_kg') or data.get('netWeightKg', 0))
        data['packed_by'] = data.get('packed_by') or data.get('packedBy', 'Packing Supervisor')
        data['verified_by'] = data.get('verified_by') or data.get('verifiedBy', 'Quality Inspector')
        data['status'] = data.get('status', 'Packed')
        data['remarks'] = data.get('remarks', '')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='mark-inspected')
    def mark_inspected(self, request, pk=None):
        order = self.get_object()
        order.status = 'Ready for Dispatch'
        order.save()
        return Response(PackingOrderSerializer(order).data)


class ProductionDashboardStatsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        jobs = list(ManufacturingJob.objects.all())
        work_centers = list(WorkCenter.objects.all())
        entries = list(ProductionEntry.objects.all())
        wips = list(WIPRecord.objects.all())

        status_counts = {}
        for j in jobs:
            st = j.status or 'Pending'
            status_counts[st] = status_counts.get(st, 0) + 1

        job_status_data = [
            {'name': k, 'value': v} for k, v in status_counts.items()
        ]

        work_center_capacity = [
            {
                'name': wc.work_center_code,
                'Capacity': float(wc.capacity_per_day_hours or 0),
                'Available': float(wc.available_hours or 0),
                'Efficiency': float(wc.efficiency_percent or 0),
            } for wc in work_centers
        ]

        # Group entries by day
        day_output = {}
        for e in entries:
            day_str = e.entry_date.strftime('%a') if e.entry_date else 'Day'
            if day_str not in day_output:
                day_output[day_str] = {'GoodQty': 0, 'Rejected': 0, 'Scrap': 0}
            day_output[day_str]['GoodQty'] += float(e.good_quantity or 0)
            day_output[day_str]['Rejected'] += float(e.rejected_quantity or 0)
            day_output[day_str]['Scrap'] += float(e.scrap_quantity or 0)

        daily_output = [
            {'day': k, **v} for k, v in day_output.items()
        ]

        wip_distribution = [
            {
                'job': w.job_number,
                'OperationsDone': w.completed_operations_count,
                'RemainingOps': max(0, w.total_operations_count - w.completed_operations_count),
            } for w in wips
        ]

        cost_comparison = [
            {
                'job': j.job_number,
                'Estimated': float(j.quantity or 1) * 100000,
                'Actual': float(j.quantity or 1) * 95000,
            } for j in jobs[:6]
        ]

        downtime_map = {}
        for e in entries:
            if e.downtime_reason:
                r = e.downtime_reason.strip()
                downtime_map[r] = downtime_map.get(r, 0) + int(e.downtime_minutes or 0)

        downtime_reasons = [
            {'name': k, 'value': v} for k, v in downtime_map.items()
        ]

        return Response({
            'job_status_data': job_status_data,
            'work_center_capacity': work_center_capacity,
            'daily_output': daily_output,
            'wip_distribution': wip_distribution,
            'cost_comparison': cost_comparison,
            'downtime_reasons': downtime_reasons,
            'total_jobs_count': len(jobs),
            'work_centers_count': len(work_centers),
            'entries_count': len(entries),
            'wip_count': len(wips),
        })


