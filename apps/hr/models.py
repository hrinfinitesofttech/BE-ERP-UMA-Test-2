from apps.core.softdelete import SoftDeleteModel
from django.db import models


class Designation(SoftDeleteModel):
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


class EmployeeDocument(SoftDeleteModel):
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


class ShiftMaster(SoftDeleteModel):
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
    first_in = models.CharField(max_length=32, blank=True)
    last_out = models.CharField(max_length=32, blank=True)
    punch_count = models.IntegerField(default=0)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    late_minutes = models.IntegerField(default=0)
    early_checkout_minutes = models.IntegerField(default=0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    status = models.CharField(max_length=64, default='Present')
    source = models.CharField(max_length=64, default='Biometric System')
    is_manually_approved = models.BooleanField(default=False)
    is_missing_punch = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']
        unique_together = ('employee_id', 'date')

    def __str__(self):
        return f"{self.date} - {self.employee_name} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.id:
            import uuid
            self.id = f"ATT-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)


class LeaveType(SoftDeleteModel):
    id = models.CharField(max_length=64, primary_key=True)
    leave_code = models.CharField(max_length=32, unique=True)
    leave_name = models.CharField(max_length=128)
    annual_quota = models.DecimalField(max_digits=5, decimal_places=1, default=12.0)
    monthly_accrual = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    carry_forward_allowed = models.BooleanField(default=False)
    max_consecutive_days = models.IntegerField(default=5)
    half_day_allowed = models.BooleanField(default=True)
    attachment_required = models.BooleanField(default=False)
    status = models.CharField(max_length=32, default='Active')

    def __str__(self):
        return f"{self.leave_name} ({self.leave_code})"


class LeaveBalance(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    department = models.CharField(max_length=128, blank=True)
    leave_type_id = models.CharField(max_length=64)
    leave_code = models.CharField(max_length=32)
    leave_name = models.CharField(max_length=128)
    financial_year = models.CharField(max_length=32, default='2026-2027')
    total_credited = models.DecimalField(max_digits=5, decimal_places=1, default=12.0)
    used = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)
    pending_approval = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)
    available_balance = models.DecimalField(max_digits=5, decimal_places=1, default=12.0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee_id', 'leave_type_id', 'financial_year')

    def __str__(self):
        return f"{self.employee_name} - {self.leave_code}: {self.available_balance} days"

    def recalculate(self):
        self.available_balance = max(0.0, float(self.total_credited) - float(self.used) - float(self.pending_approval))
        self.save()


class LeaveRequest(SoftDeleteModel):
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
    manager_remarks = models.TextField(blank=True, default='')
    admin_remarks = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-applied_date']

    def __str__(self):
        return f"{self.leave_number} - {self.employee_name} ({self.status})"

    def save(self, *args, **kwargs):
        import uuid
        from django.utils import timezone
        if not self.id:
            self.id = f"LV-{uuid.uuid4().hex[:10].upper()}"
        if not self.leave_number:
            self.leave_number = f"LR-2026-{uuid.uuid4().hex[:6].upper()}"
        if not self.applied_date:
            self.applied_date = timezone.now().date()
        super().save(*args, **kwargs)


class WFHRequest(SoftDeleteModel):
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


class MissedPunchRequest(SoftDeleteModel):
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


class AttendanceRegularization(SoftDeleteModel):
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


class OvertimeRecord(SoftDeleteModel):
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


class EarlyCheckoutRequest(SoftDeleteModel):
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


class SalaryComponent(SoftDeleteModel):
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


class SalaryStructure(SoftDeleteModel):
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
    # statutory applicability & identifiers (used by the payroll engine and printed on the payslip)
    pf_applicable = models.BooleanField(default=True)
    esi_applicable = models.BooleanField(default=True)
    pt_applicable = models.BooleanField(default=True)
    overtime_eligible = models.BooleanField(default=True)
    uan_number = models.CharField(max_length=32, blank=True, default='')
    esi_number = models.CharField(max_length=32, blank=True, default='')
    pan_number = models.CharField(max_length=16, blank=True, default='')

    def __str__(self):
        return f"{self.structure_name} - {self.employee_name}"


class PayrollRecord(SoftDeleteModel):
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
    status = models.CharField(max_length=64, default='Draft')  # Draft / Approved / Paid
    processed_date = models.DateField()
    approved_by = models.CharField(max_length=128, blank=True)
    accounting_voucher_ref = models.CharField(max_length=64, blank=True)
    # --- detailed calculation (added with the real payroll engine)
    period_ym = models.CharField(max_length=7, blank=True, default='', db_index=True)  # 2026-11
    calendar_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    paid_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    weekly_offs = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    holidays = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    half_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    late_days = models.IntegerField(default=0)
    conveyance_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    reimbursement_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    other_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    lop_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)  # information only
    loan_recovery_detail = models.JSONField(default=list, blank=True)
    reimbursement_ids = models.JSONField(default=list, blank=True)
    calc_notes = models.JSONField(default=list, blank=True)
    remarks = models.TextField(blank=True, default='')
    joining_date = models.CharField(max_length=30, blank=True, default='')
    uan_number = models.CharField(max_length=32, blank=True, default='')
    esi_number = models.CharField(max_length=32, blank=True, default='')
    pan_number = models.CharField(max_length=16, blank=True, default='')
    bank_name = models.CharField(max_length=150, blank=True, default='')
    bank_account_no = models.CharField(max_length=50, blank=True, default='')
    bank_ifsc = models.CharField(max_length=30, blank=True, default='')
    payment_status = models.CharField(max_length=24, default='Unpaid')
    paid_date = models.DateField(null=True, blank=True)
    payment_mode = models.CharField(max_length=32, blank=True, default='')
    payment_ref = models.CharField(max_length=128, blank=True, default='')

    class Meta:
        ordering = ['-processed_date']

    def __str__(self):
        return f"{self.payroll_number} - {self.employee_name} ({self.month_year})"


