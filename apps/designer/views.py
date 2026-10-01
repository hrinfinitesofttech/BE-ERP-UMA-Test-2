from datetime import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import (
    DesignJob,
    CustomerRequirement,
    Drawing2D,
    Design3DModel,
    AssemblyDrawing,
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
    AssemblyDrawingSerializer,
    BOMHeaderSerializer,
    DesignRevisionLogSerializer,
    TechnicalDocumentItemSerializer,
    DesignTaskSerializer,
)


class AssemblyDrawingViewSet(viewsets.ModelViewSet):
    queryset = AssemblyDrawing.objects.all().order_by('-created_at')
    serializer_class = AssemblyDrawingSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            code = data.get('assembly_number') or data.get('assemblyNumber') or f"ASM-2026-{AssemblyDrawing.objects.count() + 1:04d}"
            data['id'] = code
        if 'assembly_number' not in data:
            data['assembly_number'] = data.get('assemblyNumber') or f"ASM-{data.get('id', '001')}"
        if 'assembly_title' not in data:
            data['assembly_title'] = data.get('assemblyTitle') or 'Sub-Assembly Drawing'
        if 'sub_assembly_code' not in data:
            data['sub_assembly_code'] = data.get('subAssemblyCode') or ''
        if 'parent_assembly_number' not in data:
            data['parent_assembly_number'] = data.get('parentAssemblyNumber') or ''
        if 'revision_number' not in data:
            data['revision_number'] = data.get('revisionNumber') or 'REV-00'
        if 'file_format' not in data:
            data['file_format'] = data.get('fileFormat') or 'DWG'
        if 'file_size' not in data:
            data['file_size'] = data.get('fileSize') or '5.0 MB'
        if 'file_url' not in data:
            data['file_url'] = data.get('fileUrl') or '#'
        if 'linked_bom_item_id' not in data:
            data['linked_bom_item_id'] = data.get('linkedBOMItemId') or ''
        if 'drawn_by' not in data:
            data['drawn_by'] = data.get('drawnBy') or ''
        if 'approved_by' not in data:
            data['approved_by'] = data.get('approvedBy') or ''
        if 'design_job_id' not in data:
            data['design_job_id'] = data.get('designJobId') or ''
        if 'job_number' not in data:
            data['job_number'] = data.get('jobNumber') or ''
        if 'project_id' not in data:
            data['project_id'] = data.get('projectId') or ''

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class DesignJobViewSet(viewsets.ModelViewSet):
    queryset = DesignJob.objects.all().order_by('-created_at')
    serializer_class = DesignJobSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        job_id = data.get('id') or data.get('design_job_number') or data.get('designJobNumber')
        if not job_id or DesignJob.objects.filter(id=job_id).exists() or DesignJob.objects.filter(design_job_number=job_id).exists():
            import re
            all_ids = list(DesignJob.objects.values_list('id', flat=True)) + list(DesignJob.objects.values_list('design_job_number', flat=True))
            max_num = 0
            for did in all_ids:
                match = re.search(r'(\d+)$', str(did))
                if match:
                    max_num = max(max_num, int(match.group(1)))
            next_num = max_num + 1
            job_id = f"DES-2026-{next_num:04d}"
            while DesignJob.objects.filter(id=job_id).exists() or DesignJob.objects.filter(design_job_number=job_id).exists():
                next_num += 1
                job_id = f"DES-2026-{next_num:04d}"

        data['id'] = job_id
        data['design_job_number'] = job_id
        data['designJobNumber'] = job_id

        if not data.get('project_id') and not data.get('projectId'):
            data['project_id'] = 'PRJ-2026-0001'
        if not data.get('customer_id') and not data.get('customerId'):
            data['customer_id'] = 'CUST-001'
        if not data.get('customer_name') and not data.get('customerName'):
            data['customer_name'] = 'Customer'
        if not data.get('product_name') and not data.get('productName'):
            data['product_name'] = 'Custom Equipment'
        if not data.get('delivery_date') and not data.get('deliveryDate'):
            data['delivery_date'] = datetime.now().strftime('%Y-%m-%d')
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
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        
        # Support Developer JSON payload: product, bom_name, version, quantity, items
        if 'bom_name' in data and not data.get('bom_number'):
            data['bom_number'] = data['bom_name']
        if not data.get('id'):
            data['id'] = data.get('bom_number') or data.get('bomNumber') or f"BOM-2026-{BOMHeader.objects.count() + 1:04d}"
        if 'bom_number' not in data:
            data['bom_number'] = data.get('bomNumber') or data['id']
            
        if 'product' in data:
            if 'design_job_id' not in data:
                data['design_job_id'] = f"PRD-{data['product']}" if isinstance(data['product'], int) else str(data['product'])
            if 'job_number' not in data:
                data['job_number'] = str(data['product'])

        if not data.get('design_job_id'):
            data['design_job_id'] = data.get('designJobId') or 'DES-2026-0001'
        if not data.get('project_id'):
            data['project_id'] = data.get('projectId') or 'PRJ-2026-0001'
        if not data.get('job_number'):
            data['job_number'] = data.get('jobNumber') or 'JOB-2026-001'
            
        if 'version' in data and 'active_revision' not in data:
            data['active_revision'] = data['version']
        if not data.get('active_revision'):
            data['active_revision'] = data.get('activeRevision') or 'V1'
            
        if not data.get('prepared_by'):
            data['prepared_by'] = data.get('preparedBy') or 'Engineering Team'

        # Process items if present
        items = data.get('items', [])
        if isinstance(items, list):
            data['total_items'] = len(items)
            # Ensure standard item structure
            formatted_items = []
            for idx, it in enumerate(items):
                if isinstance(it, dict):
                    formatted_item = {
                        'id': it.get('id') or f"ITM-{idx+1:03d}",
                        'itemNumber': it.get('itemNumber') or f"ITM-{idx+1:03d}",
                        'material': it.get('material') or it.get('partNumber') or it.get('materialName') or f"MAT-{idx+1}",
                        'partNumber': it.get('partNumber') or str(it.get('material', f"MAT-{idx+1}")),
                        'partName': it.get('partName') or it.get('materialName') or f"Component {idx+1}",
                        'item_type': it.get('item_type') or it.get('itemType') or 'RAW_MATERIAL',
                        'itemType': it.get('itemType') or it.get('item_type') or 'RAW_MATERIAL',
                        'procurement': it.get('procurement') or 'PURCHASE',
                        'quantity': float(it.get('quantity', 1)),
                        'unit': it.get('unit') or 'PCS',
                        'unitCost': float(it.get('unitCost', it.get('unit_cost', 0))),
                        'extendedCost': float(it.get('extendedCost', it.get('extended_cost', 0))),
                        'materialGrade': it.get('materialGrade', it.get('material_grade', '')),
                    }
                    formatted_items.append(formatted_item)
            data['items'] = formatted_items

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
    queryset = TechnicalDocumentItem.objects.all().order_by('-created_at')
    serializer_class = TechnicalDocumentItemSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            data['id'] = f"TDOC-{TechnicalDocumentItem.objects.count() + 1:04d}"
        if not data.get('doc_number') and not data.get('docNumber'):
            data['doc_number'] = data['id']
        if not data.get('upload_date') and not data.get('uploadDate'):
            data['upload_date'] = datetime.now().strftime('%Y-%m-%d')
        if not data.get('created_date') and not data.get('createdDate'):
            data['created_date'] = datetime.now().strftime('%Y-%m-%d')
        if 'documentName' in data and not data.get('document_name'):
            data['document_name'] = data['documentName']
        if not data.get('title') and data.get('document_name'):
            data['title'] = data['document_name']

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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

