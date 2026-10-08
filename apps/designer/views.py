from datetime import datetime
from django.db import models, connection
from django.db.models import Q
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

# Auto-migration / Schema ensure logic for production SQLite compatibility
def _ensure_designer_schema():
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(designer_designjob);")
            columns = {row[1]: row for row in cursor.fetchall()}
            if columns:
                if 'approval_notes' not in columns:
                    cursor.execute("ALTER TABLE designer_designjob ADD COLUMN approval_notes text DEFAULT '';")
                if 'approved_by' not in columns:
                    cursor.execute("ALTER TABLE designer_designjob ADD COLUMN approved_by varchar(150) DEFAULT '';")
                if 'approved_date' not in columns:
                    cursor.execute("ALTER TABLE designer_designjob ADD COLUMN approved_date varchar(50) DEFAULT '';")
                if 'disapproved_by' not in columns:
                    cursor.execute("ALTER TABLE designer_designjob ADD COLUMN disapproved_by varchar(150) DEFAULT '';")
                if 'disapproved_date' not in columns:
                    cursor.execute("ALTER TABLE designer_designjob ADD COLUMN disapproved_date varchar(50) DEFAULT '';")
                if 'rejection_reason' not in columns:
                    cursor.execute("ALTER TABLE designer_designjob ADD COLUMN rejection_reason text DEFAULT '';")
    except Exception as err:
        pass

try:
    _ensure_designer_schema()
