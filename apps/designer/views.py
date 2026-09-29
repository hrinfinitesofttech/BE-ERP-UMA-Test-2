from datetime import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import (
    DesignJob,
    CustomerRequirement,
    Drawing2D,
    Design3DModel,
    BOMHeader,
    DesignRevisionLog,
    TechnicalDocumentItem,
    DesignTask,
)
from .serializers import (
    DesignJobSerializer,
    CustomerRequirementSerializer,
    Drawing2DSerializer,
    Design3DModelSerializer,
    BOMHeaderSerializer,
    DesignRevisionLogSerializer,
    TechnicalDocumentItemSerializer,
    DesignTaskSerializer,
)


class DesignJobViewSet(viewsets.ModelViewSet):
    queryset = DesignJob.objects.all().order_by('-created_at')
    serializer_class = DesignJobSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            code = data.get('design_job_number') or data.get('designJobNumber') or f"DES-2026-{DesignJob.objects.count() + 1:04d}"
            data['id'] = code
            data['design_job_number'] = code
        if 'project_id' not in data:
            data['project_id'] = data.get('projectId') or 'PRJ-2026-0001'
        if 'project_number' not in data:
            data['project_number'] = data.get('projectNumber') or ''
        if 'job_number' not in data:
            data['job_number'] = data.get('jobNumber') or ''
        if 'customer_id' not in data:
            data['customer_id'] = data.get('customerId') or 'CUST-001'
        if 'customer_name' not in data:
            data['customer_name'] = data.get('customerName') or ''
        if 'customer_po_number' not in data:
            data['customer_po_number'] = data.get('customerPoNumber') or ''
        if 'sales_order_number' not in data:
            data['sales_order_number'] = data.get('salesOrderNumber') or ''
        if 'product_name' not in data:
            data['product_name'] = data.get('productName') or 'Custom Equipment'
        if 'machine_type' not in data:
            data['machine_type'] = data.get('machineType') or 'Process Equipment'
        if 'delivery_date' not in data:
            data['delivery_date'] = data.get('deliveryDate') or datetime.now().strftime('%Y-%m-%d')
        if 'design_manager' not in data:
            data['design_manager'] = data.get('designManager') or 'Dharmesh Joshi'
        if 'assigned_designer' not in data:
            data['assigned_designer'] = data.get('assignedDesigner') or 'Dharmesh Joshi'
        if 'required_date' not in data:
            data['required_date'] = data.get('requiredDate') or data.get('delivery_date') or ''
        if 'active_revision' not in data:
            data['active_revision'] = data.get('activeRevision') or 'REV-00'
        if not data.get('created_date') and not data.get('createdDate'):
            data['created_date'] = datetime.now().strftime('%Y-%m-%d')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='release-to-production')
    def release_to_production(self, request, pk=None):
        job = self.get_object()
        job.status = 'released_to_production'
        job.save(update_fields=['status'])

        # Also release linked BOM
        bom = BOMHeader.objects.filter(design_job_id=job.id).first()
        if bom:
            bom.status = 'released'
            bom.release_date = datetime.now().strftime('%Y-%m-%d')
            bom.save(update_fields=['status', 'release_date'])

        return Response({
            'success': True,
            'message': f'Design Job {job.design_job_number} officially released to Production!',
            'job': DesignJobSerializer(job).data,
            'bom': BOMHeaderSerializer(bom).data if bom else None,
        })


