from rest_framework import serializers
from .models import (
    Designation, EmployeeDocument, ShiftMaster, AttendanceRecord,
    LeaveRequest, WFHRequest, MissedPunchRequest, AttendanceRegularization,
    OvertimeRecord, EarlyCheckoutRequest, SalaryComponent, SalaryStructure,
    PayrollRecord, EmployeeAdvanceLoan, ReimbursementExpense,
    EmployeeOnboarding, EmployeeTransfer, EmployeePromotion, EmployeeExit,
    Holiday
)


class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = '__all__'


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = '__all__'


class ShiftMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftMaster
        fields = '__all__'


class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = '__all__'


class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = '__all__'


class WFHRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WFHRequest
        fields = '__all__'


class MissedPunchRequestSerializer(serializers.ModelSerializer):
    requestNumber = serializers.CharField(source='request_number', required=False)
    employeeId = serializers.CharField(source='employee_id', required=False)
    employeeName = serializers.CharField(source='employee_name', required=False)
    missingPunchType = serializers.CharField(source='missing_punch_type', required=False)
    requestedTime = serializers.CharField(source='requested_time', required=False)
    reportingManager = serializers.CharField(source='reporting_manager', required=False, allow_blank=True)

    class Meta:
        model = MissedPunchRequest
        fields = '__all__'

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        if 'id' in data:
            ret['id'] = data['id']
        if 'requestNumber' in data and 'request_number' not in ret:
            ret['request_number'] = data['requestNumber']
        if 'employeeId' in data and 'employee_id' not in ret:
            ret['employee_id'] = data['employeeId']
        if 'employeeName' in data and 'employee_name' not in ret:
            ret['employee_name'] = data['employeeName']
        if 'missingPunchType' in data and 'missing_punch_type' not in ret:
            ret['missing_punch_type'] = data['missingPunchType']
        if 'requestedTime' in data and 'requested_time' not in ret:
            ret['requested_time'] = data['requestedTime']
        if 'reportingManager' in data and 'reporting_manager' not in ret:
            ret['reporting_manager'] = data['reportingManager']
        return ret



class AttendanceRegularizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRegularization
        fields = '__all__'


class OvertimeRecordSerializer(serializers.ModelSerializer):
    overtimeNo = serializers.CharField(source='overtime_no', required=False)
    employeeId = serializers.CharField(source='employee_id', required=False)
    employeeName = serializers.CharField(source='employee_name', required=False)
    regularHours = serializers.DecimalField(source='regular_hours', max_digits=5, decimal_places=2, required=False)
    overtimeHours = serializers.DecimalField(source='overtime_hours', max_digits=5, decimal_places=2, required=False)
    overtimeRateMultiplier = serializers.DecimalField(source='overtime_rate_multiplier', max_digits=4, decimal_places=2, required=False)
    overtimeAmount = serializers.DecimalField(source='overtime_amount', max_digits=10, decimal_places=2, required=False)
    approvedBy = serializers.CharField(source='approved_by', required=False, allow_blank=True)

    class Meta:
        model = OvertimeRecord
        fields = '__all__'

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        if 'id' in data:
            ret['id'] = data['id']
        if 'overtimeNo' in data and 'overtime_no' not in ret:
            ret['overtime_no'] = data['overtimeNo']
        if 'employeeId' in data and 'employee_id' not in ret:
            ret['employee_id'] = data['employeeId']
        if 'employeeName' in data and 'employee_name' not in ret:
            ret['employee_name'] = data['employeeName']
        if 'regularHours' in data and 'regular_hours' not in ret:
            ret['regular_hours'] = data['regularHours']
        if 'overtimeHours' in data and 'overtime_hours' not in ret:
            ret['overtime_hours'] = data['overtimeHours']
        if 'overtimeRateMultiplier' in data and 'overtime_rate_multiplier' not in ret:
            ret['overtime_rate_multiplier'] = data['overtimeRateMultiplier']
        if 'overtimeAmount' in data and 'overtime_amount' not in ret:
            ret['overtime_amount'] = data['overtimeAmount']
        if 'approvedBy' in data and 'approved_by' not in ret:
            ret['approved_by'] = data['approvedBy']
        return ret



class EarlyCheckoutRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = EarlyCheckoutRequest
        fields = '__all__'


class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = '__all__'


class SalaryStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryStructure
        fields = '__all__'


class PayrollRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRecord
        fields = '__all__'


class EmployeeAdvanceLoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAdvanceLoan
        fields = '__all__'


class ReimbursementExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReimbursementExpense
        fields = '__all__'


class EmployeeOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeOnboarding
        fields = '__all__'


class EmployeeTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeTransfer
        fields = '__all__'


class EmployeePromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeePromotion
        fields = '__all__'


class EmployeeExitSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeExit
        fields = '__all__'


class HolidaySerializer(serializers.ModelSerializer):
    holidayName = serializers.CharField(source='holiday_name', required=False)
    holidayDate = serializers.DateField(source='holiday_date', required=False)
    holidayType = serializers.CharField(source='holiday_type', required=False, default='Public Holiday')
    applicableDepartments = serializers.JSONField(source='applicable_departments', required=False)
    isOptional = serializers.BooleanField(source='is_optional', required=False, default=False)
    financialYear = serializers.CharField(source='financial_year', required=False, default='FY 2026-27')

    class Meta:
        model = Holiday
        fields = '__all__'