class EmployeeAdvanceLoan(SoftDeleteModel):
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


class ReimbursementExpense(SoftDeleteModel):
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


class EmployeeOnboarding(SoftDeleteModel):
    id = models.CharField(max_length=64, primary_key=True)
    candidate_id = models.CharField(max_length=64, blank=True)
    candidate_name = models.CharField(max_length=128)
    email = models.CharField(max_length=128, blank=True)
    mobile = models.CharField(max_length=32, blank=True)
    joining_date = models.DateField()
    department = models.CharField(max_length=128)
    designation = models.CharField(max_length=128)
    reporting_manager = models.CharField(max_length=128, blank=True)
    shift = models.CharField(max_length=128, blank=True)
    salary_structure_id = models.CharField(max_length=64, blank=True)
    offered_ctc = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    onboarding_checklist = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=64, default='In Progress')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate_name} ({self.department} - {self.designation})"


class EmployeeTransfer(SoftDeleteModel):
    id = models.CharField(max_length=64, primary_key=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    effective_date = models.DateField()
    from_department = models.CharField(max_length=128)
    to_department = models.CharField(max_length=128)
    from_designation = models.CharField(max_length=128, blank=True)
    to_designation = models.CharField(max_length=128, blank=True)
    from_location = models.CharField(max_length=128, blank=True)
    to_location = models.CharField(max_length=128, blank=True)
    reason = models.TextField(blank=True)
    approved_by = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=32, default='Approved')

    def __str__(self):
        return f"{self.employee_name}: {self.from_department} -> {self.to_department}"


class EmployeePromotion(SoftDeleteModel):
    id = models.CharField(max_length=64, primary_key=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    effective_date = models.DateField()
    old_designation = models.CharField(max_length=128)
    new_designation = models.CharField(max_length=128)
    old_grade = models.CharField(max_length=64, blank=True)
    new_grade = models.CharField(max_length=64, blank=True)
    old_ctc = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    new_ctc = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    increment_percentage = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    approved_by = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=32, default='Approved')

    def __str__(self):
        return f"{self.employee_name}: {self.old_designation} -> {self.new_designation}"


class EmployeeExit(SoftDeleteModel):
    id = models.CharField(max_length=64, primary_key=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    department = models.CharField(max_length=128)
    designation = models.CharField(max_length=128)
    resignation_date = models.DateField()
    last_working_date = models.DateField()
    notice_period_days = models.IntegerField(default=30)
    reason = models.TextField(blank=True)
    exit_interview_notes = models.TextField(blank=True)
    department_clearance = models.BooleanField(default=False)
    asset_return_clearance = models.BooleanField(default=False)
    hr_clearance = models.BooleanField(default=False)
    accounts_clearance = models.BooleanField(default=False)
    status = models.CharField(max_length=32, default='Pending')

    def __str__(self):
        return f"Exit: {self.employee_name} ({self.resignation_date})"


class Holiday(SoftDeleteModel):
    id = models.CharField(max_length=64, primary_key=True)
    holiday_name = models.CharField(max_length=128)
    holiday_date = models.DateField()
    holiday_type = models.CharField(max_length=64, default='Public Holiday')
    applicable_departments = models.JSONField(default=list, blank=True)
    is_optional = models.BooleanField(default=False)
    financial_year = models.CharField(max_length=32, default='FY 2026-27')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['holiday_date']

    def __str__(self):
        return f"{self.holiday_name} ({self.holiday_date})"


class EmployeeAppraisal(SoftDeleteModel):
    id = models.CharField(max_length=64, primary_key=True)
    appraisal_number = models.CharField(max_length=64, unique=True)
    employee_id = models.CharField(max_length=64)
    employee_name = models.CharField(max_length=128)
    department = models.CharField(max_length=128, blank=True)
    cycle_period = models.CharField(max_length=128, default='FY 2025-26 Annual')
    kpi_score = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    self_rating = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    manager_rating = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    final_score = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    manager_comments = models.TextField(blank=True)
    promotion_recommended = models.BooleanField(default=False)
    recommended_increment_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=64, default='Manager Review Pending')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.appraisal_number} - {self.employee_name}"




