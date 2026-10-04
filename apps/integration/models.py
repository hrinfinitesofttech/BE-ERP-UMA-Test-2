from django.db import models
from django.utils import timezone


class ApprovalItem(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    category = models.CharField(max_length=64)
    title = models.CharField(max_length=255)
    record_number = models.CharField(max_length=64)
    requester_name = models.CharField(max_length=128)
    requester_role = models.CharField(max_length=128, blank=True)
    request_date = models.CharField(max_length=50, blank=True, default='')
    amount = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    related_job_number = models.CharField(max_length=64, blank=True)
    remarks = models.TextField(blank=True)
    urgency = models.CharField(max_length=32, default='Normal')
    status = models.CharField(max_length=32, default='Pending')
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.record_number}) - {self.status}"


class ERPAlertItem(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    module = models.CharField(max_length=64)
    severity = models.CharField(max_length=32, default='Info')
    title = models.CharField(max_length=255)
    description = models.TextField()
    target_url = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, blank=True, null=True)
    action_required = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.severity}] {self.title}"


# 1. Job 360 Overview / Master Traceability Record
class Job360Overview(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    job_number = models.CharField(max_length=64, unique=True)
    project_id = models.CharField(max_length=64, blank=True, default='')
    sales_order_number = models.CharField(max_length=64, blank=True, default='')
    customer_po_number = models.CharField(max_length=100, blank=True, default='')
    customer_id = models.CharField(max_length=64, blank=True, default='')
    customer_name = models.CharField(max_length=200)
    product_name = models.CharField(max_length=200)
    specification = models.TextField(blank=True, default='')
    quantity = models.IntegerField(default=1)
    unit = models.CharField(max_length=30, default='Set')
    order_value = models.FloatField(default=0)
    start_date = models.CharField(max_length=50, blank=True, default='')
    target_delivery_date = models.CharField(max_length=50, blank=True, default='')
    actual_delivery_date = models.CharField(max_length=50, blank=True, null=True)
    current_status = models.CharField(max_length=50, default='planning')
    progress_percent = models.IntegerField(default=0)
    priority = models.CharField(max_length=30, default='high')
    project_manager = models.CharField(max_length=150, blank=True, default='Bhavin Shah')
    steps = models.JSONField(default=list, blank=True)
    linked_records = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Job 360 Overview'
        verbose_name_plural = 'Job 360 Overviews'

    def __str__(self):
        return f"Job 360: {self.job_number} - {self.customer_name}"


# 2. Executive Dashboard KPI & Analytics
class ExecutiveDashboardKPI(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    kpi_name = models.CharField(max_length=150)
    category = models.CharField(max_length=100, default='Revenue')
    current_value = models.FloatField(default=0)
    target_value = models.FloatField(default=0)
    unit = models.CharField(max_length=30, default='₹')
    trend_percentage = models.FloatField(default=0)
    period = models.CharField(max_length=50, default='Monthly')
    meta_data = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Executive Dashboard KPI'
        verbose_name_plural = 'Executive Dashboard KPIs'

    def __str__(self):
        return f"{self.kpi_name}: {self.current_value} / {self.target_value} ({self.period})"


# 5. Customer 360 Profile Summary
class Customer360Summary(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    customer_id = models.CharField(max_length=64, unique=True)
    customer_name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100, blank=True, default='')
    total_revenue_billed = models.FloatField(default=0)
    total_orders_count = models.IntegerField(default=0)
    active_projects_count = models.IntegerField(default=0)
    outstanding_receivable = models.FloatField(default=0)
    amc_contracts_count = models.IntegerField(default=0)
    satisfaction_score = models.FloatField(default=4.8)
    summary_data = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Customer 360 Summary'
        verbose_name_plural = 'Customer 360 Summaries'

    def __str__(self):
        return f"Customer 360: {self.customer_name}"


# 6. Supplier 360 Profile Summary
class Supplier360Summary(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    supplier_id = models.CharField(max_length=64, unique=True)
    supplier_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True, default='')
    total_purchase_spend = models.FloatField(default=0)
    purchase_orders_count = models.IntegerField(default=0)
    on_time_delivery_rate = models.FloatField(default=95.0)
    quality_acceptance_rate = models.FloatField(default=98.5)
    outstanding_payable = models.FloatField(default=0)
    summary_data = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Supplier 360 Summary'
        verbose_name_plural = 'Supplier 360 Summaries'

    def __str__(self):
        return f"Supplier 360: {self.supplier_name}"


# 7. Item / Material 360 Profile Summary
class ItemMaterial360Summary(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    item_code = models.CharField(max_length=64, unique=True)
    item_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True, default='')
    current_stock = models.FloatField(default=0)
    reorder_level = models.FloatField(default=10)
    unit = models.CharField(max_length=30, default='KG')
    average_unit_cost = models.FloatField(default=0)
    total_stock_value = models.FloatField(default=0)
    allocated_to_jobs = models.FloatField(default=0)
    primary_suppliers = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Material 360 Summary'
        verbose_name_plural = 'Material 360 Summaries'

    def __str__(self):
        return f"Item 360: {self.item_code} - {self.item_name}"


# 8. Employee 360 Profile Summary
class Employee360Summary(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    employee_id = models.CharField(max_length=64, unique=True)
    employee_name = models.CharField(max_length=150)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    active_tasks_count = models.IntegerField(default=0)
    completed_projects_count = models.IntegerField(default=0)
    attendance_rate = models.FloatField(default=96.0)
    performance_rating = models.FloatField(default=4.5)
    summary_data = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Employee 360 Summary'
        verbose_name_plural = 'Employee 360 Summaries'

    def __str__(self):
        return f"Employee 360: {self.employee_name} ({self.employee_id})"


# 9. Global Activity Trail Log
class GlobalActivityLog(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    module = models.CharField(max_length=64)
    action = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=64, blank=True, default='')
    details = models.TextField(blank=True, default='')
    user_name = models.CharField(max_length=150, default='Super Admin')
    user_role = models.CharField(max_length=100, default='Admin')
    ip_address = models.CharField(max_length=50, blank=True, default='127.0.0.1')
    date = models.CharField(max_length=50, blank=True, default='')
    time = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Global Activity Log'
        verbose_name_plural = 'Global Activity Logs'

    def __str__(self):
        return f"[{self.module}] {self.action} by {self.user_name} ({self.date})"


# 10. ERP Report Center Definition & Cache
class ERPReportCenterItem(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    report_code = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100, default='Operations')
    description = models.TextField(blank=True, default='')
    format_supported = models.CharField(max_length=100, default='PDF, Excel, CSV')
    frequency = models.CharField(max_length=50, default='On-Demand')
    last_generated_at = models.CharField(max_length=50, blank=True, default='')
    generated_by = models.CharField(max_length=150, default='Super Admin')
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)

    class Meta:
        verbose_name = 'Report Center Item'
        verbose_name_plural = 'Report Center Items'

    def __str__(self):
        return f"{self.report_code}: {self.title}"


# 11. Job Profitability Analysis Record
class JobProfitabilityRecord(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    job_number = models.CharField(max_length=64, unique=True)
    customer_name = models.CharField(max_length=200)
    product_name = models.CharField(max_length=200)
    contract_price = models.FloatField(default=0)
    material_cost = models.FloatField(default=0)
    labor_cost = models.FloatField(default=0)
    machining_cost = models.FloatField(default=0)
    consumables_cost = models.FloatField(default=0)
    overhead_cost = models.FloatField(default=0)
    total_cost = models.FloatField(default=0)
    net_profit = models.FloatField(default=0)
    profit_margin_percent = models.FloatField(default=0)
    status = models.CharField(max_length=50, default='in_progress')
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Job Profitability Record'
        verbose_name_plural = 'Job Profitability Records'

    def __str__(self):
        return f"Profitability: {self.job_number} (Margin: {self.profit_margin_percent}%)"
