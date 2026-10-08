from django.db import models
from django.utils import timezone



class ManufacturingJob(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    job_number = models.CharField(max_length=64, unique=True)
    project_id = models.CharField(max_length=64, blank=True, null=True)
    project_number = models.CharField(max_length=64, blank=True, null=True)
    customer_id = models.CharField(max_length=64, blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True)
    sales_order_id = models.CharField(max_length=64, blank=True, null=True)
    sales_order_number = models.CharField(max_length=64, blank=True)
    customer_po_number = models.CharField(max_length=64, blank=True)
    product_name = models.CharField(max_length=255)
    specification = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit = models.CharField(max_length=32, default='Nos')
    design_id = models.CharField(max_length=64, blank=True, null=True)
    design_revision = models.CharField(max_length=32, blank=True, default='R0')
    bom_id = models.CharField(max_length=64, blank=True, null=True)
    bom_revision = models.CharField(max_length=32, blank=True, default='R0')
    project_manager = models.CharField(max_length=128, blank=True)
    production_manager = models.CharField(max_length=128, blank=True)
    planned_start_date = models.DateField(null=True, blank=True)
    planned_completion_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    actual_completion_date = models.DateField(null=True, blank=True)
    production_progress = models.IntegerField(default=0)
    status = models.CharField(max_length=64, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.job_number} - {self.product_name}"


class ProductionPlan(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    plan_number = models.CharField(max_length=64, unique=True)
    job_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    project_id = models.CharField(max_length=64, blank=True)
    product_name = models.CharField(max_length=255, blank=True)
    required_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    bom_id = models.CharField(max_length=64, blank=True)
    bom_revision = models.CharField(max_length=32, blank=True)
    material_availability_status = models.CharField(max_length=64, default='Fully Available')
    planned_start_date = models.DateField(null=True, blank=True)
    planned_completion_date = models.DateField(null=True, blank=True)
    assigned_work_centers = models.JSONField(default=list, blank=True)
    planned_manpower_count = models.IntegerField(default=1)
    production_manager = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=64, default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plan_number} - {self.job_number}"


class WorkCenter(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    work_center_code = models.CharField(max_length=64, unique=True)
    work_center_name = models.CharField(max_length=255)
    department = models.CharField(max_length=128, blank=True)
    machine_name = models.CharField(max_length=255, blank=True)
    machine_number = models.CharField(max_length=64, blank=True)
    location = models.CharField(max_length=128, blank=True)
    capacity_per_day_hours = models.DecimalField(max_digits=6, decimal_places=2, default=8.0)
    available_hours = models.DecimalField(max_digits=6, decimal_places=2, default=8.0)
    efficiency_percent = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    supervisor_name = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=64, default='Available')

    def __str__(self):
        return f"{self.work_center_code} - {self.work_center_name}"


class RoutingOperation(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    operation_number = models.IntegerField(default=10)
    operation_name = models.CharField(max_length=255)
    sequence = models.IntegerField(default=1)
    work_center_code = models.CharField(max_length=64, blank=True)
    work_center_name = models.CharField(max_length=255, blank=True)
    machine_name = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=128, blank=True)
    planned_setup_minutes = models.IntegerField(default=0)
    planned_processing_minutes = models.IntegerField(default=0)
    total_planned_minutes = models.IntegerField(default=0)
    assigned_operator = models.CharField(max_length=128, blank=True)
    qc_required = models.BooleanField(default=True)
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=64, default='Pending')

    def __str__(self):
        return f"{self.operation_name} (Seq {self.sequence})"


class WorkOrder(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    work_order_number = models.CharField(max_length=64, unique=True)
    job_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    project_id = models.CharField(max_length=64, blank=True)
    customer_id = models.CharField(max_length=64, blank=True)
    customer_name = models.CharField(max_length=255, blank=True)
    sales_order_number = models.CharField(max_length=64, blank=True)
    design_revision = models.CharField(max_length=32, blank=True)
    bom_revision = models.CharField(max_length=32, blank=True)
    product_name = models.CharField(max_length=255)
    production_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    uom = models.CharField(max_length=32, default='Nos')
    planned_start_date = models.DateField(null=True, blank=True)
    planned_end_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    production_manager = models.CharField(max_length=128, blank=True)
    priority = models.CharField(max_length=32, default='Medium')
    status = models.CharField(max_length=64, default='Draft')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.work_order_number} ({self.status})"


