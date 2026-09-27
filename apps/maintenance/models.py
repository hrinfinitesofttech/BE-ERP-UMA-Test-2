from django.db import models


class InternalAsset(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    asset_code = models.CharField(max_length=64, unique=True)
    asset_name = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=64, default='Machine')
    category = models.CharField(max_length=128, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    model = models.CharField(max_length=128, blank=True)
    serial_number = models.CharField(max_length=128, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_supplier = models.CharField(max_length=255, blank=True)
    purchase_invoice = models.CharField(max_length=128, blank=True)
    purchase_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    installation_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=128, blank=True)
    department = models.CharField(max_length=128, blank=True)
    responsible_person = models.CharField(max_length=128, blank=True)
    warranty_start = models.DateField(null=True, blank=True)
    warranty_end = models.DateField(null=True, blank=True)
    amc_status = models.CharField(max_length=64, default='None')
    amc_start = models.DateField(null=True, blank=True)
    amc_end = models.DateField(null=True, blank=True)
    maintenance_frequency = models.CharField(max_length=64, default='Monthly')
    criticality = models.CharField(max_length=32, default='Medium')
    status = models.CharField(max_length=64, default='Active')
    documents = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.asset_code} - {self.asset_name}"


class CustomerMachine(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    customer_machine_id = models.CharField(max_length=64, unique=True)
    customer_id = models.CharField(max_length=64, blank=True)
    customer_name = models.CharField(max_length=255)
    project_id = models.CharField(max_length=64, blank=True)
    project_name = models.CharField(max_length=255, blank=True)
    job_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    sales_order_id = models.CharField(max_length=64, blank=True)
    customer_po = models.CharField(max_length=64, blank=True)
    dispatch_number = models.CharField(max_length=64, blank=True)
    installation_number = models.CharField(max_length=64, blank=True)
    machine_name = models.CharField(max_length=255)
    machine_model = models.CharField(max_length=128, blank=True)
    serial_number = models.CharField(max_length=128, blank=True)
    manufacturing_date = models.DateField(null=True, blank=True)
    installation_date = models.DateField(null=True, blank=True)
    commissioning_date = models.DateField(null=True, blank=True)
    warranty_start = models.DateField(null=True, blank=True)
    warranty_end = models.DateField(null=True, blank=True)
    amc_start = models.DateField(null=True, blank=True)
    amc_end = models.DateField(null=True, blank=True)
    machine_location = models.CharField(max_length=255, blank=True)
    customer_contact = models.CharField(max_length=128, blank=True)
    contact_phone = models.CharField(max_length=32, blank=True)
    contact_email = models.CharField(max_length=128, blank=True)
    service_engineer = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=64, default='Installed & Operational')
    documents = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.customer_machine_id} - {self.machine_name} ({self.customer_name})"


class ServiceRequest(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    request_number = models.CharField(max_length=64, unique=True)
    request_date = models.DateField()
    origin = models.CharField(max_length=64, default='Customer')
    customer_id = models.CharField(max_length=64, blank=True)
    customer_name = models.CharField(max_length=255)
    customer_machine_id = models.CharField(max_length=64, blank=True)
    machine_name = models.CharField(max_length=255, blank=True)
    serial_number = models.CharField(max_length=128, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    contact_person = models.CharField(max_length=128, blank=True)
    mobile = models.CharField(max_length=32, blank=True)
    email = models.CharField(max_length=128, blank=True)
    complaint_type = models.CharField(max_length=128, blank=True)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=32, default='Medium')
    warranty_status = models.CharField(max_length=64, default='Under Warranty')
    amc_status = models.CharField(max_length=64, default='No AMC')
    preferred_visit_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    attachments = models.JSONField(default=list, blank=True)
    assigned_department = models.CharField(max_length=128, blank=True)
    assigned_technician_id = models.CharField(max_length=64, blank=True)
    assigned_technician_name = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=64, default='New')
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.request_number} - {self.customer_name} ({self.status})"


