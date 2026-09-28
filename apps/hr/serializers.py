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
    class Meta:
        model = MissedPunchRequest
        fields = '__all__'


class AttendanceRegularizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRegularization
        fields = '__all__'


class OvertimeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = OvertimeRecord
        fields = '__all__'


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

