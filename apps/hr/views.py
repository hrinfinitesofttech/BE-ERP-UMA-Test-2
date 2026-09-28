from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import (
    Designation, EmployeeDocument, ShiftMaster, AttendanceRecord,
    LeaveRequest, WFHRequest, MissedPunchRequest, AttendanceRegularization,
    OvertimeRecord, EarlyCheckoutRequest, SalaryComponent, SalaryStructure,
    PayrollRecord, EmployeeAdvanceLoan, ReimbursementExpense,
    EmployeeOnboarding, EmployeeTransfer, EmployeePromotion, EmployeeExit,
    Holiday
)
from .serializers import (
    DesignationSerializer, EmployeeDocumentSerializer, ShiftMasterSerializer,
    AttendanceRecordSerializer, LeaveRequestSerializer, WFHRequestSerializer,
    MissedPunchRequestSerializer, AttendanceRegularizationSerializer,
    OvertimeRecordSerializer, EarlyCheckoutRequestSerializer,
    SalaryComponentSerializer, SalaryStructureSerializer, PayrollRecordSerializer,
    EmployeeAdvanceLoanSerializer, ReimbursementExpenseSerializer,
    EmployeeOnboardingSerializer, EmployeeTransferSerializer,
    EmployeePromotionSerializer, EmployeeExitSerializer,
    HolidaySerializer
)


class DesignationViewSet(viewsets.ModelViewSet):
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['designation_code', 'designation_name', 'department']
    filterset_fields = ['status', 'department']


class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    queryset = EmployeeDocument.objects.all()
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['employee_name', 'document_type', 'document_number']
    filterset_fields = ['verification_status', 'employee_id']