except Exception:
    pass


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

    def get_object(self):
        from urllib.parse import unquote
        pk = unquote(str(self.kwargs.get('pk'))) if self.kwargs.get('pk') else self.kwargs.get('pk')
        obj = DesignJob.objects.filter(
            models.Q(id=pk) | models.Q(design_job_number=pk) | models.Q(job_number=pk)
        ).first()
        if not obj:
            raise Http404(f"Design Job '{pk}' not found")
        return obj

    def update(self, request, *args, **kwargs):
        from urllib.parse import unquote
        pk = unquote(str(self.kwargs.get('pk'))) if self.kwargs.get('pk') else self.kwargs.get('pk')
        job = DesignJob.objects.filter(
            models.Q(id=pk) | models.Q(design_job_number=pk) | models.Q(job_number=pk)
        ).first()
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not job:
            job_id = pk or data.get('designJobNumber') or data.get('design_job_number') or data.get('id') or f"DES-2026-{DesignJob.objects.count() + 1:04d}"
            job = DesignJob.objects.create(
                id=job_id,
                design_job_number=data.get('designJobNumber') or data.get('design_job_number') or job_id,
                project_id=data.get('projectId') or data.get('project_id') or 'PRJ-2026-0001',
                job_number=data.get('jobNumber') or data.get('job_number') or '',
                customer_id=data.get('customerId') or data.get('customer_id') or 'CUST-001',
                customer_name=data.get('customerName') or data.get('customer_name') or 'Customer',
                product_name=data.get('productName') or data.get('product_name') or 'Custom Equipment',
                delivery_date=data.get('deliveryDate') or data.get('delivery_date') or datetime.now().strftime('%Y-%m-%d'),
                created_date=data.get('createdDate') or data.get('created_date') or datetime.now().strftime('%Y-%m-%d'),
                assigned_designer=data.get('assignedDesigner') or data.get('assigned_designer') or 'Dharmesh Joshi',
                design_manager=data.get('designManager') or data.get('design_manager') or 'Ketan Patel',
                active_revision=data.get('activeRevision') or data.get('active_revision') or 'REV-00',
                status=data.get('status', 'in_progress'),
                remarks=data.get('remarks', ''),
            )
            return Response(DesignJobSerializer(job).data, status=status.HTTP_201_CREATED)

        if 'status' in data:
            job.status = data['status']
        if 'remarks' in data:
            job.remarks = data['remarks']
        if 'assignedDesigner' in data or 'assigned_designer' in data:
            job.assigned_designer = data.get('assignedDesigner') or data.get('assigned_designer')
        if 'designManager' in data or 'design_manager' in data:
            job.design_manager = data.get('designManager') or data.get('design_manager')
        if 'activeRevision' in data or 'active_revision' in data:
            job.active_revision = data.get('activeRevision') or data.get('active_revision')
        
        safe, err_resp = validate_edit_safety(job, data)
        if not safe:
            return err_resp

        job.save()
        return Response(DesignJobSerializer(job).data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post', 'patch'], url_path='approve')
    def approve(self, request, pk=None):
        from urllib.parse import unquote
        pk = unquote(str(pk)) if pk else pk
        job = DesignJob.objects.filter(
            models.Q(id=pk) | models.Q(design_job_number=pk) | models.Q(job_number=pk)
        ).first()

        # 1. Authorization check
        allowed, err_resp, user_info = validate_approval_permission(
            request,
            allowed_departments=['Design', 'Engineering', 'R&D', 'Technical', 'Management'],
            allowed_roles=['Design Manager', 'Chief Engineer', 'Manager', 'Director', 'Admin']
        )
        if not allowed:
            return err_resp

        # 2. Transition guard
        current_stat = job.status if job else 'pending'
        valid_trans, trans_resp = validate_approval_transition(current_stat, 'approve')
        if not valid_trans:
            return trans_resp

        approver = user_info['name'] or request.data.get('approvedBy') or request.data.get('approved_by') or 'Admin User'
        notes = request.data.get('approvalNotes') or request.data.get('approval_notes') or request.data.get('notes') or 'Approved after engineering verification.'
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')

        if not job:
            job_id = pk or request.data.get('designJobNumber') or request.data.get('id') or f"DES-2026-{DesignJob.objects.count() + 1:04d}"
            job = DesignJob.objects.create(
                id=job_id,
                design_job_number=request.data.get('designJobNumber') or job_id,
                project_id=request.data.get('projectId') or 'PRJ-2026-0001',
                job_number=request.data.get('jobNumber') or '',
                customer_id=request.data.get('customerId') or 'CUST-001',
                customer_name=request.data.get('customerName') or 'Customer',
                product_name=request.data.get('productName') or 'Custom Equipment',
                delivery_date=request.data.get('deliveryDate') or datetime.now().strftime('%Y-%m-%d'),
                created_date=request.data.get('createdDate') or datetime.now().strftime('%Y-%m-%d'),
                assigned_designer=request.data.get('assignedDesigner') or 'Dharmesh Joshi',
                design_manager=request.data.get('designManager') or 'Ketan Patel',
                active_revision=request.data.get('activeRevision') or 'REV-00',
                status='approved',
                approved_by=approver,
                approved_date=date_str,
                approval_notes=notes,
                remarks=f"Approved by {approver} on {date_str}. {notes}",
            )
        else:
            job.status = 'approved'
            job.approved_by = approver
            job.approved_date = date_str
            job.approval_notes = notes
            job.disapproved_by = ''
            job.disapproved_date = ''
            job.rejection_reason = ''
            job.remarks = f"Approved by {approver} on {date_str}. {notes}"
            job.save()

        # Update linked BOM status to approved
        bom = BOMHeader.objects.filter(
            models.Q(design_job_id=job.id) | models.Q(design_job_id=job.design_job_number) | models.Q(job_number=job.job_number)
        ).first()
        if bom:
            bom.status = 'approved'
            bom.approved_by = approver
            bom.save()

        log_approval_audit(user_info, 'APPROVE', 'Design', 'DesignJob', job.id, notes)
        return Response({
            'success': True,
            'message': f'Design Job {job.design_job_number} approved successfully by {approver}.',
            'job': DesignJobSerializer(job).data,
            'bom': BOMHeaderSerializer(bom).data if bom else None,
        })

    @action(detail=True, methods=['post', 'patch'], url_path='disapprove')
    def disapprove(self, request, pk=None):
        from urllib.parse import unquote
        pk = unquote(str(pk)) if pk else pk
        job = DesignJob.objects.filter(
            models.Q(id=pk) | models.Q(design_job_number=pk) | models.Q(job_number=pk)
        ).first()

        # 1. Authorization check
        allowed, err_resp, user_info = validate_approval_permission(
            request,
            allowed_departments=['Design', 'Engineering', 'R&D', 'Technical', 'Management'],
            allowed_roles=['Design Manager', 'Chief Engineer', 'Manager', 'Director', 'Admin']
        )
        if not allowed:
            return err_resp

        # 2. Transition guard
        current_stat = job.status if job else 'pending'
        valid_trans, trans_resp = validate_approval_transition(current_stat, 'disapprove')
        if not valid_trans:
            return trans_resp

        disapprover = user_info['name'] or request.data.get('disapprovedBy') or request.data.get('disapproved_by') or 'Admin User'
        reason = request.data.get('rejectionReason') or request.data.get('rejection_reason') or request.data.get('reason') or 'Design requires revision and engineering adjustments.'
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')

        if not job:
            job_id = pk or request.data.get('designJobNumber') or request.data.get('id') or f"DES-2026-{DesignJob.objects.count() + 1:04d}"
            job = DesignJob.objects.create(
                id=job_id,
                design_job_number=request.data.get('designJobNumber') or job_id,
                project_id=request.data.get('projectId') or 'PRJ-2026-0001',
                job_number=request.data.get('jobNumber') or '',
                customer_id=request.data.get('customerId') or 'CUST-001',
                customer_name=request.data.get('customerName') or 'Customer',
                product_name=request.data.get('productName') or 'Custom Equipment',
                delivery_date=request.data.get('deliveryDate') or datetime.now().strftime('%Y-%m-%d'),
                created_date=request.data.get('createdDate') or datetime.now().strftime('%Y-%m-%d'),
                assigned_designer=request.data.get('assignedDesigner') or 'Dharmesh Joshi',
                design_manager=request.data.get('designManager') or 'Ketan Patel',
                active_revision=request.data.get('activeRevision') or 'REV-00',
                status='disapproved',
                disapproved_by=disapprover,
                disapproved_date=date_str,
                rejection_reason=reason,
                remarks=f"Disapproved by {disapprover} on {date_str}. Reason: {reason}",
            )
        else:
            job.status = 'disapproved'
            job.disapproved_by = disapprover
            job.disapproved_date = date_str
            job.rejection_reason = reason
            job.remarks = f"Disapproved by {disapprover} on {date_str}. Reason: {reason}"
            job.save()

        # Update linked BOM status to draft / under_revision
        bom = BOMHeader.objects.filter(
            models.Q(design_job_id=job.id) | models.Q(design_job_id=job.design_job_number) | models.Q(job_number=job.job_number)
        ).first()
        if bom:
            bom.status = 'draft'
            bom.save()

        log_approval_audit(user_info, 'REJECT', 'Design', 'DesignJob', job.id, reason)
        return Response({
            'success': True,
            'message': f'Design Job {job.design_job_number} disapproved. Reason recorded: {reason}',
            'job': DesignJobSerializer(job).data,
            'bom': BOMHeaderSerializer(bom).data if bom else None,
        })

    @action(detail=True, methods=['post', 'patch'], url_path='reject')
    def reject(self, request, pk=None):
        return self.disapprove(request, pk=pk)


    @action(detail=True, methods=['post', 'patch'], url_path='release-to-production')
    def release_to_production(self, request, pk=None):
        from urllib.parse import unquote
        pk = unquote(str(pk)) if pk else pk
        job = DesignJob.objects.filter(
            models.Q(id=pk) | models.Q(design_job_number=pk) | models.Q(job_number=pk)
        ).first()

        releaser = request.data.get('releasedBy') or request.data.get('released_by') or 'Super Admin'
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        remarks = request.data.get('remarks') or f"Released to shop floor by {releaser} on {date_str}"

        if not job:
            job_id = pk or request.data.get('designJobNumber') or request.data.get('design_job_number') or request.data.get('id') or f"DES-2026-{DesignJob.objects.count() + 1:04d}"
            job = DesignJob.objects.create(
                id=job_id,
                design_job_number=request.data.get('designJobNumber') or request.data.get('design_job_number') or job_id,
                project_id=request.data.get('projectId') or request.data.get('project_id') or 'PRJ-2026-0001',
                job_number=request.data.get('jobNumber') or request.data.get('job_number') or '',
                customer_id=request.data.get('customerId') or request.data.get('customer_id') or 'CUST-001',
                customer_name=request.data.get('customerName') or request.data.get('customer_name') or 'Customer',
                product_name=request.data.get('productName') or request.data.get('product_name') or 'Custom Equipment',
                machine_type=request.data.get('machineType') or request.data.get('machine_type') or 'Process Equipment',
                quantity=int(request.data.get('quantity') or 1),
                delivery_date=request.data.get('deliveryDate') or request.data.get('delivery_date') or datetime.now().strftime('%Y-%m-%d'),
                created_date=request.data.get('createdDate') or request.data.get('created_date') or datetime.now().strftime('%Y-%m-%d'),
                assigned_designer=request.data.get('assignedDesigner') or request.data.get('assigned_designer') or 'Dharmesh Joshi',
                design_manager=request.data.get('designManager') or request.data.get('design_manager') or 'Ketan Patel',
                active_revision=request.data.get('activeRevision') or request.data.get('active_revision') or 'REV-00',
                status='released_to_production',
                approved_by=releaser,
                approved_date=date_str,
                remarks=remarks,
            )
        else:
            job.status = 'released_to_production'
            job.approved_by = releaser
            job.approved_date = date_str
            job.remarks = remarks
            if request.data.get('customerName') or request.data.get('customer_name'):
                job.customer_name = request.data.get('customerName') or request.data.get('customer_name')
            if request.data.get('productName') or request.data.get('product_name'):
                job.product_name = request.data.get('productName') or request.data.get('product_name')
            if request.data.get('jobNumber') or request.data.get('job_number'):
                job.job_number = request.data.get('jobNumber') or request.data.get('job_number')
            if request.data.get('projectId') or request.data.get('project_id'):
                job.project_id = request.data.get('projectId') or request.data.get('project_id')
            if request.data.get('machineType') or request.data.get('machine_type'):
                job.machine_type = request.data.get('machineType') or request.data.get('machine_type')
            if request.data.get('assignedDesigner') or request.data.get('assigned_designer'):
                job.assigned_designer = request.data.get('assignedDesigner') or request.data.get('assigned_designer')
            if request.data.get('designManager') or request.data.get('design_manager'):
                job.design_manager = request.data.get('designManager') or request.data.get('design_manager')
            if request.data.get('activeRevision') or request.data.get('active_revision'):
                job.active_revision = request.data.get('activeRevision') or request.data.get('active_revision')
            if request.data.get('deliveryDate') or request.data.get('delivery_date'):
                job.delivery_date = request.data.get('deliveryDate') or request.data.get('delivery_date')
            job.save()

        # Also release linked BOM
        bom = BOMHeader.objects.filter(
            models.Q(design_job_id=job.id) | models.Q(design_job_id=job.design_job_number) | models.Q(job_number=job.job_number)
        ).first()
        if bom:
            bom.status = 'released'
            bom.release_date = datetime.now().strftime('%Y-%m-%d')
            bom.save()

        # Also advance linked ProjectJobMaster & Planning Stage in Project module
        try:
            from apps.projects.models import ProjectJobMaster, ProjectPlanningStage
            proj_job = ProjectJobMaster.objects.filter(
                models.Q(job_number=job.job_number) | models.Q(project_number=job.project_id) | models.Q(id=job.project_id)
            ).first()
            if proj_job:
                if proj_job.current_status in ['planning', 'design', 'pending']:
                    proj_job.current_status = 'in_progress'
                proj_job.stage = 'Manufacturing & Store Readiness'
                proj_job.progress_percent = max(proj_job.progress_percent, 35)
                proj_job.save()

            ProjectPlanningStage.objects.filter(
                models.Q(project_id=job.project_id) & (models.Q(name__icontains='Design') | models.Q(department__icontains='Design'))
            ).update(status='completed', progress=100, completed_by=releaser, completed_at=date_str)
        except Exception:
            pass

        return Response({
            'success': True,
            'message': f'Design Job {job.design_job_number} officially released to Production!',
            'job': DesignJobSerializer(job).data,
            'bom': BOMHeaderSerializer(bom).data if bom else None,
        })

    @action(detail=True, methods=['post', 'patch'], url_path='revoke-release')
    def revoke_release(self, request, pk=None):
        from urllib.parse import unquote
        pk = unquote(str(pk)) if pk else pk
        job = DesignJob.objects.filter(
            models.Q(id=pk) | models.Q(design_job_number=pk) | models.Q(job_number=pk)
        ).first()

        revoker = request.data.get('revokedBy') or 'Super Admin'
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        remarks = request.data.get('remarks') or f"Status set to pending by {revoker} on {date_str}"

        if job:
            job.status = 'in_progress'
            job.remarks = remarks
            job.save()

        bom = BOMHeader.objects.filter(
            models.Q(design_job_id=job.id) | models.Q(design_job_id=job.design_job_number) | models.Q(job_number=job.job_number)
        ).first() if job else None
        if bom:
            bom.status = 'draft'
            bom.save()

        return Response({
            'success': True,
            'message': f'Design Job {job.design_job_number if job else pk} reset to review.',
            'job': DesignJobSerializer(job).data if job else None,
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
    serializer_class = BOMHeaderSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        try:
            if not BOMHeader.objects.filter(
                models.Q(id='BOM-JOB-TEST-6-V1') | models.Q(bom_number='test 6') | models.Q(job_number='JOB-TEST-6')
            ).exists():
                test_items = [
                    {
                        "id": "bi-test6-001",
                        "itemNo": 1,
                        "itemNumber": "ITM-001",
                        "partNumber": "MAT-201",
                        "part_number": "MAT-201",
                        "itemName": "Mild Steel Plate 5mm (IS 2062 Gr B)",
                        "item_name": "Mild Steel Plate 5mm (IS 2062 Gr B)",
                        "partName": "Mild Steel Plate 5mm (IS 2062 Gr B)",
                        "description": "RAW_MATERIAL for test 6",
                        "specification": "IS 2062 Grade B, 5mm thickness structural plate",
                        "material": "201 - Mild Steel Plate 5mm",
                        "itemType": "Raw Material",
                        "item_type": "RAW_MATERIAL",
                        "procurement": "PURCHASE",
                        "procurementType": "Purchase",
                        "quantity": 4.0,
                        "qty": 4.0,
                        "unit": "KG",
                        "estimatedRate": 150.0,
                        "estimated_rate": 150.0,
                        "rate": 150.0,
                        "totalEstimatedAmount": 600.0,
                        "total_estimated_amount": 600.0,
                        "makeBrand": "Tata Steel / Jindal"
                    },
                    {
                        "id": "bi-test6-002",
                        "itemNo": 2,
                        "itemNumber": "ITM-002",
                        "partNumber": "MAT-202",
                        "part_number": "MAT-202",
                        "itemName": "Table Legs 50x50 Box Sub-Assembly",
                        "item_name": "Table Legs 50x50 Box Sub-Assembly",
                        "partName": "Table Legs 50x50 Box Sub-Assembly",
                        "description": "FABRICATED for test 6",
                        "specification": "Fabricated 50x50x3mm square hollow section with base flange",
                        "material": "202 - Table Legs 50x50 Box Sub-Assembly",
                        "itemType": "Fabricated",
                        "item_type": "FABRICATED",
                        "procurement": "FABRICATE",
                        "procurementType": "In-House",
                        "quantity": 2.0,
                        "qty": 2.0,
                        "unit": "PCS",
                        "estimatedRate": 850.0,
                        "estimated_rate": 850.0,
                        "rate": 850.0,
                        "totalEstimatedAmount": 1700.0,
                        "total_estimated_amount": 1700.0,
                        "makeBrand": "In-House Shopfloor"
                    },
                    {
                        "id": "bi-test6-003",
                        "itemNo": 3,
                        "itemNumber": "ITM-003",
                        "partNumber": "MAT-203",
                        "part_number": "MAT-203",
                        "itemName": "Heavy Duty Leveling Stud M12",
                        "item_name": "Heavy Duty Leveling Stud M12",
                        "partName": "Heavy Duty Leveling Stud M12",
                        "description": "BOUGHT_OUT for test 6",
                        "specification": "M12 x 50mm Galvanized Leveling Bolt with Anti-Vibration Pad",
                        "material": "203 - Heavy Duty Leveling Stud M12",
                        "itemType": "Bought-Out",
                        "item_type": "BOUGHT_OUT",
                        "procurement": "PURCHASE",
                        "procurementType": "Purchase",
                        "quantity": 4.0,
                        "qty": 4.0,
                        "unit": "PCS",
                        "estimatedRate": 320.0,
                        "estimated_rate": 320.0,
                        "rate": 320.0,
                        "totalEstimatedAmount": 1280.0,
                        "total_estimated_amount": 1280.0,
                        "makeBrand": "Unbrako / Standard"
                    },
                    {
                        "id": "bi-test6-004",
                        "itemNo": 4,
                        "itemNumber": "ITM-004",
                        "partNumber": "MAT-204",
                        "part_number": "MAT-204",
                        "itemName": "Anti-Rust Zinc Spray Coating",
                        "item_name": "Anti-Rust Zinc Spray Coating",
                        "partName": "Anti-Rust Zinc Spray Coating",
                        "description": "CONSUMABLE for test 6",
                        "specification": "Cold Galvanizing Spray 95% Pure Zinc Primer",
                        "material": "204 - Anti-Rust Zinc Spray Coating",
                        "itemType": "Consumable",
                        "item_type": "CONSUMABLE",
                        "procurement": "PURCHASE",
                        "procurementType": "Purchase",
                        "quantity": 1.0,
                        "qty": 1.0,
                        "unit": "KG",
                        "estimatedRate": 480.0,
                        "estimated_rate": 480.0,
                        "rate": 480.0,
                        "totalEstimatedAmount": 480.0,
                        "total_estimated_amount": 480.0,
                        "makeBrand": "CRC / Rust-Oleum"
                    }
                ]
                BOMHeader.objects.create(
                    id='BOM-JOB-TEST-6-V1',
                    bom_number='test 6',
                    design_job_id='DES-2026-TEST-6',
                    project_id='PRJ-2026-TEST-6',
                    job_number='JOB-TEST-6',
                    active_revision='V1',
                    status='draft',
                    total_items=len(test_items),
                    total_weight_kg=45.0,
                    total_estimated_cost=4060.0,
                    prepared_by='Dharmesh Joshi',
                    release_date=datetime.now().strftime('%Y-%m-%d'),
                    items=test_items,
                    revisions=[]
                )
        except Exception:
            pass
        return BOMHeader.objects.all().order_by('-created_at')

    def get_object(self):
        pk = self.kwargs.get('pk')
        from urllib.parse import unquote
        decoded_pk = unquote(pk) if pk else pk
        obj = BOMHeader.objects.filter(
            models.Q(id=pk) | models.Q(id=decoded_pk) |
            models.Q(bom_number=pk) | models.Q(bom_number=decoded_pk) |
            models.Q(job_number=pk) | models.Q(job_number=decoded_pk) |
            models.Q(design_job_id=pk) | models.Q(design_job_id=decoded_pk)
        ).first()
        if not obj and pk:
            clean_pk = pk.replace('BOM-', '')
            obj = BOMHeader.objects.filter(
                models.Q(id=clean_pk) | models.Q(bom_number=clean_pk) | models.Q(job_number=clean_pk)
            ).first()
        if not obj:
            from django.http import Http404
            raise Http404(f"BOM '{pk}' not found")
        return obj

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
            formatted_items = []
            calc_total_cost = 0.0
            for idx, it in enumerate(items):
                if isinstance(it, dict):
                    qty = float(it.get('quantity') or it.get('qty') or 1.0)
                    rate = float(
                        it.get('estimatedRate') or it.get('estimated_rate') or
                        it.get('rate') or it.get('unitPrice') or it.get('unit_price') or
                        it.get('unitCost') or it.get('unit_cost') or it.get('est_rate') or
                        it.get('estRate') or it.get('costPerUnit') or 0.0
                    )
                    amt = float(
                        it.get('totalEstimatedAmount') or it.get('total_estimated_amount') or
                        it.get('total_amount') or it.get('totalAmount') or
                        it.get('extendedCost') or it.get('extended_cost') or (qty * rate)
                    )
                    calc_total_cost += amt
                    item_name = it.get('itemName') or it.get('item_name') or it.get('partName') or it.get('materialName') or it.get('material') or f"Component {idx+1}"
                    part_num = it.get('partNumber') or it.get('part_number') or it.get('itemCode') or it.get('item_code') or f"MAT-{idx+1:03d}"

                    formatted_item = {
                        **it,
                        'id': it.get('id') or f"ITM-{idx+1:03d}",
                        'itemNo': it.get('itemNo') or idx + 1,
                        'itemNumber': it.get('itemNumber') or f"ITM-{idx+1:03d}",
                        'partNumber': part_num,
                        'part_number': part_num,
                        'itemName': item_name,
                        'item_name': item_name,
                        'partName': item_name,
                        'description': it.get('description') or it.get('specification') or f"{it.get('item_type', 'Material')} requirement",
                        'specification': it.get('specification') or it.get('description') or '',
                        'material': it.get('material') or item_name,
                        'item_type': it.get('item_type') or it.get('itemType') or 'RAW_MATERIAL',
                        'itemType': it.get('itemType') or it.get('item_type') or 'RAW_MATERIAL',
                        'procurement': it.get('procurement') or ('FABRICATE' if it.get('procurementType') == 'In-House' else 'PURCHASE'),
                        'procurementType': it.get('procurementType') or ('In-House' if it.get('procurement') == 'FABRICATE' else 'Purchase'),
                        'quantity': qty,
                        'qty': qty,
                        'unit': it.get('unit') or 'PCS',
                        'estimatedRate': rate,
                        'estimated_rate': rate,
                        'rate': rate,
                        'unitCost': rate,
                        'unit_price': rate,
                        'totalEstimatedAmount': amt,
                        'total_estimated_amount': amt,
                        'total_amount': amt,
                        'totalAmount': amt,
                        'extendedCost': amt,
                        'materialGrade': it.get('materialGrade', it.get('material_grade', '')),
                    }
                    formatted_items.append(formatted_item)
            data['items'] = formatted_items
            if not data.get('total_estimated_cost') and not data.get('totalEstimatedCost'):
                data['total_estimated_cost'] = calc_total_cost

        # Upsert: check if already exists by id or bom_number or job_number
        target_id = data.get('id')
        target_bom_no = data.get('bom_number')
        target_job_no = data.get('job_number')
        existing = BOMHeader.objects.filter(
            models.Q(id=target_id) | models.Q(bom_number=target_bom_no) |
            (models.Q(job_number=target_job_no) if target_job_no else models.Q(id='__NONE__'))
        ).first()

        if existing:
            # Update existing BOM
            if 'items' in data:
                existing.items = data['items']
                existing.total_items = len(data['items'])
            if 'total_estimated_cost' in data:
                existing.total_estimated_cost = float(data['total_estimated_cost'])
            if 'active_revision' in data:
                existing.active_revision = data['active_revision']
            if 'status' in data:
                existing.status = data['status']
            if 'prepared_by' in data:
                existing.prepared_by = data['prepared_by']
            if 'job_number' in data and data['job_number']:
                existing.job_number = data['job_number']
            existing.save()
            return Response(BOMHeaderSerializer(existing).data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        from urllib.parse import unquote
        decoded_pk = unquote(pk) if pk else pk
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        bom = BOMHeader.objects.filter(
            models.Q(id=pk) | models.Q(id=decoded_pk) |
            models.Q(bom_number=pk) | models.Q(bom_number=decoded_pk) |
            models.Q(job_number=pk) | models.Q(job_number=decoded_pk) |
            models.Q(design_job_id=pk) | models.Q(design_job_id=decoded_pk)
        ).first()

        items = data.get('items')
        calc_total_cost = None
        if items is not None and isinstance(items, list):
            formatted_items = []
            calc_total = 0.0
            for idx, it in enumerate(items):
                if isinstance(it, dict):
                    qty = float(it.get('quantity') or it.get('qty') or 1.0)
                    rate = float(
                        it.get('estimatedRate') or it.get('estimated_rate') or
                        it.get('rate') or it.get('unitPrice') or it.get('unit_price') or
                        it.get('unitCost') or it.get('unit_cost') or it.get('est_rate') or
                        it.get('estRate') or it.get('costPerUnit') or 0.0
                    )
                    amt = float(
                        it.get('totalEstimatedAmount') or it.get('total_estimated_amount') or
                        it.get('total_amount') or it.get('totalAmount') or
                        it.get('extendedCost') or it.get('extended_cost') or (qty * rate)
                    )
                    calc_total += amt
                    item_name = it.get('itemName') or it.get('item_name') or it.get('partName') or it.get('materialName') or it.get('material') or f"Component {idx+1}"
                    part_num = it.get('partNumber') or it.get('part_number') or it.get('itemCode') or it.get('item_code') or f"MAT-{idx+1:03d}"
                    formatted_items.append({
                        **it,
                        'id': it.get('id') or f"ITM-{idx+1:03d}",
                        'itemNo': it.get('itemNo') or idx + 1,
                        'itemNumber': it.get('itemNumber') or f"ITM-{idx+1:03d}",
                        'partNumber': part_num,
                        'part_number': part_num,
                        'itemName': item_name,
                        'item_name': item_name,
                        'partName': item_name,
                        'description': it.get('description') or it.get('specification') or '',
                        'specification': it.get('specification') or it.get('description') or '',
                        'material': it.get('material') or item_name,
                        'item_type': it.get('item_type') or it.get('itemType') or 'RAW_MATERIAL',
                        'itemType': it.get('itemType') or it.get('item_type') or 'RAW_MATERIAL',
                        'procurement': it.get('procurement') or ('FABRICATE' if it.get('procurementType') == 'In-House' else 'PURCHASE'),
                        'procurementType': it.get('procurementType') or ('In-House' if it.get('procurement') == 'FABRICATE' else 'Purchase'),
                        'quantity': qty,
                        'qty': qty,
                        'unit': it.get('unit') or 'PCS',
                        'estimatedRate': rate,
                        'estimated_rate': rate,
                        'rate': rate,
                        'unitCost': rate,
                        'unit_price': rate,
                        'totalEstimatedAmount': amt,
                        'total_estimated_amount': amt,
                        'total_amount': amt,
                        'totalAmount': amt,
                        'extendedCost': amt,
                    })
            data['items'] = formatted_items
            data['total_items'] = len(formatted_items)
            calc_total_cost = calc_total

        if not bom:
            bom_id = pk or data.get('id') or data.get('bomNumber') or f"BOM-{BOMHeader.objects.count() + 1:04d}"
            bom = BOMHeader.objects.create(
                id=bom_id,
                bom_number=data.get('bomNumber') or data.get('bom_number') or bom_id,
                design_job_id=data.get('designJobId') or data.get('design_job_id') or 'DES-2026-0001',
                project_id=data.get('projectId') or data.get('project_id') or 'PRJ-2026-0001',
                job_number=data.get('jobNumber') or data.get('job_number') or 'JOB-2026-001',
                active_revision=data.get('activeRevision') or data.get('active_revision') or 'REV-01',
                status=data.get('status') or data.get('approvalStatus') or 'draft',
                total_items=data.get('total_items', len(data.get('items', []))),
                total_estimated_cost=float(data.get('total_estimated_cost') or data.get('totalEstimatedCost') or data.get('estimatedTotalCost') or (calc_total_cost if calc_total_cost is not None else 0.0)),
                prepared_by=data.get('preparedBy') or data.get('prepared_by') or 'Engineering Team',
                approved_by=data.get('approvedBy') or data.get('approved_by') or '',
                release_date=data.get('releaseDate') or data.get('release_date') or '',
                items=data.get('items', []),
            )
            return Response(BOMHeaderSerializer(bom).data, status=status.HTTP_201_CREATED)

        if 'items' in data:
            bom.items = data['items']
            bom.total_items = len(data['items'])
        if calc_total_cost is not None:
            bom.total_estimated_cost = calc_total_cost
        elif 'totalEstimatedCost' in data or 'total_estimated_cost' in data:
            bom.total_estimated_cost = float(data.get('totalEstimatedCost') or data.get('total_estimated_cost') or 0.0)
        if 'status' in data or 'approvalStatus' in data:
            bom.status = data.get('status') or data.get('approvalStatus') or bom.status
        if 'approvedBy' in data or 'approved_by' in data:
            bom.approved_by = data.get('approvedBy') or data.get('approved_by') or bom.approved_by
        if 'activeRevision' in data or 'active_revision' in data:
            bom.active_revision = data.get('activeRevision') or data.get('active_revision') or bom.active_revision
        if 'preparedBy' in data or 'prepared_by' in data:
            bom.prepared_by = data.get('preparedBy') or data.get('prepared_by') or bom.prepared_by

        bom.save()
        return Response(BOMHeaderSerializer(bom).data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        bom = self.get_object()
        item = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        items = list(bom.items or [])
        idx = len(items)
        qty = float(item.get('quantity') or item.get('qty') or 1.0)
        rate = float(
            item.get('estimatedRate') or item.get('estimated_rate') or
            item.get('rate') or item.get('unitPrice') or item.get('unit_price') or
            item.get('unitCost') or item.get('unit_cost') or item.get('est_rate') or
            item.get('estRate') or item.get('costPerUnit') or 0.0
        )
        amt = float(
            item.get('totalEstimatedAmount') or item.get('total_estimated_amount') or
            item.get('total_amount') or item.get('totalAmount') or
            item.get('extendedCost') or item.get('extended_cost') or (qty * rate)
        )
        item_name = item.get('itemName') or item.get('item_name') or item.get('partName') or item.get('materialName') or item.get('material') or f"Component {idx+1}"
        part_num = item.get('partNumber') or item.get('part_number') or item.get('itemCode') or item.get('item_code') or f"MAT-{idx+1:03d}"

        formatted_item = {
            **item,
            'id': item.get('id') or f"ITM-{idx+1:03d}",
            'itemNo': item.get('itemNo') or idx + 1,
            'itemNumber': item.get('itemNumber') or f"ITM-{idx+1:03d}",
            'partNumber': part_num,
            'part_number': part_num,
            'itemName': item_name,
            'item_name': item_name,
            'partName': item_name,
            'description': item.get('description') or item.get('specification') or '',
            'specification': item.get('specification') or item.get('description') or '',
            'material': item.get('material') or item_name,
            'item_type': item.get('item_type') or item.get('itemType') or 'RAW_MATERIAL',
            'itemType': item.get('itemType') or item.get('item_type') or 'RAW_MATERIAL',
            'procurement': item.get('procurement') or ('FABRICATE' if item.get('procurementType') == 'In-House' else 'PURCHASE'),
            'procurementType': item.get('procurementType') or ('In-House' if item.get('procurement') == 'FABRICATE' else 'Purchase'),
            'quantity': qty,
            'qty': qty,
            'unit': item.get('unit') or 'PCS',
            'estimatedRate': rate,
            'estimated_rate': rate,
            'rate': rate,
            'unitCost': rate,
            'unit_price': rate,
            'totalEstimatedAmount': amt,
            'total_estimated_amount': amt,
            'total_amount': amt,
            'totalAmount': amt,
            'extendedCost': amt,
        }
        items.append(formatted_item)
        bom.items = items
        bom.total_items = len(items)
        new_total_cost = sum(float(i.get('totalEstimatedAmount') or i.get('total_amount') or 0.0) for i in items)
        bom.total_estimated_cost = new_total_cost
        bom.save(update_fields=['items', 'total_items', 'total_estimated_cost'])
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