class PreventiveMaintenancePlan(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    plan_number = models.CharField(max_length=64, unique=True)
    asset_id = models.CharField(max_length=64, blank=True)
    asset_name = models.CharField(max_length=255)
    customer_machine_id = models.CharField(max_length=64, blank=True)
    customer_name = models.CharField(max_length=255, blank=True)
    maintenance_type = models.CharField(max_length=128, default='Preventive')
    frequency = models.CharField(max_length=64, default='Monthly')
    start_date = models.DateField()
    next_due_date = models.DateField()
    checklist = models.JSONField(default=list, blank=True)
    responsible_technician_id = models.CharField(max_length=64, blank=True)
    responsible_technician_name = models.CharField(max_length=128, blank=True)
    estimated_duration_hours = models.DecimalField(max_digits=6, decimal_places=2, default=2.0)
    required_spare_parts = models.JSONField(default=list, blank=True)
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=64, default='Active')

    def __str__(self):
        return f"{self.plan_number} - {self.asset_name}"


class BreakdownRecord(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    breakdown_number = models.CharField(max_length=64, unique=True)
    asset_type = models.CharField(max_length=64, default='Internal Asset')
    asset_id = models.CharField(max_length=64, blank=True)
    asset_name = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=128, blank=True)
    customer_id = models.CharField(max_length=64, blank=True)
    customer_name = models.CharField(max_length=255, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    breakdown_date = models.DateField()
    breakdown_time = models.CharField(max_length=32, blank=True)
    reported_by = models.CharField(max_length=128, blank=True)
    problem = models.TextField()
    severity = models.CharField(max_length=32, default='Medium')
    initial_diagnosis = models.TextField(blank=True)
    assigned_technician_id = models.CharField(max_length=64, blank=True)
    assigned_technician_name = models.CharField(max_length=128, blank=True)
    response_time_minutes = models.IntegerField(default=0)
    resolution_time_minutes = models.IntegerField(default=0)
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    spare_parts_used = models.JSONField(default=list, blank=True)
    downtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    status = models.CharField(max_length=64, default='Reported')
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.breakdown_number} - {self.asset_name} ({self.status})"


class ServiceVisit(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    visit_number = models.CharField(max_length=64, unique=True)
    service_request_id = models.CharField(max_length=64, blank=True)
    request_number = models.CharField(max_length=64, blank=True)
    customer_id = models.CharField(max_length=64, blank=True)
    customer_name = models.CharField(max_length=255)
    machine_name = models.CharField(max_length=255, blank=True)
    serial_number = models.CharField(max_length=128, blank=True)
    technician_id = models.CharField(max_length=64, blank=True)
    technician_name = models.CharField(max_length=128, blank=True)
    visit_date = models.DateField()
    start_time = models.CharField(max_length=32, blank=True)
    end_time = models.CharField(max_length=32, blank=True)
    travel_time_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    customer_contact = models.CharField(max_length=128, blank=True)
    problem = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    work_performed = models.TextField(blank=True)
    parts_used = models.JSONField(default=list, blank=True)
    labour_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    status = models.CharField(max_length=64, default='Scheduled')
    customer_remarks = models.TextField(blank=True)
    customer_signature = models.BooleanField(default=False)
    attachments = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.visit_number} - {self.customer_name}"


class AMCContract(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    amc_number = models.CharField(max_length=64, unique=True)
    customer_id = models.CharField(max_length=64, blank=True)
    customer_name = models.CharField(max_length=255)
    customer_machine_id = models.CharField(max_length=64, blank=True)
    machine_name = models.CharField(max_length=255, blank=True)
    serial_number = models.CharField(max_length=128, blank=True)
    contract_start = models.DateField()
    contract_end = models.DateField()
    contract_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    billing_frequency = models.CharField(max_length=64, default='Yearly')
    total_visits_included = models.IntegerField(default=4)
    visits_completed = models.IntegerField(default=0)
    preventive_visits = models.IntegerField(default=4)
    breakdown_support = models.BooleanField(default=True)
    parts_included = models.BooleanField(default=False)
    labour_included = models.BooleanField(default=True)
    response_time_hours = models.IntegerField(default=24)
    terms_and_conditions = models.TextField(blank=True)
    assigned_technician_id = models.CharField(max_length=64, blank=True)
    assigned_technician_name = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=64, default='Active')

    def __str__(self):
        return f"{self.amc_number} - {self.customer_name}"
