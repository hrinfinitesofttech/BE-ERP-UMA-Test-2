from django.db import models
from django.utils import timezone


class ProjectJobMaster(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    project_number = models.CharField(max_length=64, unique=True)
    job_number = models.CharField(max_length=64)
    customer_id = models.CharField(max_length=64)
    customer_name = models.CharField(max_length=200)
    sales_order_id = models.CharField(max_length=64, blank=True, null=True)
    sales_order_number = models.CharField(max_length=64, blank=True, default='')
    customer_po_number = models.CharField(max_length=100, blank=True, default='')
    product_name = models.CharField(max_length=200)
    product_code = models.CharField(max_length=100, blank=True, default='')
    specification = models.TextField(blank=True, default='')
    quantity = models.IntegerField(default=1)
    unit = models.CharField(max_length=30, default='Set')
    order_value = models.FloatField(default=0)
    start_date = models.CharField(max_length=50)
    target_delivery_date = models.CharField(max_length=50)
    actual_delivery_date = models.CharField(max_length=50, blank=True, null=True)
    current_status = models.CharField(max_length=50, default='planning')
    progress_percent = models.IntegerField(default=0)
    priority = models.CharField(max_length=30, default='high')
    project_manager_id = models.CharField(max_length=64, blank=True, default='')
    project_manager_name = models.CharField(max_length=150, blank=True, default='')
    stage = models.CharField(max_length=50, default='Kickoff & Planning')
    health_status = models.CharField(max_length=30, default='on_track')
    linked_records = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project_number} / {self.job_number} - {self.customer_name}"


class ProjectPlanningStage(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    project_id = models.CharField(max_length=64)
    stage_number = models.IntegerField()
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=50)
    assigned_employee_name = models.CharField(max_length=150, blank=True, default='')
    assignees = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=30, default='pending') # completed, in_progress, pending, delayed, skipped
    progress = models.IntegerField(default=0)
    start_date = models.CharField(max_length=50, blank=True, default='')
    end_date = models.CharField(max_length=50, blank=True, default='')
    planned_duration_days = models.IntegerField(default=7)
    actual_duration_days = models.IntegerField(default=0)
    description = models.TextField(blank=True, default='')
    completed_by = models.CharField(max_length=150, blank=True, null=True)
    completed_at = models.CharField(max_length=60, blank=True, null=True)
    completion_notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['stage_number']

    def __str__(self):
        return f"Stage {self.stage_number}: {self.name} ({self.status})"


class ProjectMilestone(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    project_id = models.CharField(max_length=64)
    project_number = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    title = models.CharField(max_length=200, blank=True, default='')
    milestone_name = models.CharField(max_length=200, blank=True, default='')
    milestone_code = models.CharField(max_length=50, blank=True, default='')
    owner = models.CharField(max_length=150, blank=True, default='')
    planned_date = models.CharField(max_length=50, blank=True, default='')
    actual_date = models.CharField(max_length=50, blank=True, null=True)
    target_date = models.CharField(max_length=50, blank=True, default='')
    completion_date = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=30, default='pending') # pending, in_progress, completed, delayed, achieved
    payment_percentage = models.FloatField(default=0)
    payment_amount = models.FloatField(default=0)
    department = models.CharField(max_length=50, blank=True, default='')
    remarks = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.milestone_name or self.title} ({self.status})"



class ProjectTask(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    project_id = models.CharField(max_length=64)
    task_number = models.CharField(max_length=64, blank=True, default='')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    department = models.CharField(max_length=50)
    assigned_to_id = models.CharField(max_length=64, blank=True, default='')
    assigned_to_name = models.CharField(max_length=150, blank=True, default='')
    status = models.CharField(max_length=30, default='pending') # pending, in_progress, completed, blocked
    priority = models.CharField(max_length=30, default='medium')
    due_date = models.CharField(max_length=50, blank=True, default='')
    completion_date = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.task_number} - {self.title}"


class DepartmentAssignment(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    project_id = models.CharField(max_length=64)
    department = models.CharField(max_length=50)
    lead_person_id = models.CharField(max_length=64, blank=True, default='')
    lead_person_name = models.CharField(max_length=150, blank=True, default='')
    status = models.CharField(max_length=30, default='assigned')
    notes = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.department} -> {self.lead_person_name}"