class CustomerRequirementViewSet(viewsets.ModelViewSet):
    queryset = CustomerRequirement.objects.all().order_by('-created_at')
    serializer_class = CustomerRequirementSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            data['id'] = f"REQ-2026-{CustomerRequirement.objects.count() + 1:03d}"
        if 'design_job_id' not in data:
            data['design_job_id'] = data.get('designJobId') or 'DES-2026-0001'
        if 'project_id' not in data:
            data['project_id'] = data.get('projectId') or ''
        if 'job_number' not in data:
            data['job_number'] = data.get('jobNumber') or ''
        if 'customer_name' not in data:
            data['customer_name'] = data.get('customerName') or ''
        if 'contact_person' not in data:
            data['contact_person'] = data.get('contactPerson') or ''
        if 'contact_mobile' not in data:
            data['contact_mobile'] = data.get('contactMobile') or ''
        if 'machine_name' not in data:
            data['machine_name'] = data.get('machineName') or 'Custom Machine'
        if 'machine_type' not in data:
            data['machine_type'] = data.get('machineType') or 'Process Equipment'
        if 'production_requirement' not in data:
            data['production_requirement'] = data.get('productionRequirement') or ''
        if 'power_requirement' not in data:
            data['power_requirement'] = data.get('powerRequirement') or ''
        if 'automation_level' not in data:
            data['automation_level'] = data.get('automationLevel') or ''
        if 'control_system' not in data:
            data['control_system'] = data.get('controlSystem') or ''
        if 'safety_requirements' not in data:
            data['safety_requirements'] = data.get('safetyRequirements') or ''
        if 'special_requirements' not in data:
            data['special_requirements'] = data.get('specialRequirements') or ''
        if 'customer_drawing_url' not in data:
            data['customer_drawing_url'] = data.get('customerDrawingUrl') or ''
        if 'customer_notes' not in data:
            data['customer_notes'] = data.get('customerNotes') or ''
        if 'designer_notes' not in data:
            data['designer_notes'] = data.get('designerNotes') or ''

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class Drawing2DViewSet(viewsets.ModelViewSet):
    queryset = Drawing2D.objects.all().order_by('-created_at')
    serializer_class = Drawing2DSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            data['id'] = f"DWG-2D-{Drawing2D.objects.count() + 1:04d}"
        if 'design_job_id' not in data:
            data['design_job_id'] = data.get('designJobId') or ''
        if 'drawing_number' not in data:
            data['drawing_number'] = data.get('drawingNumber') or data['id']
        if 'title' not in data:
            data['title'] = data.get('drawingTitle') or data.get('title') or '2D CAD Drawing'
        if 'revision' not in data:
            data['revision'] = data.get('revisionNumber') or data.get('revision') or 'REV-00'
        if 'sheet_size' not in data:
            data['sheet_size'] = data.get('sheetSize') or 'A1'
        if 'scale' not in data:
            data['scale'] = data.get('scale') or '1:10'
        if 'prepared_by' not in data:
            data['prepared_by'] = data.get('drawnBy') or data.get('prepared_by') or 'Dharmesh Joshi'
        if 'checked_by' not in data:
            data['checked_by'] = data.get('checkedBy') or ''
        if 'approved_by' not in data:
            data['approved_by'] = data.get('approvedBy') or ''
        if 'file_url' not in data:
            data['file_url'] = data.get('fileUrl') or ''

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class Design3DModelViewSet(viewsets.ModelViewSet):
    queryset = Design3DModel.objects.all().order_by('-created_at')
    serializer_class = Design3DModelSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            data['id'] = f"MOD3D-{Design3DModel.objects.count() + 1:04d}"
        if 'design_job_id' not in data:
            data['design_job_id'] = data.get('designJobId') or ''
        if 'model_number' not in data:
            data['model_number'] = data.get('modelNumber') or data.get('designNumber') or data['id']
        if 'model_name' not in data:
            data['model_name'] = data.get('modelName') or data.get('modelTitle') or '3D CAD Model'
        if 'software' not in data:
            data['software'] = data.get('software') or 'SolidWorks'
        if 'version' not in data:
            data['version'] = data.get('version') or '2026 SP1'
        if 'mass_kg' not in data:
            data['mass_kg'] = data.get('massKg') or data.get('totalWeightKg') or 0
        if 'volume_m3' not in data:
            data['volume_m3'] = data.get('volumeM3') or 0
        if 'modeled_by' not in data:
            data['modeled_by'] = data.get('modeledBy') or data.get('designer') or 'Dharmesh Joshi'
        if 'file_url' not in data:
            data['file_url'] = data.get('fileUrl') or ''

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BOMHeaderViewSet(viewsets.ModelViewSet):
    queryset = BOMHeader.objects.all().order_by('-created_at')
    serializer_class = BOMHeaderSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id') or not data.get('bom_number') and not data.get('bomNumber'):
            code = f"BOM-2026-{BOMHeader.objects.count() + 1:04d}"
            data['id'] = code
            data['bom_number'] = code
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        bom = self.get_object()
        item = request.data
        items = list(bom.items or [])
        items.append(item)
        bom.items = items
        bom.total_items = len(items)
        bom.save(update_fields=['items', 'total_items'])
        return Response(BOMHeaderSerializer(bom).data)


class DesignRevisionLogViewSet(viewsets.ModelViewSet):
    queryset = DesignRevisionLog.objects.all().order_by('-date')
    serializer_class = DesignRevisionLogSerializer
    permission_classes = [permissions.AllowAny]


class TechnicalDocumentItemViewSet(viewsets.ModelViewSet):
    queryset = TechnicalDocumentItem.objects.all().order_by('-created_date')
    serializer_class = TechnicalDocumentItemSerializer
    permission_classes = [permissions.AllowAny]


class DesignTaskViewSet(viewsets.ModelViewSet):
    queryset = DesignTask.objects.all().order_by('-created_at')
    serializer_class = DesignTaskSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            data['id'] = f"DTASK-{DesignTask.objects.count() + 1:04d}"
        if 'design_job_id' not in data:
            data['design_job_id'] = data.get('designJobId') or ''
        if 'project_id' not in data:
            data['project_id'] = data.get('projectId') or ''
        if 'job_number' not in data:
            data['job_number'] = data.get('jobNumber') or ''
        if 'task_name' not in data:
            data['task_name'] = data.get('taskName') or 'Engineering Task'
        if 'customer_name' not in data:
            data['customer_name'] = data.get('customerName') or ''
        if 'machine_name' not in data:
            data['machine_name'] = data.get('machineName') or ''
        if 'start_date' not in data:
            data['start_date'] = data.get('startDate') or datetime.now().strftime('%Y-%m-%d')
        if 'target_date' not in data:
            data['target_date'] = data.get('targetDate') or data.get('dueDate') or ''
        if 'due_date' not in data:
            data['due_date'] = data.get('dueDate') or data.get('target_date') or ''
        if 'estimated_hours' not in data:
            data['estimated_hours'] = data.get('estimatedHours') or 16
        if 'actual_hours' not in data:
            data['actual_hours'] = data.get('actualHours') or 0
        if 'progress_percent' not in data:
            data['progress_percent'] = data.get('progressPercent') or 0

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'progressPercent' in data and 'progress_percent' not in data:
            data['progress_percent'] = data['progressPercent']
        if 'actualHours' in data and 'actual_hours' not in data:
            data['actual_hours'] = data['actualHours']
        if 'estimatedHours' in data and 'estimated_hours' not in data:
            data['estimated_hours'] = data['estimatedHours']
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

