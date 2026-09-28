from rest_framework import serializers
from .models import (
    Designation, EmployeeDocument, ShiftMaster, AttendanceRecord,
    LeaveRequest, WFHRequest, MissedPunchRequest, AttendanceRegularization,
    OvertimeRecord, EarlyCheckoutRequest, SalaryComponent, SalaryStructure,
    PayrollRecord, EmployeeAdvanceLoan, ReimbursementExpense,
    EmployeeOnboarding, EmployeeTransfer, EmployeePromotion, EmployeeExit
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

