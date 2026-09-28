import uuid
from datetime import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from apps.core.models import NumberingSetting
from .models import (
    ProjectJobMaster,
    ProjectPlanningStage,
    ProjectMilestone,
    ProjectTask,
    DepartmentAssignment,
    ProjectIssue,
    ProjectDelay,
    CustomerChangeRequest,
    ProjectCost,
)
from .serializers import (
    ProjectJobMasterSerializer,
    ProjectPlanningStageSerializer,
    ProjectMilestoneSerializer,
    ProjectTaskSerializer,
    DepartmentAssignmentSerializer,
    ProjectIssueSerializer,
    ProjectDelaySerializer,
    CustomerChangeRequestSerializer,
    ProjectCostSerializer,
)

STANDARD_16_STAGE_DEFINITIONS = [
    {'num': 1, 'name': 'Order Confirmation & Kickoff', 'dept': 'crm', 'emp': 'Pravin Patel', 'desc': 'Sales Order confirmed, commercial terms agreed, customer PO received and internal kickoff.'},
    {'num': 2, 'name': 'Project Creation & Job Allocation', 'dept': 'project', 'emp': 'Bhavin Shah', 'desc': 'Job Number and Project File created. PM, Design lead and Shop supervisor assigned.'},
    {'num': 3, 'name': 'Design CAD 3D & GA Drawings', 'dept': 'designer', 'emp': 'Dharmesh Joshi', 'desc': 'Mechanical 3D modeling, General Arrangement (GA) drawing and nozzle orientation details.'},
    {'num': 4, 'name': 'Customer Design Approval & Sign-off', 'dept': 'designer', 'emp': 'Dharmesh Joshi', 'desc': 'GA Drawing submitted to customer engineering for official approval and revision lock.'},
    {'num': 5, 'name': 'BOM Finalization & Indent Release', 'dept': 'designer', 'emp': 'Dharmesh Joshi', 'desc': 'BOM exploded into raw plates, forgings, pipes, fasteners and bought-out components.'},
    {'num': 6, 'name': 'Material Planning & Stock Reservation', 'dept': 'store', 'emp': 'Hitesh Rawal', 'desc': 'Warehouse inventory check, stock reservation, and purchase requisition trigger.'},
    {'num': 7, 'name': 'Purchase Requisitions & Supplier POs', 'dept': 'purchase', 'emp': 'Vikram Solanki', 'desc': 'Supplier quotations, commercial comparison, PO release for steel plates, motors & seals.'},
    {'num': 8, 'name': 'Material Receipt & GRN Inspection', 'dept': 'store', 'emp': 'Hitesh Rawal', 'desc': 'Material arrival, Mill Test Certificate (MTC) verification, and GRN inward clearance.'},
    {'num': 9, 'name': 'Production Planning & Routing Card', 'dept': 'production', 'emp': 'Bhavin Shah', 'desc': 'Fabrication bay allocation, CNC cutting plans, welding procedure specification (WPS).'},
    {'num': 10, 'name': 'Raw Material Cutting & Rolling', 'dept': 'production', 'emp': 'Bhavin Shah', 'desc': 'Shell plate CNC plasma cutting, bevelling, and plate rolling machine operation.'},
    {'num': 11, 'name': 'Fabrication, Fit-up & Welding', 'dept': 'production', 'emp': 'Bhavin Shah', 'desc': 'Long-seam and circ-seam SAW/TIG welding, dish end fit-up and nozzle orientation welding.'},
    {'num': 12, 'name': 'Intermediate NDT & Quality Stage Inspection', 'dept': 'production', 'emp': 'Ketan Patel', 'desc': '100% Radiography Testing (RT), Dye Penetrant (DP) and Ultrasonic Testing (UT) on joints.'},
    {'num': 13, 'name': 'Assembly, Agitator & Drive Integration', 'dept': 'production', 'emp': 'Bhavin Shah', 'desc': 'Internal cooling coils, anchor agitator shaft alignment, mechanical seal and gearbox mounting.'},
    {'num': 14, 'name': 'Hydro Testing, FAT & Customer Inspection', 'dept': 'production', 'emp': 'Ketan Patel', 'desc': 'Hydrostatic pressure test at 12.5 Bar shell, hold for 4 hours and joint customer inspection.'},
    {'num': 15, 'name': 'Surface Finishing, Painting & Packaging', 'dept': 'production', 'emp': 'Bhavin Shah', 'desc': 'Internal electro-polishing to mirror finish (Ra < 0.4 um), external epoxy primer and PU paint.'},
    {'num': 16, 'name': 'Commercial Invoicing & Dispatch Handover', 'dept': 'accounting', 'emp': 'Pravin Patel', 'desc': 'Final tax invoice raised, dispatch clearance note issued, transit insurance and truck loading.'},
]


def auto_generate_16_stages(project_id):
    created_stages = []
    for s in STANDARD_16_STAGE_DEFINITIONS:
        stage_id = f"stg-{project_id.lower()}-{s['num']:02d}"
        obj, _ = ProjectPlanningStage.objects.update_or_create(
            id=stage_id,
            defaults={
                'project_id': project_id,
                'stage_number': s['num'],
                'name': s['name'],
                'department': s['dept'],
                'assigned_employee_name': s['emp'],
                'assignees': [{'name': s['emp'], 'department': s['dept']}],
                'status': 'completed' if s['num'] in [1, 2] else ('in_progress' if s['num'] == 3 else 'pending'),
                'progress': 100 if s['num'] in [1, 2] else (35 if s['num'] == 3 else 0),
                'description': s['desc'],
                'planned_duration_days': 7,
            }
        )
        created_stages.append(obj)
    return created_stages