class ProductionOrder(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    production_order_number = models.CharField(max_length=64, unique=True)
    work_order_id = models.CharField(max_length=64, blank=True)
    work_order_number = models.CharField(max_length=64, blank=True)
    job_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    product_name = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    bom_revision = models.CharField(max_length=32, blank=True)
    design_revision = models.CharField(max_length=32, blank=True)
    planned_start_date = models.DateField(null=True, blank=True)
    planned_end_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    production_manager = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=64, default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.production_order_number} - {self.job_number}"


class ProductionScheduleItem(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    schedule_number = models.CharField(max_length=64, unique=True)
    job_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    work_order_number = models.CharField(max_length=64, blank=True)
    operation_name = models.CharField(max_length=255)
    work_center_code = models.CharField(max_length=64, blank=True)
    work_center_name = models.CharField(max_length=255, blank=True)
    machine_name = models.CharField(max_length=255, blank=True)
    assigned_operator = models.CharField(max_length=128, blank=True)
    planned_start = models.DateTimeField(null=True, blank=True)
    planned_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    delay_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    status = models.CharField(max_length=64, default='Scheduled')

    def __str__(self):
        return f"{self.schedule_number} - {self.operation_name}"


class ProductionEntry(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    production_entry_number = models.CharField(max_length=64, unique=True)
    entry_date = models.DateField()
    job_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    work_order_number = models.CharField(max_length=64, blank=True)
    production_order_number = models.CharField(max_length=64, blank=True)
    operation_name = models.CharField(max_length=255)
    work_center_name = models.CharField(max_length=255, blank=True)
    machine_name = models.CharField(max_length=255, blank=True)
    operator_name = models.CharField(max_length=128, blank=True)
    start_time = models.CharField(max_length=32, blank=True)
    end_time = models.CharField(max_length=32, blank=True)
    planned_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    produced_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rejected_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rework_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    scrap_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    good_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    downtime_minutes = models.IntegerField(default=0)
    downtime_reason = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    created_by = models.CharField(max_length=128, blank=True)

    def save(self, *args, **kwargs):
        if self.good_quantity is None or self.good_quantity == 0:
            self.good_quantity = max(0, self.produced_quantity - self.rejected_quantity - self.scrap_quantity)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Production Entry'
        verbose_name_plural = 'Production Entries'

    def __str__(self):
        return f"{self.production_entry_number} ({self.operation_name})"


class WIPRecord(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    job_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    work_order_number = models.CharField(max_length=64, blank=True)
    production_order_number = models.CharField(max_length=64, blank=True)
    current_operation_name = models.CharField(max_length=255, blank=True)
    completed_operations_count = models.IntegerField(default=0)
    total_operations_count = models.IntegerField(default=0)
    wip_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    uom = models.CharField(max_length=32, default='Nos')
    location = models.CharField(max_length=128, blank=True)
    responsible_department = models.CharField(max_length=128, blank=True)
    start_date = models.DateField(null=True, blank=True)
    expected_completion_date = models.DateField(null=True, blank=True)
    delay_days = models.IntegerField(default=0)
    status = models.CharField(max_length=64, default='In Progress')

    class Meta:
        verbose_name = 'WIP Record'
        verbose_name_plural = 'WIP Records'

    def __str__(self):
        return f"WIP: {self.job_number} - {self.current_operation_name}"


class ProductionHold(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    hold_number = models.CharField(max_length=64, unique=True)
    job_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    work_order_number = models.CharField(max_length=64, blank=True)
    operation_name = models.CharField(max_length=255, blank=True)
    reason = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    expected_resume_date = models.DateField(null=True, blank=True)
    approved_by = models.CharField(max_length=128, blank=True)
    resume_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=64, default='Active Hold')
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.hold_number} - {self.job_number}"


class ReworkOrder(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    rework_number = models.CharField(max_length=64, unique=True)
    job_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    work_order_number = models.CharField(max_length=64, blank=True)
    production_entry_number = models.CharField(max_length=64, blank=True)
    operation_name = models.CharField(max_length=255, blank=True)
    item_code = models.CharField(max_length=64, blank=True)
    item_name = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    uom = models.CharField(max_length=32, default='Nos')
    reason = models.CharField(max_length=128, blank=True)
    responsible_department = models.CharField(max_length=128, blank=True)
    rework_instructions = models.TextField(blank=True)
    assigned_operator = models.CharField(max_length=128, blank=True)
    start_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=64, default='Open')

    def __str__(self):
        return f"{self.rework_number} - {self.item_name}"


class ProductionScrap(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    scrap_number = models.CharField(max_length=64, unique=True)
    entry_date = models.DateField()
    job_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    work_order_number = models.CharField(max_length=64, blank=True)
    production_order_number = models.CharField(max_length=64, blank=True)
    operation_name = models.CharField(max_length=255, blank=True)
    material_code = models.CharField(max_length=64, blank=True)
    material_name = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    uom = models.CharField(max_length=32, default='Kg')
    reason = models.TextField(blank=True)
    scrap_type = models.CharField(max_length=128, default='Cutting Scrap')
    operator_name = models.CharField(max_length=128, blank=True)
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.scrap_number} - {self.material_name}"


class FinishedGoodsItem(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    finished_goods_number = models.CharField(max_length=64, unique=True)
    job_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    work_order_number = models.CharField(max_length=64, blank=True)
    production_order_number = models.CharField(max_length=64, blank=True)
    product_name = models.CharField(max_length=255)
    specification = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    uom = models.CharField(max_length=32, default='Nos')
    serial_number = models.CharField(max_length=128, blank=True)
    batch_number = models.CharField(max_length=128, blank=True)
    warehouse_id = models.CharField(max_length=64, blank=True)
    warehouse_name = models.CharField(max_length=255, blank=True)
    location_bin = models.CharField(max_length=64, blank=True)
    completion_date = models.DateField()
    qc_status = models.CharField(max_length=64, default='QC Pending')
    status = models.CharField(max_length=64, default='Production Complete')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.finished_goods_number} - {self.product_name}"


class ProductionMaterialRequest(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    request_number = models.CharField(max_length=64, unique=True, verbose_name="Request / Issue Slip #")
    project_id = models.CharField(max_length=64, blank=True, default='')
    job_id = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    work_order_number = models.CharField(max_length=64, blank=True, default='')
    bom_number = models.CharField(max_length=64, blank=True, default='BOM-2026-001')
    bom_revision = models.CharField(max_length=20, blank=True, default='Rev-01')
    production_stage = models.CharField(max_length=150, blank=True, default='Fabrication & Welding')
    requested_by = models.CharField(max_length=150, blank=True, default='Production Supervisor')
    issued_to = models.CharField(max_length=150, blank=True, default='')
    issued_by = models.CharField(max_length=150, blank=True, default='Store Supervisor')
    request_date = models.DateField(null=True, blank=True)
    warehouse_id = models.CharField(max_length=64, default='WH-001')
    warehouse_name = models.CharField(max_length=200, blank=True, default='Raw Material Yard & Plate Store')
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    items = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=50, default='Fully Issued')
    remarks = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Production Material Request & Issue"
        verbose_name_plural = "Production Material Requests & Store Issues"

    def __str__(self):
        return f"{self.request_number} ({self.job_number or self.work_order_number})"


class DispatchOrder(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    dispatch_number = models.CharField(max_length=64, unique=True)
    dispatch_date = models.DateField(default=timezone.now)
    job_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    sales_order_number = models.CharField(max_length=64, blank=True, default='')
    work_order_number = models.CharField(max_length=64, blank=True)
    finished_goods_number = models.CharField(max_length=64, blank=True)
    customer_id = models.CharField(max_length=64, blank=True)
    customer_name = models.CharField(max_length=255)
    customer_address = models.TextField(blank=True)
    destination_city = models.CharField(max_length=128, blank=True)
    product_name = models.CharField(max_length=255)
    specification = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    uom = models.CharField(max_length=32, default='Nos')
    serial_number = models.CharField(max_length=128, blank=True)
    batch_number = models.CharField(max_length=128, blank=True)
    weight_mt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transporter_name = models.CharField(max_length=255, blank=True)
    vehicle_number = models.CharField(max_length=64, blank=True)
    lr_number = models.CharField(max_length=64, blank=True)
    driver_name = models.CharField(max_length=128, blank=True)
    driver_mobile = models.CharField(max_length=32, blank=True)
    e_way_bill_number = models.CharField(max_length=64, blank=True)
    invoice_number = models.CharField(max_length=64, blank=True)
    packaging_type = models.CharField(max_length=128, default='Wooden Saddle & Tarpaulin')
    dispatch_type = models.CharField(max_length=64, default='Road Freight (Trailer)')
    qc_clearance_by = models.CharField(max_length=128, blank=True, default='Quality Manager')
    dispatched_by = models.CharField(max_length=128, blank=True, default='Dispatch Officer')
    status = models.CharField(max_length=64, default='Ready for Dispatch')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dispatch Order & Delivery Challan'
        verbose_name_plural = 'Dispatch Orders & Delivery Challans'

    def __str__(self):
        return f"{self.dispatch_number} - {self.customer_name} ({self.status})"

