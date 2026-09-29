from django.contrib import admin
from .models import ProjectJobMaster, ProjectPlanningStage, ProjectMilestone, ProjectTask, DepartmentAssignment, ProjectIssue, ProjectDelay, CustomerChangeRequest, ProjectCost, ProjectDocument

@admin.register(ProjectJobMaster)
class ProjectJobMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_number', 'job_number', 'customer_id', 'customer_name', 'sales_order_id')
    search_fields = ('id', 'project_number', 'job_number', 'customer_id')
    list_filter = ('current_status', 'health_status', 'created_at', 'updated_at')

@admin.register(ProjectPlanningStage)
class ProjectPlanningStageAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_id', 'stage_number', 'name', 'department', 'assigned_employee_name')
    search_fields = ('id', 'project_id', 'name', 'assigned_employee_name')
    list_filter = ('status',)

@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_id', 'title', 'milestone_code', 'target_date', 'completion_date')
    search_fields = ('id', 'project_id', 'title', 'milestone_code')
    list_filter = ('status',)

@admin.register(ProjectTask)
class ProjectTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_id', 'task_number', 'title', 'department', 'assigned_to_id')
    search_fields = ('id', 'project_id', 'task_number', 'title')
    list_filter = ('status',)

@admin.register(DepartmentAssignment)
class DepartmentAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_id', 'department', 'lead_person_id', 'lead_person_name', 'status')
    search_fields = ('id', 'project_id', 'lead_person_id', 'lead_person_name')
    list_filter = ('status',)

@admin.register(ProjectIssue)
class ProjectIssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_id', 'title', 'department', 'severity', 'status')
    search_fields = ('id', 'project_id', 'title')
    list_filter = ('status',)

@admin.register(ProjectDelay)
class ProjectDelayAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_id', 'reason', 'department', 'delayed_days', 'recorded_by')
    search_fields = ('id', 'project_id')

@admin.register(CustomerChangeRequest)
class CustomerChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_id', 'request_no', 'title', 'impact_on_timeline_days', 'impact_on_cost')
    search_fields = ('id', 'project_id', 'request_no', 'title')
    list_filter = ('status',)

@admin.register(ProjectCost)
class ProjectCostAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_id', 'category', 'estimated_amount', 'actual_amount')
    search_fields = ('id', 'project_id')
    list_filter = ('category',)

@admin.register(ProjectDocument)
class ProjectDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_id', 'job_number', 'document_name', 'type', 'version', 'uploaded_by', 'upload_date')
    search_fields = ('id', 'project_id', 'job_number', 'document_name', 'uploaded_by')
    list_filter = ('type', 'department')

