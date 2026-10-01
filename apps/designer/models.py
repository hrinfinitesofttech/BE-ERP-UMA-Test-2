from django.db import models
from django.utils import timezone


class DesignJob(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    design_job_number = models.CharField(max_length=64, unique=True)
    project_id = models.CharField(max_length=64)
    project_number = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    customer_id = models.CharField(max_length=64)
    customer_name = models.CharField(max_length=200)
    customer_po_number = models.CharField(max_length=100, blank=True, default='')
    sales_order_number = models.CharField(max_length=64, blank=True, default='')
    product_name = models.CharField(max_length=200)
    machine_type = models.CharField(max_length=100, blank=True, default='')
    quantity = models.IntegerField(default=1)
    delivery_date = models.CharField(max_length=50)
    design_manager = models.CharField(max_length=150, default='Dharmesh Joshi')
    assigned_designer = models.CharField(max_length=150, blank=True, default='')
    priority = models.CharField(max_length=30, default='high')
    required_date = models.CharField(max_length=50, blank=True, default='')
    status = models.CharField(max_length=50, default='in_progress')
    remarks = models.TextField(blank=True, default='')
    active_revision = models.CharField(max_length=30, default='REV-01')
    approved_by = models.CharField(max_length=150, blank=True, default='')
    approved_date = models.CharField(max_length=50, blank=True, default='')
    disapproved_by = models.CharField(max_length=150, blank=True, default='')
    disapproved_date = models.CharField(max_length=50, blank=True, default='')
    rejection_reason = models.TextField(blank=True, default='')
    approval_notes = models.TextField(blank=True, default='')
    created_date = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.design_job_number} - {self.product_name}"


class CustomerRequirement(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    design_job_id = models.CharField(max_length=64)
    project_id = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    customer_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150, blank=True, default='')
    contact_mobile = models.CharField(max_length=30, blank=True, default='')
    machine_name = models.CharField(max_length=200)
    machine_type = models.CharField(max_length=100, blank=True, default='')
    model = models.CharField(max_length=100, blank=True, default='')
    quantity = models.IntegerField(default=1)
    capacity = models.CharField(max_length=100, blank=True, default='')
    application = models.CharField(max_length=200, blank=True, default='')
    production_requirement = models.TextField(blank=True, default='')
    dimensions = models.CharField(max_length=200, blank=True, default='')
    material = models.CharField(max_length=150, blank=True, default='')
    power_requirement = models.CharField(max_length=100, blank=True, default='')
    speed = models.CharField(max_length=100, blank=True, default='')
    output = models.CharField(max_length=100, blank=True, default='')
    automation_level = models.CharField(max_length=100, blank=True, default='')
    control_system = models.CharField(max_length=150, blank=True, default='')
    safety_requirements = models.TextField(blank=True, default='')
    special_requirements = models.TextField(blank=True, default='')
    customer_drawing_url = models.CharField(max_length=255, blank=True, default='')
    customer_notes = models.TextField(blank=True, default='')
    designer_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Req: {self.machine_name} for {self.customer_name}"


class Drawing2D(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    design_job_id = models.CharField(max_length=64)
    drawing_number = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    revision = models.CharField(max_length=30, default='REV-00')
    status = models.CharField(max_length=50, default='approved')
    scale = models.CharField(max_length=30, blank=True, default='1:10')
    sheet_size = models.CharField(max_length=20, default='A1')
    prepared_by = models.CharField(max_length=150)
    checked_by = models.CharField(max_length=150, blank=True, default='')
    approved_by = models.CharField(max_length=150, blank=True, default='')
    release_date = models.CharField(max_length=50, blank=True, default='')
    file_url = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.drawing_number} - {self.title}"