class ProjectIssue(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    project_id = models.CharField(max_length=64)
    project_number = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    issue_no = models.CharField(max_length=64, blank=True, default='')
    title = models.CharField(max_length=200, blank=True, default='')
    issue_type = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField(blank=True, default='')
    department = models.CharField(max_length=50, blank=True, default='Production')
    severity = models.CharField(max_length=30, default='medium') # low, medium, high, critical
    status = models.CharField(max_length=30, default='open') # open, in_progress, resolved, closed
    reported_by = models.CharField(max_length=150, blank=True, default='Super Admin')
    assigned_to = models.CharField(max_length=150, blank=True, default='')
    reported_date = models.CharField(max_length=50, blank=True, default='')
    created_date = models.CharField(max_length=50, blank=True, default='')
    resolved_date = models.CharField(max_length=50, blank=True, null=True)
    resolution = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.issue_no or self.id}: {self.title or self.issue_type} ({self.status})"


class ProjectDelay(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    project_id = models.CharField(max_length=64)
    project_number = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    delay_no = models.CharField(max_length=64, blank=True, default='')
    reason = models.CharField(max_length=255, blank=True, default='')
    delay_reason = models.CharField(max_length=255, blank=True, default='')
    department = models.CharField(max_length=50, blank=True, default='project')
    task_name = models.CharField(max_length=200, blank=True, default='')
    delayed_days = models.IntegerField(default=0)
    delay_days = models.IntegerField(default=0)
    impact = models.TextField(blank=True, default='')
    mitigation_plan = models.TextField(blank=True, default='')
    corrective_action = models.TextField(blank=True, default='')
    recorded_by = models.CharField(max_length=150, blank=True, default='Super Admin')
    responsible_person = models.CharField(max_length=150, blank=True, default='')
    date = models.CharField(max_length=50, blank=True, default='')
    start_date = models.CharField(max_length=50, blank=True, default='')
    original_delivery_date = models.CharField(max_length=50, blank=True, default='')
    expected_delivery_date = models.CharField(max_length=50, blank=True, default='')
    status = models.CharField(max_length=30, default='open')
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.delay_no or self.id}: {self.delay_reason or self.reason} ({self.delay_days or self.delayed_days} days)"



class CustomerChangeRequest(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    project_id = models.CharField(max_length=64)
    project_number = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    customer_name = models.CharField(max_length=200, blank=True, default='')
    change_request_no = models.CharField(max_length=64, blank=True, default='')
    request_no = models.CharField(max_length=64, blank=True, default='')
    requested_by = models.CharField(max_length=150, blank=True, default='Customer Representative')
    title = models.CharField(max_length=200, blank=True, default='')
    description = models.TextField(blank=True, default='')
    change_description = models.TextField(blank=True, default='')
    reason = models.TextField(blank=True, default='')
    design_impact = models.TextField(blank=True, default='')
    material_impact = models.TextField(blank=True, default='')
    cost_impact = models.FloatField(default=0)
    timeline_impact_days = models.IntegerField(default=0)
    impact_on_timeline_days = models.IntegerField(default=0)
    impact_on_cost = models.FloatField(default=0)
    approval_status = models.CharField(max_length=30, default='requested') # requested, under_review, approved, rejected, implemented
    status = models.CharField(max_length=30, default='pending')
    approved_by = models.CharField(max_length=150, blank=True, null=True)
    approved_date = models.CharField(max_length=50, blank=True, default='')
    request_date = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)

    def __str__(self):
        return f"{self.change_request_no or self.request_no or self.id} - {self.customer_name or self.title}"


class ProjectCost(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    project_id = models.CharField(max_length=64)
    category = models.CharField(max_length=50) # material, labor, machining, consumables, logistics, other
    estimated_amount = models.FloatField(default=0)
    actual_amount = models.FloatField(default=0)
    notes = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.category}: est {self.estimated_amount} / act {self.actual_amount}"


class ProjectDocument(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    project_id = models.CharField(max_length=64)
    job_number = models.CharField(max_length=64, blank=True, default='')
    document_name = models.CharField(max_length=200)
    type = models.CharField(max_length=50, default='Drawing')
    version = models.CharField(max_length=50, default='v1.0')
    uploaded_by = models.CharField(max_length=150, blank=True, default='')
    department = models.CharField(max_length=50, blank=True, default='')
    related_record = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField(blank=True, default='')
    file_size = models.CharField(max_length=50, blank=True, default='1.5 MB')
    file_url = models.CharField(max_length=255, blank=True, default='')
    upload_date = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)

    def __str__(self):
        return f"{self.document_name} ({self.version})"