class PunchMachineConfig(models.Model):
    """Configuration for eTimeOffice punching machine integration."""
    id = models.CharField(max_length=64, primary_key=True)
    machine_name = models.CharField(max_length=128, default='eTimeOffice Machine')
    base_url = models.CharField(max_length=512, default='https://api.etimeoffice.com/api')
    corporate_id = models.CharField(max_length=128, default='support')
    username = models.CharField(max_length=128, default='support')
    password = models.CharField(max_length=256, default='support')
    is_active = models.BooleanField(default=True)
    last_sync_time = models.DateTimeField(null=True, blank=True)
    last_record_token = models.CharField(max_length=256, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.machine_name} ({self.base_url})"

    def get_auth_header(self):
        import base64
        raw = f"{self.corporate_id}:{self.username}:{self.password}:true"
        encoded = base64.b64encode(raw.encode()).decode()
        return {'Authorization': encoded}

    def save(self, *args, **kwargs):
        if not self.id:
            import uuid
            self.id = f"PMC-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)


class PunchLog(models.Model):
    """Raw punch logs fetched from the punching machine."""
    id = models.CharField(max_length=64, primary_key=True)
    emp_code = models.CharField(max_length=64)  # Machine employee code
    emp_name = models.CharField(max_length=128, blank=True)
    punch_datetime = models.DateTimeField()
    punch_date = models.DateField(null=True, blank=True, db_index=True)
    machine_id = models.CharField(max_length=64, blank=True)
    m_flag = models.CharField(max_length=32, blank=True)
    emp_card_no = models.CharField(max_length=64, blank=True)
    source_table = models.CharField(max_length=128, blank=True)
    raw_record_id = models.IntegerField(null=True, blank=True)
    erp_employee = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='punch_logs'
    )
    is_mapped = models.BooleanField(default=False, db_index=True)
    synced_to_attendance = models.BooleanField(default=False)
    sync_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-punch_datetime']
        unique_together = ('emp_code', 'punch_datetime')

    def __str__(self):
        return f"{self.emp_code} - {self.punch_datetime}"

    def save(self, *args, **kwargs):
        if not self.id:
            import uuid
            self.id = f"PL-{uuid.uuid4().hex[:10].upper()}"
        if self.punch_datetime and not self.punch_date:
            self.punch_date = self.punch_datetime.date()
        super().save(*args, **kwargs)


class BiometricEmployeeMapping(models.Model):
    """Explicit mapping between eTimeOffice machine employee code and ERP Employee User."""
    id = models.CharField(max_length=64, primary_key=True)
    machine_emp_code = models.CharField(max_length=64, unique=True)
    employee = models.ForeignKey(
        'authentication.User',
        on_delete=models.CASCADE,
        related_name='biometric_mappings'
    )
    employee_code = models.CharField(max_length=64, blank=True)
    employee_name = models.CharField(max_length=128, blank=True)
    device_card_no = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    mapped_by = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee_code', 'machine_emp_code']

    def __str__(self):
        return f"{self.machine_emp_code} -> {self.employee_code} ({self.employee_name})"

    def save(self, *args, **kwargs):
        if not self.id:
            import uuid
            self.id = f"MAP-{uuid.uuid4().hex[:10].upper()}"
        if self.employee:
            self.employee_code = self.employee.id
            if not self.employee_name:
                self.employee_name = self.employee.name or self.employee.username
        super().save(*args, **kwargs)



class PayrollSettings(models.Model):
    """Singleton (pk=1): statutory rates and rules used by the payroll engine."""
    days_basis = models.CharField(max_length=16, default='calendar')  # calendar | fixed26 | fixed30
    pf_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12)
    pf_wage_ceiling = models.DecimalField(max_digits=10, decimal_places=2, default=15000)
    esi_employee_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.75)
    esi_employer_rate = models.DecimalField(max_digits=5, decimal_places=2, default=3.25)
    esi_gross_ceiling = models.DecimalField(max_digits=10, decimal_places=2, default=21000)
    # Gujarat professional tax slabs for men: [{"upto": 5999, "pt": 0}, ...] — last slab has "upto": null
    pt_slabs = models.JSONField(default=list, blank=True)
    ot_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=2)
    shift_hours = models.DecimalField(max_digits=4, decimal_places=1, default=8)
    unpaid_leave_keywords = models.CharField(max_length=255, default='unpaid,lwp,loss of pay,lop')
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        if not obj.pt_slabs:
            obj.pt_slabs = [{'upto': 5999, 'pt': 0}, {'upto': 8999, 'pt': 80}, {'upto': 11999, 'pt': 150}, {'upto': None, 'pt': 200}]
            obj.save()
        return obj
