from rest_framework import serializers
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
    ProjectDocument,
)


class ProjectPlanningStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPlanningStage
        fields = [
            'id',
            'project_id',
            'stage_number',
            'name',
            'department',
            'assigned_employee_name',
            'assignees',
            'status',
            'progress',
            'start_date',
            'end_date',
            'planned_duration_days',
            'actual_duration_days',
            'description',
            'completed_by',
            'completed_at',
            'completion_notes',
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'projectId' in data and 'project_id' not in data:
            data['project_id'] = data.pop('projectId')
        if 'stageNumber' in data and 'stage_number' not in data:
            data['stage_number'] = data.pop('stageNumber')
        if 'stageName' in data and 'name' not in data:
            data['name'] = data.pop('stageName')
        elif 'stage_name' in data and 'name' not in data:
            data['name'] = data.pop('stage_name')
        if 'responsibleDepartment' in data and 'department' not in data:
            data['department'] = data.pop('responsibleDepartment')
        elif 'responsible_department' in data and 'department' not in data:
            data['department'] = data.pop('responsible_department')
        if 'responsibleEmployee' in data and 'assigned_employee_name' not in data:
            data['assigned_employee_name'] = data.pop('responsibleEmployee')
        elif 'responsible_employee' in data and 'assigned_employee_name' not in data:
            data['assigned_employee_name'] = data.pop('responsible_employee')
        if 'assignedEmployees' in data and 'assignees' not in data:
            data['assignees'] = data.pop('assignedEmployees')
        elif 'assigned_employees' in data and 'assignees' not in data:
            data['assignees'] = data.pop('assigned_employees')
        if 'progressPercent' in data and 'progress' not in data:
            data['progress'] = data.pop('progressPercent')
        elif 'progress_percent' in data and 'progress' not in data:
            data['progress'] = data.pop('progress_percent')
        if 'plannedStart' in data and 'start_date' not in data:
            data['start_date'] = data.pop('plannedStart')
        elif 'planned_start' in data and 'start_date' not in data:
            data['start_date'] = data.pop('planned_start')
        if 'plannedEnd' in data and 'end_date' not in data:
            data['end_date'] = data.pop('plannedEnd')
        elif 'planned_end' in data and 'end_date' not in data:
            data['end_date'] = data.pop('planned_end')
        if 'remarks' in data and 'description' not in data:
            data['description'] = data.pop('remarks')
        if 'completedBy' in data and 'completed_by' not in data:
            data['completed_by'] = data.pop('completedBy')
        if 'completedAt' in data and 'completed_at' not in data:
            data['completed_at'] = data.pop('completedAt')
        if 'completionNotes' in data and 'completion_notes' not in data:
            data['completion_notes'] = data.pop('completionNotes')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {
            **ret,
            'stageNumber': ret.get('stage_number', 1),
            'stageName': ret.get('name', ''),
            'projectId': ret.get('project_id', ''),
            'jobNumber': ret.get('project_id', '').replace('PRJ-', 'JOB-'),
            'responsibleDepartment': ret.get('department', 'production'),
            'responsibleEmployee': ret.get('assigned_employee_name', ''),
            'assignedEmployees': ret.get('assignees', []),
            'progressPercent': ret.get('progress', 0),
            'plannedStart': ret.get('start_date', ''),
            'plannedEnd': ret.get('end_date', ''),
            'remarks': ret.get('description', ''),
            'completedBy': ret.get('completed_by', ''),
            'completedAt': ret.get('completed_at', ''),
            'completionNotes': ret.get('completion_notes', ''),
        }


class ProjectMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMilestone
        fields = [
            'id',
            'project_id',
            'project_number',
            'job_number',
            'title',
            'milestone_name',
            'milestone_code',
            'owner',
            'planned_date',
            'actual_date',
            'target_date',
            'completion_date',
            'status',
            'payment_percentage',
            'payment_amount',
            'department',
            'remarks',
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'projectId' in data and 'project_id' not in data:
            data['project_id'] = data.pop('projectId')
        if 'projectNumber' in data and 'project_number' not in data:
            data['project_number'] = data.pop('projectNumber')
        if 'jobNumber' in data and 'job_number' not in data:
            data['job_number'] = data.pop('jobNumber')
        if 'milestoneName' in data and 'milestone_name' not in data:
            data['milestone_name'] = data.pop('milestoneName')
        if 'plannedDate' in data and 'planned_date' not in data:
            data['planned_date'] = data.pop('plannedDate')
        if 'actualDate' in data and 'actual_date' not in data:
            data['actual_date'] = data.pop('actualDate')
        if 'targetDate' in data and 'target_date' not in data:
            data['target_date'] = data.pop('targetDate')
        if 'paymentPercentage' in data and 'payment_percentage' not in data:
            data['payment_percentage'] = data.pop('paymentPercentage')
        if 'paymentAmount' in data and 'payment_amount' not in data:
            data['payment_amount'] = data.pop('paymentAmount')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {
            **ret,
            'projectId': ret.get('project_id', ''),
            'projectNumber': ret.get('project_number', ''),
            'jobNumber': ret.get('job_number', ''),
            'milestoneName': ret.get('milestone_name') or ret.get('title', ''),
            'plannedDate': ret.get('planned_date', ''),
            'actualDate': ret.get('actual_date', ''),
            'targetDate': ret.get('target_date', ''),
            'paymentPercentage': ret.get('payment_percentage', 0),
            'paymentAmount': ret.get('payment_amount', 0),
        }


class ProjectDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDocument
        fields = '__all__'

    def to_internal_value(self, data):
        ret = {}
        ret['id'] = data.get('id') or f"DOC-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        ret['project_id'] = data.get('project_id') or data.get('projectId') or 'PRJ-GEN'
        ret['job_number'] = data.get('job_number') or data.get('jobNumber') or ''
        ret['document_name'] = data.get('document_name') or data.get('documentName') or 'Project Document'
        ret['type'] = data.get('type') or 'Drawing'
        ret['version'] = data.get('version') or 'v1.0'
        ret['uploaded_by'] = data.get('uploaded_by') or data.get('uploadedBy') or 'Super Admin'
        ret['department'] = data.get('department') or ''
        ret['related_record'] = data.get('related_record') or data.get('relatedRecord') or ''
        ret['description'] = data.get('description') or ''
        ret['file_size'] = data.get('file_size') or data.get('fileSize') or '1.5 MB'
        ret['file_url'] = data.get('file_url') or data.get('fileUrl') or ''
        ret['upload_date'] = data.get('upload_date') or data.get('uploadDate') or timezone.now().strftime('%Y-%m-%d')
        return ret

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['id'] = instance.id
        rep['projectId'] = instance.project_id
        rep['jobNumber'] = instance.job_number
        rep['documentName'] = instance.document_name
        rep['type'] = instance.type
        rep['version'] = instance.version
        rep['uploadedBy'] = instance.uploaded_by
        rep['department'] = instance.department
        rep['relatedRecord'] = instance.related_record
        rep['description'] = instance.description
        rep['fileSize'] = instance.file_size
        rep['fileUrl'] = instance.file_url
        rep['uploadDate'] = instance.upload_date or (instance.created_at.strftime('%Y-%m-%d') if instance.created_at else '')
        return rep


class ProjectTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTask
        fields = [
            'id',
            'project_id',
            'task_number',
            'title',
            'description',
            'department',
            'assigned_to_id',
            'assigned_to_name',
            'status',
            'priority',
            'due_date',
            'completion_date',
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'projectId' in data and 'project_id' not in data:
            data['project_id'] = data.pop('projectId')
        if 'taskNumber' in data and 'task_number' not in data:
            data['task_number'] = data.pop('taskNumber')
        if 'taskName' in data and 'title' not in data:
            data['title'] = data.pop('taskName')
        if 'assignedToName' in data and 'assigned_to_name' not in data:
            data['assigned_to_name'] = data.pop('assignedToName')
        elif 'assignedEmployee' in data and 'assigned_to_name' not in data:
            data['assigned_to_name'] = data.pop('assignedEmployee')
        if 'dueDate' in data and 'due_date' not in data:
            data['due_date'] = data.pop('dueDate')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {
            **ret,
            'projectId': ret.get('project_id', ''),
            'taskNumber': ret.get('task_number', ''),
            'taskName': ret.get('title', ''),
            'assignedToName': ret.get('assigned_to_name', ''),
            'assignedEmployee': ret.get('assigned_to_name', ''),
            'dueDate': ret.get('due_date', ''),
        }


class DepartmentAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentAssignment
        fields = '__all__'

    def to_internal_value(self, data):
        ret = {}
        proj = data.get('projectId') or data.get('project_id') or 'PRJ'
        dept = data.get('department') or 'DEPT'
        ret['id'] = data.get('id') or f"DA-{proj}-{dept}"
        ret['project_id'] = data.get('project_id') or data.get('projectId') or ''
        ret['department'] = data.get('department') or ''
        ret['lead_person_id'] = data.get('lead_person_id') or data.get('leadPersonId') or data.get('managerId') or ''
        ret['lead_person_name'] = data.get('lead_person_name') or data.get('leadPersonName') or data.get('manager') or data.get('assignedEmployee') or ''
        ret['status'] = data.get('status') or 'in_progress'
        ret['notes'] = data.get('notes') or data.get('responsibility') or data.get('remarks') or ''
        return ret

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['id'] = instance.id
        rep['projectId'] = instance.project_id
        rep['projectNumber'] = instance.project_id
        rep['jobNumber'] = instance.project_id
        rep['department'] = instance.department
        rep['manager'] = instance.lead_person_name or 'Unassigned'
        rep['assignedEmployee'] = instance.lead_person_name or 'Unassigned'
        rep['responsibility'] = instance.notes
        rep['startDate'] = ''
        rep['dueDate'] = ''
        rep['status'] = instance.status or 'in_progress'
        rep['priority'] = 'high'
        rep['remarks'] = instance.notes
        return rep


class ProjectIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectIssue
        fields = '__all__'


class ProjectDelaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDelay
        fields = '__all__'


class CustomerChangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerChangeRequest
        fields = '__all__'

    def to_internal_value(self, data):
        ret = {}
        cr_no = data.get('changeRequestNo') or data.get('change_request_no') or data.get('request_no') or f"CR-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        ret['id'] = data.get('id') or cr_no
        ret['project_id'] = data.get('project_id') or data.get('projectId') or 'PRJ-GEN'
        ret['project_number'] = data.get('project_number') or data.get('projectNumber') or ret['project_id']
        ret['job_number'] = data.get('job_number') or data.get('jobNumber') or ''
        ret['customer_name'] = data.get('customer_name') or data.get('customerName') or ''
        ret['change_request_no'] = cr_no
        ret['request_no'] = cr_no
        ret['requested_by'] = data.get('requested_by') or data.get('requestedBy') or 'Customer Representative'
        ret['title'] = data.get('title') or data.get('changeDescription') or data.get('change_description') or 'Customer Change Request'
        ret['description'] = data.get('description') or data.get('changeDescription') or data.get('change_description') or ''
        ret['change_description'] = data.get('change_description') or data.get('changeDescription') or ''
        ret['reason'] = data.get('reason') or ''
        ret['design_impact'] = data.get('design_impact') or data.get('designImpact') or ''
        ret['material_impact'] = data.get('material_impact') or data.get('materialImpact') or ''
        ret['cost_impact'] = float(data.get('cost_impact') or data.get('costImpact') or data.get('impact_on_cost') or 0)
        ret['impact_on_cost'] = ret['cost_impact']
        ret['timeline_impact_days'] = int(data.get('timeline_impact_days') or data.get('timelineImpactDays') or data.get('impact_on_timeline_days') or 0)
        ret['impact_on_timeline_days'] = ret['timeline_impact_days']
        ret['approval_status'] = data.get('approval_status') or data.get('approvalStatus') or data.get('status') or 'requested'
        ret['status'] = ret['approval_status']
        ret['approved_by'] = data.get('approved_by') or data.get('approvedBy') or ''
        ret['approved_date'] = data.get('approved_date') or data.get('approvedDate') or ''
        ret['request_date'] = data.get('request_date') or data.get('requestDate') or timezone.now().strftime('%Y-%m-%d')
        return ret

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        cr_no = instance.change_request_no or instance.request_no or instance.id
        rep['id'] = instance.id
        rep['changeRequestNo'] = cr_no
        rep['projectId'] = instance.project_id
        rep['projectNumber'] = instance.project_number or instance.project_id
        rep['jobNumber'] = instance.job_number
        rep['customerName'] = instance.customer_name
        rep['requestedBy'] = instance.requested_by
        rep['requestDate'] = instance.request_date or (instance.created_at.strftime('%Y-%m-%d') if instance.created_at else '')
        rep['changeDescription'] = instance.change_description or instance.description or instance.title
        rep['reason'] = instance.reason
        rep['designImpact'] = instance.design_impact
        rep['materialImpact'] = instance.material_impact
        rep['costImpact'] = float(instance.cost_impact or instance.impact_on_cost or 0)
        rep['timelineImpactDays'] = int(instance.timeline_impact_days or instance.impact_on_timeline_days or 0)
        rep['approvalStatus'] = instance.approval_status or instance.status or 'requested'
        rep['approvedBy'] = instance.approved_by
        rep['approvedDate'] = instance.approved_date
        return rep


class ProjectCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCost
        fields = [
            'id',
            'project_id',
            'category',
            'estimated_amount',
            'actual_amount',
            'notes',
        ]


class ProjectJobMasterSerializer(serializers.ModelSerializer):
    planning_stages = ProjectPlanningStageSerializer(many=True, read_only=True)
    milestones = ProjectMilestoneSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectJobMaster
        fields = [
            'id',
            'project_number',
            'job_number',
            'customer_id',
            'customer_name',
            'sales_order_id',
            'sales_order_number',
            'customer_po_number',
            'product_name',
            'product_code',
            'specification',
            'quantity',
            'unit',
            'order_value',
            'start_date',
            'target_delivery_date',
            'actual_delivery_date',
            'current_status',
            'progress_percent',
            'priority',
            'project_manager_id',
            'project_manager_name',
            'stage',
            'health_status',
            'linked_records',
            'planning_stages',
            'milestones',
        ]
