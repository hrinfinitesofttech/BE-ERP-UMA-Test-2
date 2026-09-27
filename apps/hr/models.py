from django.db import models


class Designation(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    designation_code = models.CharField(max_length=64, unique=True)
    designation_name = models.CharField(max_length=128)
    department = models.CharField(max_length=128)
    level = models.IntegerField(default=1)
    reporting_designation = models.CharField(max_length=128, blank=True)
    job_description = models.TextField(blank=True)
    responsibilities = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=32, default='Active')

    def __str__(self):
        return f"{self.designation_name} ({self.department})"


class EmployeeDocument(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    document_type = models.CharField(max_length=64)
    document_number = models.CharField(max_length=128)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    file_url = models.CharField(max_length=512, blank=True)
    verification_status = models.CharField(max_length=32, default='Pending')
    verified_by = models.CharField(max_length=128, blank=True)
    verified_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee_name} - {self.document_type}"


class ShiftMaster(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    shift_name = models.CharField(max_length=128)
    start_time = models.CharField(max_length=32)
    end_time = models.CharField(max_length=32)
    grace_period_minutes = models.IntegerField(default=15)
    break_duration_minutes = models.IntegerField(default=60)
    late_rule = models.TextField(blank=True)
    early_checkout_rule = models.TextField(blank=True)
    overtime_rule = models.TextField(blank=True)
    weekly_off = models.CharField(max_length=64, default='Sunday')
    status = models.CharField(max_length=32, default='Active')

    def __str__(self):
        return f"{self.shift_name} ({self.start_time} - {self.end_time})"


class AttendanceRecord(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    department = models.CharField(max_length=128)
    date = models.DateField()
    shift_name = models.CharField(max_length=128, blank=True)
    check_in = models.CharField(max_length=32, blank=True)
    check_out = models.CharField(max_length=32, blank=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    late_minutes = models.IntegerField(default=0)
    early_checkout_minutes = models.IntegerField(default=0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    status = models.CharField(max_length=64, default='Present')
    source = models.CharField(max_length=64, default='Biometric System')
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.employee_name} ({self.status})"


class LeaveRequest(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    leave_number = models.CharField(max_length=64, unique=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    department = models.CharField(max_length=128)
    leave_type_id = models.CharField(max_length=64, blank=True)
    leave_name = models.CharField(max_length=128)
    from_date = models.DateField()
    to_date = models.DateField()
    number_of_days = models.DecimalField(max_digits=5, decimal_places=1, default=1.0)
    is_half_day = models.BooleanField(default=False)
    reason = models.TextField()
    attachment_url = models.CharField(max_length=512, blank=True)
    reporting_manager = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=64, default='Pending')
    applied_date = models.DateField()
    approved_by = models.CharField(max_length=128, blank=True)
    approved_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-applied_date']

    def __str__(self):
        return f"{self.leave_number} - {self.employee_name} ({self.status})"


class WFHRequest(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    wfh_number = models.CharField(max_length=64, unique=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    department = models.CharField(max_length=128)
    from_date = models.DateField()
    to_date = models.DateField()
    number_of_days = models.DecimalField(max_digits=5, decimal_places=1, default=1.0)
    reason = models.TextField()
    work_description = models.TextField(blank=True)
    reporting_manager = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=64, default='Pending')

    def __str__(self):
        return f"{self.wfh_number} - {self.employee_name}"


class MissedPunchRequest(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    request_number = models.CharField(max_length=64, unique=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    date = models.DateField()
    missing_punch_type = models.CharField(max_length=32, default='Check-In')
    requested_time = models.CharField(max_length=32)
    reason = models.TextField()
    reporting_manager = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=64, default='Pending')

    def __str__(self):
        return f"{self.request_number} - {self.employee_name}"


class AttendanceRegularization(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    regularization_no = models.CharField(max_length=64, unique=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    date = models.DateField()
    original_status = models.CharField(max_length=64, default='Absent')
    requested_status = models.CharField(max_length=64, default='Present')
    original_check_in = models.CharField(max_length=32, blank=True)
    original_check_out = models.CharField(max_length=32, blank=True)
    corrected_check_in = models.CharField(max_length=32, blank=True)
    corrected_check_out = models.CharField(max_length=32, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=64, default='Pending')

    def __str__(self):
        return f"{self.regularization_no} - {self.employee_name}"


class OvertimeRecord(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    overtime_no = models.CharField(max_length=64, unique=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    department = models.CharField(max_length=128)
    date = models.DateField()
    regular_hours = models.DecimalField(max_digits=5, decimal_places=2, default=8.0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    reason = models.TextField(blank=True)
    overtime_rate_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.5)
    overtime_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    approved_by = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=64, default='Pending')

    def __str__(self):
        return f"{self.overtime_no} - {self.employee_name} ({self.overtime_hours}h)"


class EarlyCheckoutRequest(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    request_number = models.CharField(max_length=64, unique=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    date = models.DateField()
    shift_name = models.CharField(max_length=128, blank=True)
    expected_checkout = models.CharField(max_length=32, blank=True)
    requested_checkout = models.CharField(max_length=32, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=64, default='Pending')

    def __str__(self):
        return f"{self.request_number} - {self.employee_name}"


class SalaryComponent(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    component_code = models.CharField(max_length=64, unique=True)
    component_name = models.CharField(max_length=128)
    component_type = models.CharField(max_length=64, default='Earning')
    calculation_type = models.CharField(max_length=64, default='Fixed Amount')
    percentage_or_formula = models.CharField(max_length=128, blank=True)
    is_taxable = models.BooleanField(default=True)
    is_statutory = models.BooleanField(default=False)
    status = models.CharField(max_length=32, default='Active')

    def __str__(self):
        return f"{self.component_name} ({self.component_type})"


class SalaryStructure(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    structure_name = models.CharField(max_length=128)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    effective_from = models.DateField()
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    hra = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    conveyance_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    employee_pf = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    employee_esi = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    professional_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    tds_monthly = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    employer_pf = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    employer_esi = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_ctc = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    status = models.CharField(max_length=32, default='Active')

    def __str__(self):
        return f"{self.structure_name} - {self.employee_name}"


class PayrollRecord(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    payroll_number = models.CharField(max_length=64, unique=True)
    month_year = models.CharField(max_length=64)
    financial_year = models.CharField(max_length=32, default='2026-2027')
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    department = models.CharField(max_length=128)
    designation = models.CharField(max_length=128)
    working_days = models.DecimalField(max_digits=5, decimal_places=1, default=30.0)
    present_days = models.DecimalField(max_digits=5, decimal_places=1, default=30.0)
    leave_days = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)
    loss_of_pay_days = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    hra = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    overtime_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    gross_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    pf_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    esi_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    pt_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    tds_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    loan_advance_recovery = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    employer_pf = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    employer_esi = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_ctc = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    status = models.CharField(max_length=64, default='Draft')
    processed_date = models.DateField()
    approved_by = models.CharField(max_length=128, blank=True)
    accounting_voucher_ref = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['-processed_date']

    def __str__(self):
        return f"{self.payroll_number} - {self.employee_name} ({self.month_year})"


class EmployeeAdvanceLoan(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    loan_number = models.CharField(max_length=64, unique=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    department = models.CharField(max_length=128)
    loan_type = models.CharField(max_length=64, default='Short Term Advance')
    sanctioned_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    disbursement_date = models.DateField()
    reason = models.TextField(blank=True)
    emi_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_installments = models.IntegerField(default=1)
    paid_installments = models.IntegerField(default=0)
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    recovery_start_month = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=64, default='Active')

    def __str__(self):
        return f"{self.loan_number} - {self.employee_name}"


class ReimbursementExpense(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    reimbursement_no = models.CharField(max_length=64, unique=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    department = models.CharField(max_length=128)
    expense_date = models.DateField()
    category = models.CharField(max_length=128)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    description = models.TextField(blank=True)
    receipt_url = models.CharField(max_length=512, blank=True)
    project_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=64, default='Pending Manager')
    approved_by = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f"{self.reimbursement_no} - {self.employee_name} ({self.amount})"
