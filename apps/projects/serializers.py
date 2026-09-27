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


class ProjectMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMilestone
        fields = [
            'id',
            'project_id',
            'title',
            'milestone_code',
            'target_date',
            'completion_date',
            'status',
            'payment_percentage',
            'payment_amount',
            'department',
        ]


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


class DepartmentAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentAssignment
        fields = [
            'id',
            'project_id',
            'department',
            'lead_person_id',
            'lead_person_name',
            'status',
            'notes',
        ]


class ProjectIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectIssue
        fields = [
            'id',
            'project_id',
            'title',
            'description',
            'department',
            'severity',
            'status',
            'reported_by',
            'assigned_to',
            'created_date',
            'resolved_date',
        ]


class ProjectDelaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDelay
        fields = [
            'id',
            'project_id',
            'reason',
            'department',
            'delayed_days',
            'impact',
            'mitigation_plan',
            'recorded_by',
            'date',
        ]


class CustomerChangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerChangeRequest
        fields = [
            'id',
            'project_id',
            'request_no',
            'title',
            'description',
            'impact_on_timeline_days',
            'impact_on_cost',
            'status',
            'approved_by',
            'request_date',
        ]


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
