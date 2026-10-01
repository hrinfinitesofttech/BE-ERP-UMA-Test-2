from rest_framework import serializers
from .models import (
    Designation, EmployeeDocument, ShiftMaster, AttendanceRecord,
    LeaveRequest, WFHRequest, MissedPunchRequest, AttendanceRegularization,
    OvertimeRecord, EarlyCheckoutRequest, SalaryComponent, SalaryStructure,
    PayrollRecord, EmployeeAdvanceLoan, ReimbursementExpense,
    EmployeeOnboarding, EmployeeTransfer, EmployeePromotion, EmployeeExit,
    Holiday, EmployeeAppraisal
)


class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = '__all__'

    def validate_designation_name(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError("Designation title cannot be blank.")
        if len(str(value).strip()) < 2:
            raise serializers.ValidationError("Designation title must be at least 2 characters.")
        return str(value).strip()

    def validate_department(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError("Department is required.")
        return str(value).strip()


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = '__all__'

    def validate_document_number(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError("Document number cannot be blank.")
        return str(value).strip().replace(' ', '')


class ShiftMasterSerializer(serializers.ModelSerializer):
    shiftName = serializers.CharField(source='shift_name', required=False)
    startTime = serializers.CharField(source='start_time', required=False)
    endTime = serializers.CharField(source='end_time', required=False)
    gracePeriodMinutes = serializers.IntegerField(source='grace_period_minutes', required=False)
    breakDurationMinutes = serializers.IntegerField(source='break_duration_minutes', required=False)
    lateRule = serializers.CharField(source='late_rule', required=False, allow_blank=True)
    earlyCheckoutRule = serializers.CharField(source='early_checkout_rule', required=False, allow_blank=True)
    overtimeRule = serializers.CharField(source='overtime_rule', required=False, allow_blank=True)
    weeklyOff = serializers.CharField(source='weekly_off', required=False, allow_blank=True)

    class Meta:
        model = ShiftMaster
        fields = '__all__'

    def validate(self, data):
        shift_name = data.get('shift_name', '')
        if not shift_name and not self.instance:
            raise serializers.ValidationError({"shift_name": "Please enter the shift name."})

        if shift_name:
            qs = ShiftMaster.objects.filter(shift_name__iexact=shift_name.strip())
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError({"shift_name": "A shift with this name already exists."})

        start_time = data.get('start_time', '')
        if not start_time and not self.instance:
            raise serializers.ValidationError({"start_time": "Please select the start time."})

        end_time = data.get('end_time', '')
        if not end_time and not self.instance:
            raise serializers.ValidationError({"end_time": "Please select the end time."})

        return data


class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = '__all__'


class LeaveRequestSerializer(serializers.ModelSerializer):
    leaveNumber = serializers.CharField(source='leave_number', required=False)
    employeeId = serializers.CharField(source='employee_id', required=False)
    employeeName = serializers.CharField(source='employee_name', required=False)
    leaveTypeId = serializers.CharField(source='leave_type_id', required=False, allow_blank=True)
    leaveName = serializers.CharField(source='leave_name', required=False)
    fromDate = serializers.DateField(source='from_date', required=False)
    toDate = serializers.DateField(source='to_date', required=False)
    numberOfDays = serializers.DecimalField(source='number_of_days', max_digits=5, decimal_places=1, required=False, default=1.0)
    isHalfDay = serializers.BooleanField(source='is_half_day', required=False, default=False)
    attachmentUrl = serializers.CharField(source='attachment_url', required=False, allow_blank=True)
    reportingManager = serializers.CharField(source='reporting_manager', required=False, allow_blank=True)
    appliedDate = serializers.DateField(source='applied_date', required=False)
    approvedBy = serializers.CharField(source='approved_by', required=False, allow_blank=True)
    approvedDate = serializers.DateField(source='approved_date', required=False, allow_null=True)

    class Meta:
        model = LeaveRequest
        fields = '__all__'

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        if 'leaveNumber' in data:
            ret['leave_number'] = data['leaveNumber']
        if 'employeeId' in data:
            ret['employee_id'] = data['employeeId']
        if 'employeeName' in data:
            ret['employee_name'] = data['employeeName']
        if 'leaveTypeId' in data:
            ret['leave_type_id'] = data['leaveTypeId']
        if 'leaveName' in data:
            ret['leave_name'] = data['leaveName']
        if 'fromDate' in data:
            ret['from_date'] = data['fromDate']
        if 'toDate' in data:
            ret['to_date'] = data['toDate']
        if 'numberOfDays' in data:
            ret['number_of_days'] = data['numberOfDays']
        if 'isHalfDay' in data:
            ret['is_half_day'] = data['isHalfDay']
        if 'attachmentUrl' in data:
            ret['attachment_url'] = data['attachmentUrl']
        if 'reportingManager' in data:
            ret['reporting_manager'] = data['reportingManager']
        if 'appliedDate' in data:
            ret['applied_date'] = data['appliedDate']
        return ret

    def validate(self, data):
        if not data.get('employee_id') and not self.instance:
            raise serializers.ValidationError({"employee_id": "Please select the employee."})

        if not data.get('leave_name') and not data.get('leave_type_id') and not self.instance:
            raise serializers.ValidationError({"leave_type_id": "Please select the leave type."})

        from_date = data.get('from_date')
        if not from_date and not self.instance:
            raise serializers.ValidationError({"from_date": "Please select the start date."})

        to_date = data.get('to_date')
        if not to_date and not self.instance:
            raise serializers.ValidationError({"to_date": "Please select the end date."})

        if from_date and to_date and to_date < from_date:
            raise serializers.ValidationError({"to_date": "The end date cannot be earlier than the start date."})

        reason = (data.get('reason') or '').strip()
        if not reason and not self.instance:
            raise serializers.ValidationError({"reason": "Please enter the reason for leave."})

        return data


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
    requestNumber = serializers.CharField(source='request_number', required=False)
    employeeId = serializers.CharField(source='employee_id', required=False)
    employeeName = serializers.CharField(source='employee_name', required=False)
    shiftName = serializers.CharField(source='shift_name', required=False, allow_blank=True)
    expectedCheckout = serializers.CharField(source='expected_checkout', required=False, allow_blank=True)
    requestedCheckout = serializers.CharField(source='requested_checkout', required=False, allow_blank=True)

    class Meta:
        model = EarlyCheckoutRequest
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
        if 'shiftName' in data and 'shift_name' not in ret:
            ret['shift_name'] = data['shiftName']
        if 'expectedCheckout' in data and 'expected_checkout' not in ret:
            ret['expected_checkout'] = data['expectedCheckout']
        if 'requestedCheckout' in data and 'requested_checkout' not in ret:
            ret['requested_checkout'] = data['requestedCheckout']
        return ret


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
    employeeId = serializers.CharField(source='employee_id', required=False)
    employeeName = serializers.CharField(source='employee_name', required=False)
    effectiveDate = serializers.DateField(source='effective_date', required=False)
    fromDepartment = serializers.CharField(source='from_department', required=False, allow_blank=True)
    toDepartment = serializers.CharField(source='to_department', required=False)
    fromDesignation = serializers.CharField(source='from_designation', required=False, allow_blank=True)
    toDesignation = serializers.CharField(source='to_designation', required=False, allow_blank=True)
    fromLocation = serializers.CharField(source='from_location', required=False, allow_blank=True)
    toLocation = serializers.CharField(source='to_location', required=False, allow_blank=True)
    approvedBy = serializers.CharField(source='approved_by', required=False, allow_blank=True)

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        if 'id' in data:
            ret['id'] = data['id']
        if 'employeeId' in data and 'employee_id' not in ret:
            ret['employee_id'] = data['employeeId']
        if 'employeeName' in data and 'employee_name' not in ret:
            ret['employee_name'] = data['employeeName']
        if 'effectiveDate' in data and 'effective_date' not in ret:
            ret['effective_date'] = data['effectiveDate']
        if 'fromDepartment' in data and 'from_department' not in ret:
            ret['from_department'] = data['fromDepartment']
        if 'toDepartment' in data and 'to_department' not in ret:
            ret['to_department'] = data['toDepartment']
        if 'fromDesignation' in data and 'from_designation' not in ret:
            ret['from_designation'] = data['fromDesignation']
        if 'toDesignation' in data and 'to_designation' not in ret:
            ret['to_designation'] = data['toDesignation']
        if 'fromLocation' in data and 'from_location' not in ret:
            ret['from_location'] = data['fromLocation']
        if 'toLocation' in data and 'to_location' not in ret:
            ret['to_location'] = data['toLocation']
        if 'approvedBy' in data and 'approved_by' not in ret:
            ret['approved_by'] = data['approvedBy']
        return ret

    class Meta:
        model = EmployeeTransfer
        fields = '__all__'

    def validate(self, data):
        employee_id = data.get('employee_id')
        if not employee_id and not self.instance:
            raise serializers.ValidationError({"employee_id": "Please select the employee."})
        
        from_dept = data.get('from_department', '') or ''
        to_dept = data.get('to_department', '') or ''
        
        if not to_dept and not self.instance:
            raise serializers.ValidationError({"to_department": "Please select the new department."})
        
        if to_dept and from_dept and to_dept.strip().lower() == from_dept.strip().lower():
            raise serializers.ValidationError({"to_department": "The new department cannot be the same as the current department."})
        
        to_desg = data.get('to_designation', '') or ''
        if not to_desg and not self.instance:
            raise serializers.ValidationError({"to_designation": "Please select the new designation."})

        effective_date = data.get('effective_date')
        if not effective_date and not self.instance:
            raise serializers.ValidationError({"effective_date": "Please select the transfer effective date."})
        elif effective_date:
            from datetime import date
            if effective_date < date.today():
                raise serializers.ValidationError({"effective_date": "The transfer effective date cannot be in the past."})

        reason = data.get('reason', '') or ''
        if not reason and not self.instance:
            raise serializers.ValidationError({"reason": "Please enter the transfer reason."})

        return data


class EmployeePromotionSerializer(serializers.ModelSerializer):
    employeeId = serializers.CharField(source='employee_id', required=False)
    employeeName = serializers.CharField(source='employee_name', required=False)
    effectiveDate = serializers.DateField(source='effective_date', required=False)
    oldDesignation = serializers.CharField(source='old_designation', required=False, allow_blank=True)
    newDesignation = serializers.CharField(source='new_designation', required=False)
    oldGrade = serializers.CharField(source='old_grade', required=False, allow_blank=True)
    newGrade = serializers.CharField(source='new_grade', required=False, allow_blank=True)
    oldCTC = serializers.DecimalField(source='old_ctc', max_digits=14, decimal_places=2, required=False)
    newCTC = serializers.DecimalField(source='new_ctc', max_digits=14, decimal_places=2, required=False)
    incrementPercentage = serializers.DecimalField(source='increment_percentage', max_digits=6, decimal_places=2, required=False)
    approvedBy = serializers.CharField(source='approved_by', required=False, allow_blank=True)

    class Meta:
        model = EmployeePromotion
        fields = '__all__'

    def validate(self, data):
        employee_id = data.get('employee_id')
        if not employee_id and not self.instance:
            raise serializers.ValidationError({"employee_id": "Please select the employee."})
        
        effective_date = data.get('effective_date')
        if not effective_date and not self.instance:
            raise serializers.ValidationError({"effective_date": "Please select the effective date."})

        new_ctc = data.get('new_ctc')
        if new_ctc is not None and new_ctc <= 0:
            raise serializers.ValidationError({"new_ctc": "Please enter the increment amount. Amount must be greater than zero."})

        return data


class EmployeeExitSerializer(serializers.ModelSerializer):
    employeeId = serializers.CharField(source='employee_id', required=False)
    employeeName = serializers.CharField(source='employee_name', required=False)
    resignationDate = serializers.DateField(source='resignation_date', required=False)
    lastWorkingDate = serializers.DateField(source='last_working_date', required=False)
    noticePeriodDays = serializers.IntegerField(source='notice_period_days', required=False)
    exitInterviewNotes = serializers.CharField(source='exit_interview_notes', required=False, allow_blank=True)
    departmentClearance = serializers.BooleanField(source='department_clearance', required=False)
    assetReturnClearance = serializers.BooleanField(source='asset_return_clearance', required=False)
    hrClearance = serializers.BooleanField(source='hr_clearance', required=False)
    accountsClearance = serializers.BooleanField(source='accounts_clearance', required=False)

    class Meta:
        model = EmployeeExit
        fields = '__all__'

    def validate(self, data):
        employee_id = data.get('employee_id')
        if not employee_id and not self.instance:
            raise serializers.ValidationError({"employee_id": "Please select the employee."})
        
        res_date = data.get('resignation_date')
        if not res_date and not self.instance:
            raise serializers.ValidationError({"resignation_date": "Please select the resignation date."})

        lwd = data.get('last_working_date')
        if not lwd and not self.instance:
            raise serializers.ValidationError({"last_working_date": "Please select the last working day."})

        if res_date and lwd and lwd < res_date:
            raise serializers.ValidationError({"last_working_date": "The last working day cannot be earlier than the resignation date."})

        reason = data.get('reason', '')
        if not reason and not self.instance:
            raise serializers.ValidationError({"reason": "Please enter the reason for leaving."})

        return data


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

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        if 'holidayName' in data:
            ret['holiday_name'] = data['holidayName']
        if 'holidayDate' in data:
            ret['holiday_date'] = data['holidayDate']
        if 'holidayType' in data:
            ret['holiday_type'] = data['holidayType']
        if 'applicableDepartments' in data:
            ret['applicable_departments'] = data['applicableDepartments']
        if 'isOptional' in data:
            ret['is_optional'] = data['isOptional']
        if 'financialYear' in data:
            ret['financial_year'] = data['financialYear']
        return ret

    def validate(self, data):
        holiday_name = (data.get('holiday_name') or '').strip()
        if not holiday_name and not self.instance:
            raise serializers.ValidationError({"holiday_name": "Please enter the holiday name."})

        holiday_date = data.get('holiday_date')
        if not holiday_date and not self.instance:
            raise serializers.ValidationError({"holiday_date": "Please select the holiday date."})

        # Check duplicate holiday on the same date
        if holiday_date:
            qs = Holiday.objects.filter(holiday_date=holiday_date)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"holiday_date": "A holiday already exists on this date."})

        return data


class EmployeeAppraisalSerializer(serializers.ModelSerializer):
    appraisalNumber = serializers.CharField(source='appraisal_number', required=False)
    employeeId = serializers.CharField(source='employee_id', required=False)
    employeeName = serializers.CharField(source='employee_name', required=False)
    cyclePeriod = serializers.CharField(source='cycle_period', required=False, default='FY 2025-26 Annual')
    kpiScore = serializers.DecimalField(source='kpi_score', max_digits=4, decimal_places=2, required=False, default=0)
    selfRating = serializers.DecimalField(source='self_rating', max_digits=4, decimal_places=2, required=False, default=0)
    managerRating = serializers.DecimalField(source='manager_rating', max_digits=4, decimal_places=2, required=False, default=0)
    finalScore = serializers.DecimalField(source='final_score', max_digits=4, decimal_places=2, required=False, default=0)
    managerComments = serializers.CharField(source='manager_comments', required=False, allow_blank=True, default='')
    promotionRecommended = serializers.BooleanField(source='promotion_recommended', required=False, default=False)
    recommendedIncrementPct = serializers.DecimalField(source='recommended_increment_pct', max_digits=5, decimal_places=2, required=False, default=0)

    class Meta:
        model = EmployeeAppraisal
        fields = '__all__'