class Design3DModel(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    design_job_id = models.CharField(max_length=64)
    model_number = models.CharField(max_length=100)
    model_name = models.CharField(max_length=200)
    software = models.CharField(max_length=50, default='SolidWorks')
    version = models.CharField(max_length=30, default='2026 SP1')
    status = models.CharField(max_length=50, default='approved')
    mass_kg = models.FloatField(default=0)
    volume_m3 = models.FloatField(default=0)
    modeled_by = models.CharField(max_length=150)
    file_url = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.model_number} - {self.model_name}"


class BOMHeader(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    bom_number = models.CharField(max_length=64, unique=True)
    design_job_id = models.CharField(max_length=64)
    project_id = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    active_revision = models.CharField(max_length=30, default='REV-01')
    status = models.CharField(max_length=50, default='approved')
    total_items = models.IntegerField(default=0)
    total_weight_kg = models.FloatField(default=0)
    total_estimated_cost = models.FloatField(default=0)
    prepared_by = models.CharField(max_length=150)
    approved_by = models.CharField(max_length=150, blank=True, default='')
    release_date = models.CharField(max_length=50, blank=True, default='')
    items = models.JSONField(default=list, blank=True)
    revisions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bom_number} ({self.status})"


class DesignRevisionLog(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    design_job_id = models.CharField(max_length=64)
    revision_number = models.CharField(max_length=30)
    reason = models.CharField(max_length=200)
    changes_summary = models.TextField()
    requested_by = models.CharField(max_length=150)
    approved_by = models.CharField(max_length=150, blank=True, default='')
    date = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.revision_number}: {self.reason}"


class TechnicalDocumentItem(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    design_job_id = models.CharField(max_length=64, blank=True, default='')
    project_id = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    doc_number = models.CharField(max_length=64, blank=True, default='')
    title = models.CharField(max_length=200, blank=True, default='')
    document_name = models.CharField(max_length=200, blank=True, default='')
    category = models.CharField(max_length=50, blank=True, default='Calculation')
    version = models.CharField(max_length=30, blank=True, default='v1.0')
    revision = models.CharField(max_length=30, blank=True, default='REV-00')
    uploaded_by = models.CharField(max_length=150, blank=True, default='Dharmesh Joshi')
    upload_date = models.CharField(max_length=50, blank=True, default='')
    access_permission = models.CharField(max_length=50, blank=True, default='public')
    file_size = models.CharField(max_length=50, blank=True, default='5.2 MB')
    file_url = models.CharField(max_length=255, blank=True, default='#')
    created_date = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.document_name or self.title}"


class DesignTask(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    design_job_id = models.CharField(max_length=64, blank=True, default='')
    project_id = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    task_name = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=200, blank=True, default='')
    machine_name = models.CharField(max_length=200, blank=True, default='')
    designer = models.CharField(max_length=150, default='Dharmesh Joshi')
    start_date = models.CharField(max_length=50, blank=True, default='')
    target_date = models.CharField(max_length=50, blank=True, default='')
    due_date = models.CharField(max_length=50, blank=True, default='')
    priority = models.CharField(max_length=30, default='high')
    estimated_hours = models.FloatField(default=16)
    actual_hours = models.FloatField(default=0)
    progress_percent = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default='pending')
    remarks = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.task_name} ({self.designer})"


class AssemblyDrawing(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    design_job_id = models.CharField(max_length=64, blank=True, default='')
    project_id = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    assembly_number = models.CharField(max_length=100)
    assembly_title = models.CharField(max_length=200)
    sub_assembly_code = models.CharField(max_length=100, blank=True, default='')
    parent_assembly_number = models.CharField(max_length=100, blank=True, default='')
    revision_number = models.CharField(max_length=30, default='REV-00')
    file_format = models.CharField(max_length=30, default='DWG')
    file_size = models.CharField(max_length=50, default='5.0 MB')
    file_url = models.CharField(max_length=255, blank=True, default='#')
    linked_bom_item_id = models.CharField(max_length=64, blank=True, default='')
    drawn_by = models.CharField(max_length=150, blank=True, default='')
    approved_by = models.CharField(max_length=150, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.assembly_number} - {self.assembly_title}"


