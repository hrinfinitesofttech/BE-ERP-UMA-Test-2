from django.contrib import admin
from .models import Designation, EmployeeDocument, ShiftMaster, AttendanceRecord, LeaveRequest, WFHRequest, MissedPunchRequest, AttendanceRegularization, OvertimeRecord, EarlyCheckoutRequest, SalaryComponent, SalaryStructure, PayrollRecord, EmployeeAdvanceLoan, ReimbursementExpense

@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('id', 'designation_code', 'designation_name', 'department', 'level', 'reporting_designation')
    search_fields = ('id', 'designation_code', 'designation_name')
    list_filter = ('status',)

@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee_id', 'employee_name', 'document_type', 'document_number', 'issue_date')
    search_fields = ('id', 'employee_id', 'employee_name', 'document_number')
    list_filter = ('document_type', 'issue_date', 'expiry_date', 'verification_status')

@admin.register(ShiftMaster)
class ShiftMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift_name', 'start_time', 'end_time', 'grace_period_minutes', 'break_duration_minutes')
    search_fields = ('id', 'shift_name')
    list_filter = ('status',)

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee_id', 'employee_name', 'department', 'date', 'shift_name')
    search_fields = ('id', 'employee_id', 'employee_name', 'shift_name')
    list_filter = ('date', 'status')

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'leave_number', 'employee_id', 'employee_name', 'department', 'leave_type_id')
    search_fields = ('id', 'leave_number', 'employee_id', 'employee_name')
    list_filter = ('leave_type_id', 'from_date', 'to_date', 'is_half_day')

@admin.register(WFHRequest)
class WFHRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'wfh_number', 'employee_id', 'employee_name', 'department', 'from_date')
    search_fields = ('id', 'wfh_number', 'employee_id', 'employee_name')
    list_filter = ('from_date', 'to_date', 'status')

@admin.register(MissedPunchRequest)
class MissedPunchRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'request_number', 'employee_id', 'employee_name', 'date', 'missing_punch_type')
    search_fields = ('id', 'request_number', 'employee_id', 'employee_name')
    list_filter = ('date', 'missing_punch_type', 'status')

@admin.register(AttendanceRegularization)
class AttendanceRegularizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'regularization_no', 'employee_id', 'employee_name', 'date', 'original_status')
    search_fields = ('id', 'regularization_no', 'employee_id', 'employee_name')
    list_filter = ('date', 'original_status', 'requested_status', 'status')

@admin.register(OvertimeRecord)
class OvertimeRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'overtime_no', 'employee_id', 'employee_name', 'department', 'date')
    search_fields = ('id', 'overtime_no', 'employee_id', 'employee_name')
    list_filter = ('date', 'status')

@admin.register(EarlyCheckoutRequest)
class EarlyCheckoutRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'request_number', 'employee_id', 'employee_name', 'date', 'shift_name')
    search_fields = ('id', 'request_number', 'employee_id', 'employee_name')
    list_filter = ('date', 'status')

@admin.register(SalaryComponent)
class SalaryComponentAdmin(admin.ModelAdmin):
    list_display = ('id', 'component_code', 'component_name', 'component_type', 'calculation_type', 'percentage_or_formula')
    search_fields = ('id', 'component_code', 'component_name')
    list_filter = ('component_type', 'calculation_type', 'is_taxable', 'is_statutory')

@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ('id', 'structure_name', 'employee_id', 'employee_name', 'effective_from', 'basic_salary')
    search_fields = ('id', 'structure_name', 'employee_id', 'employee_name')
    list_filter = ('effective_from', 'status')

@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'payroll_number', 'month_year', 'financial_year', 'employee_id', 'employee_name')
    search_fields = ('id', 'payroll_number', 'employee_id', 'employee_name')
    list_filter = ('status', 'processed_date')

@admin.register(EmployeeAdvanceLoan)
class EmployeeAdvanceLoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'loan_number', 'employee_id', 'employee_name', 'department', 'loan_type')
    search_fields = ('id', 'loan_number', 'employee_id', 'employee_name')
    list_filter = ('loan_type', 'disbursement_date', 'status')

@admin.register(ReimbursementExpense)
class ReimbursementExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'reimbursement_no', 'employee_id', 'employee_name', 'department', 'expense_date')
    search_fields = ('id', 'reimbursement_no', 'employee_id', 'employee_name')
    list_filter = ('expense_date', 'category', 'status')