class ShiftMasterViewSet(viewsets.ModelViewSet):
    queryset = ShiftMaster.objects.all()
    serializer_class = ShiftMasterSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['shift_name']
    filterset_fields = ['status']


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['employee_name', 'department']
    filterset_fields = ['status', 'employee_id', 'date']


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['leave_number', 'employee_name', 'department', 'leave_name']
    filterset_fields = ['status', 'employee_id']

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_leave(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'Approved'
        leave.approved_by = request.data.get('approved_by') or request.data.get('approvedBy') or 'HR Manager'
        leave.approved_date = timezone.now().date()
        leave.save()
        return Response(LeaveRequestSerializer(leave).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_leave(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'Rejected'
        leave.approved_by = request.data.get('approved_by') or request.data.get('approvedBy') or 'HR Manager'
        leave.approved_date = timezone.now().date()
        leave.save()
        return Response(LeaveRequestSerializer(leave).data)


class WFHRequestViewSet(viewsets.ModelViewSet):
    queryset = WFHRequest.objects.all()
    serializer_class = WFHRequestSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['wfh_number', 'employee_name']
    filterset_fields = ['status', 'employee_id']

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_wfh(self, request, pk=None):
        wfh = self.get_object()
        wfh.status = 'Approved'
        wfh.save()
        return Response(WFHRequestSerializer(wfh).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_wfh(self, request, pk=None):
        wfh = self.get_object()
        wfh.status = 'Rejected'
        wfh.save()
        return Response(WFHRequestSerializer(wfh).data)


class MissedPunchRequestViewSet(viewsets.ModelViewSet):
    queryset = MissedPunchRequest.objects.all()
    serializer_class = MissedPunchRequestSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['request_number', 'employee_name']
    filterset_fields = ['status', 'employee_id']

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_missed_punch(self, request, pk=None):
        mp = self.get_object()
        mp.status = 'Approved'
        mp.save()
        return Response(MissedPunchRequestSerializer(mp).data)


class AttendanceRegularizationViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRegularization.objects.all()
    serializer_class = AttendanceRegularizationSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['regularization_no', 'employee_name']
    filterset_fields = ['status', 'employee_id']

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_regularization(self, request, pk=None):
        reg = self.get_object()
        reg.status = 'Approved'
        reg.save()
        return Response(AttendanceRegularizationSerializer(reg).data)


class OvertimeRecordViewSet(viewsets.ModelViewSet):
    queryset = OvertimeRecord.objects.all()
    serializer_class = OvertimeRecordSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['overtime_no', 'employee_name']
    filterset_fields = ['status', 'employee_id']


class EarlyCheckoutRequestViewSet(viewsets.ModelViewSet):
    queryset = EarlyCheckoutRequest.objects.all()
    serializer_class = EarlyCheckoutRequestSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['request_number', 'employee_name']
    filterset_fields = ['status', 'employee_id']


class SalaryComponentViewSet(viewsets.ModelViewSet):
    queryset = SalaryComponent.objects.all()
    serializer_class = SalaryComponentSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['component_code', 'component_name']
    filterset_fields = ['status', 'component_type']


class SalaryStructureViewSet(viewsets.ModelViewSet):
    queryset = SalaryStructure.objects.all()
    serializer_class = SalaryStructureSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['structure_name', 'employee_name']
    filterset_fields = ['status', 'employee_id']


class PayrollRecordViewSet(viewsets.ModelViewSet):
    queryset = PayrollRecord.objects.all()
    serializer_class = PayrollRecordSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['payroll_number', 'employee_name', 'department', 'month_year']
    filterset_fields = ['status', 'month_year', 'financial_year', 'employee_id']

    @action(detail=False, methods=['post'], url_path='generate-monthly-payroll')
    def generate_monthly_payroll(self, request):
        month_year = request.data.get('monthYear') or request.data.get('month_year', 'September 2026')
        financial_year = request.data.get('financialYear') or request.data.get('financial_year', '2026-2027')
        
        structures = SalaryStructure.objects.filter(status='Active')
        created_records = []
        for idx, struct in enumerate(structures, 1):
            p_no = f"PAY-{financial_year[:4]}-{month_year[:3].upper()}-{str(idx).padStart(2, '0') if hasattr(str(idx), 'padStart') else str(idx).zfill(2)}"
            record, created = PayrollRecord.objects.get_or_create(
                payroll_number=p_no,
                defaults={
                    'id': p_no,
                    'month_year': month_year,
                    'financial_year': financial_year,
                    'employee_id': struct.employee_id,
                    'employee_name': struct.employee_name,
                    'department': 'Operations',
                    'designation': 'Executive',
                    'working_days': 26,
                    'present_days': 25,
                    'leave_days': 1,
                    'loss_of_pay_days': 0,
                    'overtime_hours': 4,
                    'basic_salary': struct.basic_salary,
                    'hra': struct.hra,
                    'allowances': struct.conveyance_allowance + struct.medical_allowance + struct.special_allowance,
                    'overtime_amount': 1500,
                    'gross_earnings': struct.gross_salary + 1500,
                    'pf_deduction': struct.employee_pf,
                    'esi_deduction': struct.employee_esi,
                    'pt_deduction': struct.professional_tax,
                    'tds_deduction': struct.tds_monthly,
                    'loan_advance_recovery': 0,
                    'other_deductions': 0,
                    'total_deductions': struct.total_deductions,
                    'net_salary': struct.net_salary + 1500,
                    'employer_pf': struct.employer_pf,
                    'employer_esi': struct.employer_esi,
                    'total_ctc': struct.total_ctc + 1500,
                    'status': 'Draft',
                    'processed_date': timezone.now().date(),
                }
            )
            created_records.append(record)

        return Response(PayrollRecordSerializer(created_records, many=True).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_payroll(self, request, pk=None):
        rec = self.get_object()
        rec.status = 'Approved'
        rec.approved_by = request.data.get('approvedBy') or 'HR / Finance Head'
        rec.save()
        return Response(PayrollRecordSerializer(rec).data)


class EmployeeAdvanceLoanViewSet(viewsets.ModelViewSet):
    queryset = EmployeeAdvanceLoan.objects.all()
    serializer_class = EmployeeAdvanceLoanSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['loan_number', 'employee_name', 'department']
    filterset_fields = ['status', 'employee_id']


class ReimbursementExpenseViewSet(viewsets.ModelViewSet):
    queryset = ReimbursementExpense.objects.all()
    serializer_class = ReimbursementExpenseSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['reimbursement_no', 'employee_name', 'category']
    filterset_fields = ['status', 'employee_id']


class EmployeeOnboardingViewSet(viewsets.ModelViewSet):
    queryset = EmployeeOnboarding.objects.all()
    serializer_class = EmployeeOnboardingSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['candidate_name', 'email', 'mobile', 'department', 'designation']
    filterset_fields = ['status', 'department']

    @action(detail=True, methods=['post'], url_path='complete')
    def complete_onboarding(self, request, pk=None):
        onb = self.get_object()
        onb.status = 'Completed'
        onb.save()
        return Response(EmployeeOnboardingSerializer(onb).data)


class EmployeeTransferViewSet(viewsets.ModelViewSet):
    queryset = EmployeeTransfer.objects.all()
    serializer_class = EmployeeTransferSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['employee_name', 'from_department', 'to_department']
    filterset_fields = ['status']


class EmployeePromotionViewSet(viewsets.ModelViewSet):
    queryset = EmployeePromotion.objects.all()
    serializer_class = EmployeePromotionSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['employee_name', 'old_designation', 'new_designation']
    filterset_fields = ['status']


class EmployeeExitViewSet(viewsets.ModelViewSet):
    queryset = EmployeeExit.objects.all()
    serializer_class = EmployeeExitSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['employee_name', 'department', 'designation']
    filterset_fields = ['status']


class HolidayViewSet(viewsets.ModelViewSet):
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['holiday_name', 'holiday_type', 'financial_year']
    filterset_fields = ['holiday_type', 'financial_year', 'is_optional']

    def perform_create(self, serializer):
        req_id = serializer.validated_data.get('id') or self.request.data.get('id')
        if not req_id:
            count = Holiday.objects.count() + 1
            req_id = f"HOL-2026-{count:02d}"
        serializer.save(id=req_id)

