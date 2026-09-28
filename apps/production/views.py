import uuid
from django.db.models import Q
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import (
    ManufacturingJob, ProductionPlan, WorkCenter, RoutingOperation,
    WorkOrder, ProductionOrder, ProductionScheduleItem, ProductionEntry,
    WIPRecord, ProductionHold, ReworkOrder, ProductionScrap, FinishedGoodsItem
)
from .serializers import (
    ManufacturingJobSerializer, ProductionPlanSerializer, WorkCenterSerializer,
    RoutingOperationSerializer, WorkOrderSerializer, ProductionOrderSerializer,
    ProductionScheduleItemSerializer, ProductionEntrySerializer, WIPRecordSerializer,
    ProductionHoldSerializer, ReworkOrderSerializer, ProductionScrapSerializer,
    FinishedGoodsItemSerializer
)


class ManufacturingJobViewSet(viewsets.ModelViewSet):
    queryset = ManufacturingJob.objects.all()
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
    queryset = ProductionPlan.objects.all()
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


class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all().order_by('-created_at')
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
    queryset = ProductionOrder.objects.all()
    serializer_class = ProductionOrderSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['production_order_number', 'job_number', 'work_order_number']
    filterset_fields = ['status', 'work_order_id']


class ProductionScheduleItemViewSet(viewsets.ModelViewSet):
    queryset = ProductionScheduleItem.objects.all()
    serializer_class = ProductionScheduleItemSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['schedule_number', 'job_number', 'operation_name']
    filterset_fields = ['status', 'work_center_code']


class ProductionEntryViewSet(viewsets.ModelViewSet):
    queryset = ProductionEntry.objects.all()
    serializer_class = ProductionEntrySerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['production_entry_number', 'job_number', 'work_order_number', 'operation_name']
    filterset_fields = ['job_id', 'entry_date']


class WIPRecordViewSet(viewsets.ModelViewSet):
    queryset = WIPRecord.objects.all()
    serializer_class = WIPRecordSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['job_number', 'work_order_number', 'current_operation_name']
    filterset_fields = ['status', 'location']


class ProductionHoldViewSet(viewsets.ModelViewSet):
    queryset = ProductionHold.objects.all()
    serializer_class = ProductionHoldSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['hold_number', 'job_number', 'reason']
    filterset_fields = ['status']

    @action(detail=True, methods=['post'], url_path='resume')
    def resume_hold(self, request, pk=None):
        hold = self.get_object()
        hold.status = 'Resumed'
        hold.resume_date = timezone.now().date()
        hold.save()
        return Response({'message': f'Production Hold {hold.hold_number} resumed', 'status': hold.status})


class ReworkOrderViewSet(viewsets.ModelViewSet):
    queryset = ReworkOrder.objects.all()
    serializer_class = ReworkOrderSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['rework_number', 'job_number', 'item_name']
    filterset_fields = ['status']


class ProductionScrapViewSet(viewsets.ModelViewSet):
    queryset = ProductionScrap.objects.all()
    serializer_class = ProductionScrapSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['scrap_number', 'job_number', 'material_name']
    filterset_fields = ['scrap_type']


class FinishedGoodsItemViewSet(viewsets.ModelViewSet):
    queryset = FinishedGoodsItem.objects.all()
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