class ProjectJobMasterViewSet(viewsets.ModelViewSet):
    queryset = ProjectJobMaster.objects.all().order_by('-created_at')
    serializer_class = ProjectJobMasterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id') or not data.get('project_number') and not data.get('projectNumber'):
            num_setting = NumberingSetting.objects.filter(doc_type='project').first()
            p_code = num_setting.generate_next_number(increment=True) if num_setting else f"PRJ-2026-{ProjectJobMaster.objects.count() + 1:04d}"
            j_code = p_code.replace('PRJ-', 'JOB-')
            data['id'] = p_code
            data['project_number'] = p_code
            data['job_number'] = j_code
        if not data.get('target_delivery_date') and not data.get('targetDeliveryDate'):
            data['target_delivery_date'] = data.get('deliveryDate') or data.get('delivery_date') or datetime.now().strftime('%Y-%m-%d')
        if not data.get('start_date') and not data.get('startDate'):
            data['start_date'] = datetime.now().strftime('%Y-%m-%d')
        if not data.get('project_manager_name') and not data.get('projectManagerName'):
            data['project_manager_name'] = data.get('projectManager') or 'Bhavin Shah'
        if not data.get('current_status') and not data.get('currentStatus'):
            data['current_status'] = data.get('status') or 'planning'

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()

        # Auto-create the 16 Standard Planning Stages!
        auto_generate_16_stages(project.id)

        return Response(ProjectJobMasterSerializer(project).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='generate-stages')
    def generate_stages(self, request, pk=None):
        project = self.get_object()
        stages = auto_generate_16_stages(project.id)
        return Response({
            'success': True,
            'message': f'Generated {len(stages)} planning stages for project {project.id}',
            'stages': ProjectPlanningStageSerializer(stages, many=True).data
        })


class ProjectPlanningStageViewSet(viewsets.ModelViewSet):
    queryset = ProjectPlanningStage.objects.all().order_by('stage_number')
    serializer_class = ProjectPlanningStageSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        project_id = self.request.query_params.get('projectId') or self.request.query_params.get('project_id')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'name' not in data or not data.get('name'):
            data['name'] = data.get('stage_name') or data.get('stageName') or 'Planning Stage'
        if 'department' not in data or not data.get('department'):
            data['department'] = data.get('responsible_department') or data.get('responsibleDepartment') or 'General'
        if 'project_id' not in data or not data.get('project_id'):
            data['project_id'] = data.get('projectId') or 'PRJ-DEFAULT'
        if 'stage_number' not in data or not data.get('stage_number'):
            data['stage_number'] = data.get('stageNumber') or 1
        if 'assigned_employee_name' not in data or not data.get('assigned_employee_name'):
            data['assigned_employee_name'] = data.get('responsible_employee') or data.get('responsibleEmployee') or ''
        if 'assignees' not in data or not data.get('assignees'):
            data['assignees'] = data.get('assigned_employees') or data.get('assignedEmployees') or []
        if 'progress' not in data or data.get('progress') is None:
            data['progress'] = data.get('progress_percent') or data.get('progressPercent') or 0
        if 'start_date' not in data or not data.get('start_date'):
            data['start_date'] = data.get('planned_start') or data.get('plannedStart') or ''
        if 'end_date' not in data or not data.get('end_date'):
            data['end_date'] = data.get('planned_end') or data.get('plannedEnd') or ''
        if 'description' not in data or not data.get('description'):
            data['description'] = data.get('remarks') or ''
        if 'id' not in data or not data.get('id'):
            data['id'] = f"STG-{data.get('project_id', 'PRJ')}-{uuid.uuid4().hex[:6]}"
            
        serializer = ProjectPlanningStageSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='complete')
    def mark_completed(self, request, pk=None):
        stage = self.get_object()
        stage.status = 'completed'
        stage.progress = 100
        stage.completed_by = request.data.get('completedBy') or request.data.get('completed_by', 'Current User')
        stage.completion_notes = request.data.get('notes') or request.data.get('completionNotes', '')
        stage.completed_at = datetime.now().strftime('%Y-%m-%d %I:%M %p')
        stage.save()
        return Response(ProjectPlanningStageSerializer(stage).data)


class ProjectMilestoneViewSet(viewsets.ModelViewSet):
    queryset = ProjectMilestone.objects.all().order_by('target_date')
    serializer_class = ProjectMilestoneSerializer
    permission_classes = [permissions.AllowAny]


class ProjectTaskViewSet(viewsets.ModelViewSet):
    queryset = ProjectTask.objects.all().order_by('-due_date')
    serializer_class = ProjectTaskSerializer
    permission_classes = [permissions.AllowAny]


class DepartmentAssignmentViewSet(viewsets.ModelViewSet):
    queryset = DepartmentAssignment.objects.all().order_by('department')
    serializer_class = DepartmentAssignmentSerializer
    permission_classes = [permissions.AllowAny]


class ProjectIssueViewSet(viewsets.ModelViewSet):
    queryset = ProjectIssue.objects.all().order_by('-created_date')
    serializer_class = ProjectIssueSerializer
    permission_classes = [permissions.AllowAny]


class ProjectDelayViewSet(viewsets.ModelViewSet):
    queryset = ProjectDelay.objects.all().order_by('-date')
    serializer_class = ProjectDelaySerializer
    permission_classes = [permissions.AllowAny]


class CustomerChangeRequestViewSet(viewsets.ModelViewSet):
    queryset = CustomerChangeRequest.objects.all().order_by('-request_date')
    serializer_class = CustomerChangeRequestSerializer
    permission_classes = [permissions.AllowAny]


class ProjectCostViewSet(viewsets.ModelViewSet):
    queryset = ProjectCost.objects.all().order_by('category')
    serializer_class = ProjectCostSerializer
    permission_classes = [permissions.AllowAny]
