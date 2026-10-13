from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from apps.authentication.models import User
from apps.core.rbac_permissions import (
    is_super_admin,
    is_admin,
    is_department_manager,
    compute_effective_permissions,
)
from .models import (
    Designation, EmployeeDocument, ShiftMaster, AttendanceRecord,
    LeaveType, LeaveBalance, LeaveRequest, WFHRequest, MissedPunchRequest, AttendanceRegularization,
    OvertimeRecord, EarlyCheckoutRequest, SalaryComponent, SalaryStructure,
    PayrollRecord, EmployeeAdvanceLoan, ReimbursementExpense,
    EmployeeOnboarding, EmployeeTransfer, EmployeePromotion, EmployeeExit,
    Holiday, EmployeeAppraisal
)
from .serializers import (
    DesignationSerializer, EmployeeDocumentSerializer, ShiftMasterSerializer,
    AttendanceRecordSerializer, LeaveTypeSerializer, LeaveBalanceSerializer,
    LeaveRequestSerializer, WFHRequestSerializer,
    MissedPunchRequestSerializer, AttendanceRegularizationSerializer,
    OvertimeRecordSerializer, EarlyCheckoutRequestSerializer,
    SalaryComponentSerializer, SalaryStructureSerializer, PayrollRecordSerializer,
    EmployeeAdvanceLoanSerializer, ReimbursementExpenseSerializer,
    EmployeeOnboardingSerializer, EmployeeTransferSerializer,
    EmployeePromotionSerializer, EmployeeExitSerializer,
    HolidaySerializer, EmployeeAppraisalSerializer
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


class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['leave_code', 'leave_name']
    filterset_fields = ['status']


class LeaveBalanceViewSet(viewsets.ModelViewSet):
    queryset = LeaveBalance.objects.all()
    serializer_class = LeaveBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['employee_name', 'leave_code', 'leave_name']
    filterset_fields = ['employee_id', 'financial_year']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return LeaveBalance.objects.none()
        if is_super_admin(user) or is_admin(user):
            return LeaveBalance.objects.all()
        if is_department_manager(user):
            dept_name = getattr(user, 'department_name', '')
            return LeaveBalance.objects.filter(department__iexact=dept_name) if dept_name else LeaveBalance.objects.filter(employee_id=user.id)
        return LeaveBalance.objects.filter(employee_id=user.id)


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['employee_name', 'department']
    filterset_fields = ['status', 'employee_id', 'date']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return AttendanceRecord.objects.none()
        if is_super_admin(user) or is_admin(user):
            qs = AttendanceRecord.objects.all()
        elif is_department_manager(user):
            dept_name = getattr(user, 'department_name', '')
            qs = AttendanceRecord.objects.filter(department__iexact=dept_name) if dept_name else AttendanceRecord.objects.filter(employee_id=user.id)
        else:
            qs = AttendanceRecord.objects.filter(employee_id=user.id)

        # Optional filters
        date_param = self.request.query_params.get('date')
        if date_param:
            qs = qs.filter(date=date_param)
        emp_param = self.request.query_params.get('employee_id') or self.request.query_params.get('employeeId')
        if emp_param:
            if is_super_admin(user) or is_admin(user):
                qs = qs.filter(employee_id=emp_param)
            elif is_department_manager(user):
                qs = qs.filter(employee_id=emp_param)
            elif emp_param == user.id:
                qs = qs.filter(employee_id=user.id)
            else:
                return AttendanceRecord.objects.none()
        return qs

    @action(detail=False, methods=['post'], url_path='check-in')
    def check_in(self, request):
        from datetime import datetime, date
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        emp_id = user.id
        emp_name = user.name or f"{user.first_name} {user.last_name}".strip() or user.username
        dept = user.department_name or (user.department.name if user.department else 'General')

        # Allow authorized managers/admins to punch for employee in scope
        target_emp_id = request.data.get('employee_id') or request.data.get('employeeId')
        if target_emp_id and target_emp_id != emp_id:
            if is_super_admin(user) or is_admin(user) or is_department_manager(user):
                target_user = User.objects.filter(id=target_emp_id).first()
                if target_user:
                    if is_department_manager(user) and not is_admin(user):
                        if target_user.department_name != dept:
                            return Response({'error': 'Cannot record attendance for employee outside your department.'}, status=status.HTTP_403_FORBIDDEN)
                    emp_id = target_user.id
                    emp_name = target_user.name or f"{target_user.first_name} {target_user.last_name}".strip() or target_user.username
                    dept = target_user.department_name or dept
            else:
                return Response({'error': 'Cannot punch in for another employee.'}, status=status.HTTP_403_FORBIDDEN)

        today = date.today()
        now_dt = datetime.now()
        now_time = now_dt.strftime('%H:%M')

        # Duplicate check-in prevention
        existing = AttendanceRecord.objects.filter(employee_id=emp_id, date=today).first()
        if existing and existing.check_in:
            return Response({
                'success': False,
                'error': f"Duplicate punch: Already checked in for today at {existing.check_in}.",
                'record': AttendanceRecordSerializer(existing).data
            }, status=status.HTTP_400_BAD_REQUEST)

        # Shift & Late calculation
        shift = ShiftMaster.objects.filter(status='Active').first()
        shift_name = shift.shift_name if shift else 'General Day Shift (09:00 - 18:00)'
        grace_period = shift.grace_period_minutes if shift else 15
        start_time_str = shift.start_time if shift else '09:00'

        late_minutes = 0
        att_status = 'Present'
        try:
            shift_start_dt = datetime.strptime(f"{today} {start_time_str}", '%Y-%m-%d %H:%M')
            punch_dt = datetime.strptime(f"{today} {now_time}", '%Y-%m-%d %H:%M')
            diff_secs = (punch_dt - shift_start_dt).total_seconds()
            diff_mins = int(diff_secs / 60)
            if diff_mins > grace_period:
                late_minutes = diff_mins
                att_status = 'Late'
        except Exception:
            pass

        import uuid
        if not existing:
            record = AttendanceRecord.objects.create(
                id=f"ATT-{uuid.uuid4().hex[:10].upper()}",
                employee_id=emp_id,
                employee_name=emp_name,
                department=dept,
                date=today,
                shift_name=shift_name,
                check_in=now_time,
                late_minutes=late_minutes,
                status=att_status,
                source='Web Punch Portal',
                remarks=f"Punched in at {now_time}" + (f" ({late_minutes}m late)" if late_minutes > 0 else "")
            )
        else:
            record = existing
            record.check_in = now_time
            record.shift_name = shift_name
            record.late_minutes = late_minutes
            record.status = att_status
            record.remarks = f"Punched in at {now_time}" + (f" ({late_minutes}m late)" if late_minutes > 0 else "")
            record.save()

        return Response({
            'success': True,
            'message': f"Checked in successfully at {record.check_in}" + (f" ({late_minutes} min late)" if late_minutes > 0 else ""),
            'record': AttendanceRecordSerializer(record).data
        })

    @action(detail=False, methods=['post'], url_path='check-out')
    def check_out(self, request):
        from datetime import datetime, date
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        emp_id = user.id
        target_emp_id = request.data.get('employee_id') or request.data.get('employeeId')
        if target_emp_id and target_emp_id != emp_id:
            if is_super_admin(user) or is_admin(user) or is_department_manager(user):
                emp_id = target_emp_id
            else:
                return Response({'error': 'Cannot punch out for another employee.'}, status=status.HTTP_403_FORBIDDEN)

        today = date.today()
        record = AttendanceRecord.objects.filter(employee_id=emp_id, date=today).first()
        if not record or not record.check_in:
            return Response({
                'success': False,
                'error': 'Cannot check out without checking in first.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if record.check_out:
            return Response({
                'success': False,
                'error': f"Duplicate punch: Already checked out for today at {record.check_out}.",
                'record': AttendanceRecordSerializer(record).data
            }, status=status.HTTP_400_BAD_REQUEST)

        now_time = datetime.now().strftime('%H:%M')
        record.check_out = now_time

        # Calculate working hours
        try:
            t_in = datetime.strptime(record.check_in, '%H:%M')
            t_out = datetime.strptime(now_time, '%H:%M')
            diff_hours = (t_out - t_in).total_seconds() / 3600.0
            if diff_hours > 0:
                record.total_hours = round(diff_hours, 2)
        except Exception:
            pass

        # Early checkout calculation
        shift = ShiftMaster.objects.filter(status='Active').first()
        if shift and shift.end_time:
            try:
                shift_end_dt = datetime.strptime(shift.end_time, '%H:%M')
                punch_out_dt = datetime.strptime(now_time, '%H:%M')
                early_diff = (shift_end_dt - punch_out_dt).total_seconds() / 60.0
                if early_diff > 0:
                    record.early_checkout_minutes = int(early_diff)
            except Exception:
                pass

        record.save()
        return Response({
            'success': True,
            'message': f"Checked out successfully at {record.check_out}. Total hours worked: {record.total_hours} hrs.",
            'record': AttendanceRecordSerializer(record).data
        })

    @action(detail=False, methods=['get'], url_path='monthly-summary')
    def monthly_summary(self, request):
        from datetime import date
        import calendar
        user = request.user
        emp_id = request.query_params.get('employee_id') or request.query_params.get('employeeId') or user.id

        if emp_id != user.id and not (is_super_admin(user) or is_admin(user) or is_department_manager(user)):
            return Response({'error': 'Unauthorized to view monthly summary of another employee.'}, status=status.HTTP_403_FORBIDDEN)

        today = date.today()
        month = int(request.query_params.get('month', today.month))
        year = int(request.query_params.get('year', today.year))

        num_days = calendar.monthrange(year, month)[1]
        start_date = date(year, month, 1)
        end_date = date(year, month, num_days)

        records = AttendanceRecord.objects.filter(
            employee_id=emp_id,
            date__gte=start_date,
            date__lte=end_date
        )
        record_map = {r.date.isoformat(): r for r in records}

        holidays = Holiday.objects.filter(
            holiday_date__gte=start_date,
            holiday_date__lte=end_date
        )
        holiday_map = {h.holiday_date.isoformat(): h.holiday_name for h in holidays}

        days_list = []
        present_count = 0
        late_count = 0
        absent_count = 0
        leave_count = 0
        weekly_off_count = 0
        holiday_count = 0
        total_hours = 0.0

        for day_num in range(1, num_days + 1):
            curr_date = date(year, month, day_num)
            date_str = curr_date.isoformat()
            is_sunday = curr_date.weekday() == 6
            rec = record_map.get(date_str)
            h_name = holiday_map.get(date_str)

            if rec:
                day_status = rec.status
                check_in = rec.check_in
                check_out = rec.check_out
                hours = float(rec.total_hours or 0)
                total_hours += hours
                if rec.status == 'Late' or rec.late_minutes > 0:
                    late_count += 1
                    present_count += 1
                elif 'Leave' in rec.status:
                    leave_count += 1
                elif rec.status == 'Absent':
                    absent_count += 1
                else:
                    present_count += 1
            elif h_name:
                day_status = 'Holiday'
                check_in = ''
                check_out = ''
                hours = 0.0
                holiday_count += 1
            elif is_sunday:
                day_status = 'Weekly Off'
                check_in = ''
                check_out = ''
                hours = 0.0
                weekly_off_count += 1
            else:
                if curr_date < today:
                    day_status = 'Absent'
                    absent_count += 1
                else:
                    day_status = 'Upcoming'
                check_in = ''
                check_out = ''
                hours = 0.0

            days_list.append({
                'date': date_str,
                'day': curr_date.strftime('%a'),
                'status': day_status,
                'checkIn': check_in,
                'checkOut': check_out,
                'totalHours': hours,
                'holidayName': h_name or ''
            })

        total_working_days = num_days - weekly_off_count - holiday_count

        return Response({
            'month': month,
            'year': year,
            'employeeId': emp_id,
            'totalDays': num_days,
            'workingDays': total_working_days,
            'presentDays': present_count,
            'lateDays': late_count,
            'absentDays': absent_count,
            'leaveDays': leave_count,
            'weeklyOffs': weekly_off_count,
            'holidays': holiday_count,
            'totalHours': round(total_hours, 2),
            'calendar': days_list
        })

    @action(detail=False, methods=['get'], url_path='my-history')
    def my_history(self, request):
        user = request.user
        emp_id = user.id if user.is_authenticated else 'EMP-001'
        records = AttendanceRecord.objects.filter(employee_id=emp_id).order_by('-date')
        return Response(AttendanceRecordSerializer(records, many=True).data)


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['leave_number', 'employee_name', 'department', 'leave_name']
    filterset_fields = ['status', 'employee_id']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return LeaveRequest.objects.none()
        if is_super_admin(user) or is_admin(user):
            return LeaveRequest.objects.all()
        if is_department_manager(user):
            dept_name = getattr(user, 'department_name', '')
            return LeaveRequest.objects.filter(department__iexact=dept_name) if dept_name else LeaveRequest.objects.filter(employee_id=user.id)
        return LeaveRequest.objects.filter(employee_id=user.id)

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = LeaveRequest.objects.filter(**filter_kwargs).first()
        if not obj:
            from rest_framework.exceptions import NotFound
            raise NotFound("Leave request not found.")
        user = self.request.user
        if not (is_super_admin(user) or is_admin(user)):
            if is_department_manager(user):
                dept_name = getattr(user, 'department_name', '')
                if dept_name and obj.department.lower() != dept_name.lower() and obj.employee_id != user.id:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("You do not have permission to access leave requests outside your department.")
            else:
                if obj.employee_id != user.id:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("You do not have permission to access another employee's leave request.")
        return obj

    def create(self, request, *args, **kwargs):
        from datetime import datetime, date, timedelta
        user = request.user
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)

        # Derive employee identity
        emp_id = user.id
        emp_name = user.name or f"{user.first_name} {user.last_name}".strip() or user.username
        dept = user.department_name or (user.department.name if user.department else 'General')

        target_emp_id = data.get('employeeId') or data.get('employee_id')
        if target_emp_id and target_emp_id != emp_id:
            if is_super_admin(user) or is_admin(user) or is_department_manager(user):
                target_user = User.objects.filter(id=target_emp_id).first()
                if target_user:
                    emp_id = target_user.id
                    emp_name = target_user.name or f"{target_user.first_name} {target_user.last_name}".strip() or target_user.username
                    dept = target_user.department_name or dept
            else:
                return Response({'error': 'Cannot apply leave on behalf of another employee.'}, status=status.HTTP_403_FORBIDDEN)

        data['employee_id'] = emp_id
        data['employee_name'] = emp_name
        data['department'] = dept

        from_date_str = data.get('fromDate') or data.get('from_date')
        to_date_str = data.get('toDate') or data.get('to_date')
        if not from_date_str or not to_date_str:
            return Response({'error': 'From Date and To Date are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from_dt = datetime.strptime(str(from_date_str)[:10], '%Y-%m-%d').date()
            to_dt = datetime.strptime(str(to_date_str)[:10], '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        if to_dt < from_dt:
            return Response({'error': 'To Date cannot be before From Date.'}, status=status.HTTP_400_BAD_REQUEST)

        data['from_date'] = str(from_dt)
        data['to_date'] = str(to_dt)

        # 1. Overlap validation
        overlapping = LeaveRequest.objects.filter(
            employee_id=emp_id,
            status__in=['Pending', 'Approved', 'Pending Manager'],
            from_date__lte=to_dt,
            to_date__gte=from_dt
        ).first()
        if overlapping:
            return Response({
                'error': f"You already have an existing {overlapping.status} leave ({overlapping.leave_number}) overlapping from {overlapping.from_date} to {overlapping.to_date}."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 2. Working days calculation (exclude Sundays & Holidays)
        is_half_day = bool(data.get('isHalfDay') or data.get('is_half_day') or False)
        if is_half_day:
            calculated_days = 0.5
        else:
            curr = from_dt
            working_days_count = 0
            holidays = set(Holiday.objects.filter(holiday_date__gte=from_dt, holiday_date__lte=to_dt).values_list('holiday_date', flat=True))
            while curr <= to_dt:
                if curr.weekday() != 6 and curr not in holidays:
                    working_days_count += 1
                curr += timedelta(days=1)
            calculated_days = float(working_days_count)

        if calculated_days <= 0:
            return Response({'error': 'Selected date range contains only holidays or non-working days.'}, status=status.HTTP_400_BAD_REQUEST)

        data['number_of_days'] = calculated_days

        # 3. Leave type & balance check
        lt_id = data.get('leaveTypeId') or data.get('leave_type_id') or 'LT-01'
        lt = LeaveType.objects.filter(id=lt_id).first() or LeaveType.objects.filter(leave_code=lt_id).first()
        if lt:
            data['leave_type_id'] = lt.id
            data['leave_name'] = lt.leave_name
        else:
            data['leave_name'] = data.get('leaveName') or data.get('leave_name') or 'Casual Leave'

        # Check balance
        bal = LeaveBalance.objects.filter(employee_id=emp_id, leave_type_id=data.get('leave_type_id')).first()
        if bal:
            if float(bal.available_balance) < calculated_days:
                return Response({
                    'error': f"Insufficient leave balance for {bal.leave_name}. Available: {bal.available_balance} days, Requested: {calculated_days} days."
                }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        leave = serializer.save()

        # Update pending balance
        if bal:
            bal.pending_approval = float(bal.pending_approval) + calculated_days
            bal.recalculate()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_leave(self, request, pk=None):
        leave = self.get_object()
        user = request.user

        # Strict Self-Approval Prevention
        if user.id == leave.employee_id:
            return Response({'error': 'Self-approval of leave requests is strictly prohibited.'}, status=status.HTTP_403_FORBIDDEN)

        # Permission check
        if not (is_super_admin(user) or is_admin(user) or is_department_manager(user) or getattr(user, 'can_approve_leaves', False)):
            return Response({'error': 'You do not have permission to approve leave requests.'}, status=status.HTTP_403_FORBIDDEN)

        leave.status = 'Approved'
        approver_name = user.name or f"{user.first_name} {user.last_name}".strip() or user.username
        leave.approved_by = approver_name
        leave.approved_date = timezone.now().date()
        remarks = request.data.get('remarks') or request.data.get('managerRemarks') or request.data.get('manager_remarks') or ''
        if remarks:
            leave.manager_remarks = remarks
        leave.save()

        # Deduct from LeaveBalance
        bal = LeaveBalance.objects.filter(employee_id=leave.employee_id, leave_type_id=leave.leave_type_id).first()
        if bal:
            num = float(leave.number_of_days)
            bal.pending_approval = max(0.0, float(bal.pending_approval) - num)
            bal.used = float(bal.used) + num
            bal.recalculate()

        # Update attendance records for each working day in the range
        from datetime import timedelta
        curr = leave.from_date
        while curr <= leave.to_date:
            if curr.weekday() != 6: # not Sunday
                att_rec, _ = AttendanceRecord.objects.get_or_create(
                    employee_id=leave.employee_id,
                    date=curr,
                    defaults={
                        'employee_name': leave.employee_name,
                        'department': leave.department,
                        'status': 'Half Day Leave' if leave.is_half_day else 'On Leave',
                        'remarks': f"Approved Leave: {leave.leave_name} ({leave.leave_number})"
                    }
                )
                if att_rec.status not in ['Present', 'Late']:
                    att_rec.status = 'Half Day Leave' if leave.is_half_day else 'On Leave'
                    att_rec.remarks = f"Approved Leave: {leave.leave_name} ({leave.leave_number})"
                    att_rec.save()
            curr += timedelta(days=1)

        return Response(LeaveRequestSerializer(leave).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_leave(self, request, pk=None):
        leave = self.get_object()
        user = request.user

        # Self-action block
        if user.id == leave.employee_id:
            return Response({'error': 'Self-action on leave requests is prohibited.'}, status=status.HTTP_403_FORBIDDEN)

        if not (is_super_admin(user) or is_admin(user) or is_department_manager(user) or getattr(user, 'can_approve_leaves', False)):
            return Response({'error': 'You do not have permission to reject leave requests.'}, status=status.HTTP_403_FORBIDDEN)

        leave.status = 'Rejected'
        approver_name = user.name or f"{user.first_name} {user.last_name}".strip() or user.username
        leave.approved_by = approver_name
        leave.approved_date = timezone.now().date()
        remarks = request.data.get('remarks') or request.data.get('managerRemarks') or request.data.get('manager_remarks') or ''
        if remarks:
            leave.manager_remarks = remarks
        leave.save()

        # Restore LeaveBalance
        bal = LeaveBalance.objects.filter(employee_id=leave.employee_id, leave_type_id=leave.leave_type_id).first()
        if bal:
            num = float(leave.number_of_days)
            bal.pending_approval = max(0.0, float(bal.pending_approval) - num)
            bal.recalculate()

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
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['request_number', 'employee_name']
    filterset_fields = ['status', 'employee_id']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return MissedPunchRequest.objects.none()
        if is_super_admin(user) or is_admin(user):
            return MissedPunchRequest.objects.all()
        if is_department_manager(user):
            dept_name = getattr(user, 'department_name', '')
            return MissedPunchRequest.objects.filter(employee_id__in=User.objects.filter(department_name__iexact=dept_name).values_list('id', flat=True)) if dept_name else MissedPunchRequest.objects.filter(employee_id=user.id)
        return MissedPunchRequest.objects.filter(employee_id=user.id)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_missed_punch(self, request, pk=None):
        mp = self.get_object()
        user = request.user
        if not (is_super_admin(user) or is_admin(user) or is_department_manager(user) or getattr(user, 'can_manage_attendance', False)):
            return Response({'error': 'You do not have permission to approve missed punch requests.'}, status=status.HTTP_403_FORBIDDEN)

        mp.status = 'Approved'
        mp.save()

        att, _ = AttendanceRecord.objects.get_or_create(
            employee_id=mp.employee_id,
            date=mp.date,
            defaults={
                'employee_name': mp.employee_name,
                'department': 'General',
                'status': 'Present',
                'remarks': f"Missed Punch Approved: {mp.request_number}"
            }
        )
        if mp.missing_punch_type in ['Check-In', 'check_in', 'In']:
            att.check_in = mp.requested_time
        else:
            att.check_out = mp.requested_time

        if att.check_in and att.check_out:
            try:
                from datetime import datetime
                t_in = datetime.strptime(att.check_in, '%H:%M')
                t_out = datetime.strptime(att.check_out, '%H:%M')
                diff = (t_out - t_in).total_seconds() / 3600.0
                if diff > 0:
                    att.total_hours = round(diff, 2)
            except Exception:
                pass
        att.status = 'Present'
        att.save()

        return Response(MissedPunchRequestSerializer(mp).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_missed_punch(self, request, pk=None):
        mp = self.get_object()
        user = request.user
        if not (is_super_admin(user) or is_admin(user) or is_department_manager(user) or getattr(user, 'can_manage_attendance', False)):
            return Response({'error': 'You do not have permission to reject missed punch requests.'}, status=status.HTTP_403_FORBIDDEN)
        mp.status = 'Rejected'
        mp.save()
        return Response(MissedPunchRequestSerializer(mp).data)


class AttendanceRegularizationViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRegularization.objects.all()
    serializer_class = AttendanceRegularizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['regularization_no', 'employee_name']
    filterset_fields = ['status', 'employee_id']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return AttendanceRegularization.objects.none()
        if is_super_admin(user) or is_admin(user):
            return AttendanceRegularization.objects.all()
        if is_department_manager(user):
            dept_name = getattr(user, 'department_name', '')
            return AttendanceRegularization.objects.filter(employee_id__in=User.objects.filter(department_name__iexact=dept_name).values_list('id', flat=True)) if dept_name else AttendanceRegularization.objects.filter(employee_id=user.id)
        return AttendanceRegularization.objects.filter(employee_id=user.id)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_regularization(self, request, pk=None):
        reg = self.get_object()
        user = request.user
        if not (is_super_admin(user) or is_admin(user) or is_department_manager(user) or getattr(user, 'can_manage_attendance', False)):
            return Response({'error': 'You do not have permission to approve regularization requests.'}, status=status.HTTP_403_FORBIDDEN)

        reg.status = 'Approved'
        reg.save()

        att, _ = AttendanceRecord.objects.get_or_create(
            employee_id=reg.employee_id,
            date=reg.date,
            defaults={
                'employee_name': reg.employee_name,
                'department': 'General',
                'status': reg.requested_status or 'Present',
                'check_in': reg.corrected_check_in,
                'check_out': reg.corrected_check_out,
                'remarks': f"Regularized: {reg.regularization_no} - {reg.reason}"
            }
        )
        if reg.corrected_check_in:
            att.check_in = reg.corrected_check_in
        if reg.corrected_check_out:
            att.check_out = reg.corrected_check_out
        att.status = reg.requested_status or 'Present'
        att.remarks = f"Regularized: {reg.regularization_no} - {reg.reason}"

        if att.check_in and att.check_out:
            try:
                from datetime import datetime
                t_in = datetime.strptime(att.check_in, '%H:%M')
                t_out = datetime.strptime(att.check_out, '%H:%M')
                diff = (t_out - t_in).total_seconds() / 3600.0
                if diff > 0:
                    att.total_hours = round(diff, 2)
            except Exception:
                pass
        att.save()

        return Response(AttendanceRegularizationSerializer(reg).data)


class OvertimeRecordViewSet(viewsets.ModelViewSet):
    queryset = OvertimeRecord.objects.all()
    serializer_class = OvertimeRecordSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['overtime_no', 'employee_name']
    filterset_fields = ['status', 'employee_id']

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_overtime(self, request, pk=None):
        ot = self.get_object()
        ot.status = 'Approved'
        ot.approved_by = request.data.get('approved_by') or request.data.get('approvedBy') or 'HR Manager'
        ot.save()
        return Response(OvertimeRecordSerializer(ot).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_overtime(self, request, pk=None):
        ot = self.get_object()
        ot.status = 'Rejected'
        ot.save()
        return Response(OvertimeRecordSerializer(ot).data)


class EarlyCheckoutRequestViewSet(viewsets.ModelViewSet):
    queryset = EarlyCheckoutRequest.objects.all()
    serializer_class = EarlyCheckoutRequestSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['request_number', 'employee_name']
    filterset_fields = ['status', 'employee_id']

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_early_checkout(self, request, pk=None):
        eco = self.get_object()
        eco.status = 'Approved'
        eco.save()
        return Response(EarlyCheckoutRequestSerializer(eco).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_early_checkout(self, request, pk=None):
        eco = self.get_object()
        eco.status = 'Rejected'
        eco.save()
        return Response(EarlyCheckoutRequestSerializer(eco).data)


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


class EmployeeAppraisalViewSet(viewsets.ModelViewSet):
    queryset = EmployeeAppraisal.objects.all()
    serializer_class = EmployeeAppraisalSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['appraisal_number', 'employee_id', 'employee_name', 'department', 'cycle_period']
    filterset_fields = ['status', 'department', 'cycle_period', 'employee_id']

    def perform_create(self, serializer):
        req_id = serializer.validated_data.get('id') or self.request.data.get('id')
        appraisal_no = serializer.validated_data.get('appraisal_number') or self.request.data.get('appraisalNumber')
        if not req_id or not appraisal_no:
            count = EmployeeAppraisal.objects.count() + 1
            if not req_id:
                req_id = f"APR-2026-{count:03d}"
            if not appraisal_no:
                appraisal_no = f"APR-2026-{count:03d}"
        serializer.save(id=req_id, appraisal_number=appraisal_no)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        appraisal = self.get_object()
        appraisal.status = 'Approved'
        appraisal.save()
        return Response(self.get_serializer(appraisal).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        appraisal = self.get_object()
        appraisal.status = 'Rejected'
        appraisal.save()
        return Response(self.get_serializer(appraisal).data)


class EmployeeDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from datetime import date, datetime
        import calendar
        from apps.projects.models import ProjectTask
        from apps.core.models import Notification

        user = request.user
        emp_id = request.query_params.get('employee_id') or request.query_params.get('employeeId') or user.id

        # Scope checking
        if emp_id != user.id and not (is_super_admin(user) or is_admin(user) or is_department_manager(user)):
            return Response({'error': 'Unauthorized to view another employee dashboard.'}, status=status.HTTP_403_FORBIDDEN)

        target_user = User.objects.filter(id=emp_id).first() or user
        today = date.today()

        # 1. Profile Details
        profile_data = {
            'id': target_user.id,
            'name': target_user.name or f"{target_user.first_name} {target_user.last_name}".strip() or target_user.username,
            'username': target_user.username,
            'email': target_user.email,
            'department': target_user.department_name or (target_user.department.name if target_user.department else 'General'),
            'designation': target_user.designation or 'Staff',
            'roleType': getattr(target_user, 'role_type', 'employee'),
            'workLocation': getattr(target_user, 'work_location', 'Main Plant & Works'),
            'avatar': getattr(target_user, 'avatar', None),
        }

        # 2. Today's Attendance
        today_att = AttendanceRecord.objects.filter(employee_id=emp_id, date=today).first()
        today_att_data = {
            'date': today.isoformat(),
            'checkIn': today_att.check_in if today_att else None,
            'checkOut': today_att.check_out if today_att else None,
            'totalHours': float(today_att.total_hours) if today_att else 0.0,
            'lateMinutes': today_att.late_minutes if today_att else 0,
            'status': today_att.status if today_att else 'Not Punched Today',
            'shiftName': today_att.shift_name if today_att else 'General Day Shift (09:00 - 18:00)',
            'canCheckIn': not (today_att and today_att.check_in),
            'canCheckOut': bool(today_att and today_att.check_in and not today_att.check_out),
        }

        # 3. Monthly Attendance Summary
        start_month = date(today.year, today.month, 1)
        month_records = AttendanceRecord.objects.filter(employee_id=emp_id, date__gte=start_month, date__lte=today)
        present_count = month_records.filter(status__in=['Present', 'Late']).count()
        late_count = month_records.filter(late_minutes__gt=0).count()
        total_month_hours = sum(float(r.total_hours or 0) for r in month_records)
        monthly_summary = {
            'month': today.strftime('%B %Y'),
            'presentDays': present_count,
            'lateDays': late_count,
            'totalHours': round(total_month_hours, 2),
            'attendanceRate': round((present_count / max(1, today.day)) * 100, 1)
        }

        # 4. Leave Balances
        balances = LeaveBalance.objects.filter(employee_id=emp_id, financial_year='2026-2027')
        leave_balances_data = LeaveBalanceSerializer(balances, many=True).data

        # 5. Pending Leaves
        pending_leaves = LeaveRequest.objects.filter(employee_id=emp_id, status__in=['Pending', 'Pending Manager'])[:5]
        pending_leaves_data = LeaveRequestSerializer(pending_leaves, many=True).data

        # 6. Tasks Breakdown
        user_tasks = ProjectTask.objects.filter(assigned_to_id=emp_id)
        due_today_str = today.strftime('%Y-%m-%d')
        total_tasks = user_tasks.count()
        completed_tasks = user_tasks.filter(status__in=['Completed', 'completed']).count()
        in_progress_tasks = user_tasks.filter(status__in=['In Progress', 'in_progress', 'Accepted']).count()
        due_today_tasks = user_tasks.filter(due_date=due_today_str).exclude(status__in=['Completed', 'completed']).count()
        overdue_tasks = user_tasks.filter(due_date__lt=due_today_str).exclude(due_date='').exclude(status__in=['Completed', 'completed']).count()

        tasks_summary = {
            'totalAssigned': total_tasks,
            'inProgress': in_progress_tasks,
            'dueToday': due_today_tasks,
            'overdue': overdue_tasks,
            'completed': completed_tasks,
            'recentTasks': [
                {
                    'id': t.id,
                    'taskNumber': t.task_number,
                    'title': t.title,
                    'status': t.status,
                    'priority': t.priority,
                    'progressPercent': t.progress_percent,
                    'dueDate': t.due_date,
                    'isOverdue': bool(t.due_date and t.due_date < due_today_str and t.status not in ['Completed', 'completed'])
                } for t in user_tasks.order_by('-updated_at')[:8]
            ]
        }

        # 7. Notifications
        notifs = Notification.objects.filter(is_read=False)[:5]
        notifications_data = [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.type,
                'priority': n.priority,
                'linkUrl': n.link_url,
                'createdAt': n.timestamp.strftime('%Y-%m-%d %H:%M') if n.timestamp else ''
            } for n in notifs
        ]

        # 8. Effective Permissions & Module Shortcuts
        eff_perms = compute_effective_permissions(target_user)
        module_shortcuts = []
        module_route_map = {
            'crm': {'label': 'CRM & Sales', 'href': '/crm', 'icon': 'ShoppingCart'},
            'projects': {'label': 'Projects & Tasks', 'href': '/projects/tasks', 'icon': 'CheckSquare'},
            'designer': {'label': 'Design & GA', 'href': '/designer', 'icon': 'Palette'},
            'purchase': {'label': 'Purchase Orders', 'href': '/purchase', 'icon': 'Box'},
            'store': {'label': 'Store & Stock', 'href': '/store', 'icon': 'Building'},
            'production': {'label': 'Production Jobs', 'href': '/production', 'icon': 'Factory'},
            'hr': {'label': 'HR & Attendance', 'href': '/hr/attendance', 'icon': 'Users'},
            'accounting': {'label': 'Accounts & Billing', 'href': '/accounting', 'icon': 'Landmark'},
        }
        for mod in eff_perms.get('allowed_modules', []):
            if mod in module_route_map:
                module_shortcuts.append({
                    'module': mod,
                    **module_route_map[mod]
                })

        return Response({
            'profile': profile_data,
            'todayAttendance': today_att_data,
            'monthlySummary': monthly_summary,
            'leaveBalances': leave_balances_data,
            'pendingLeaves': pending_leaves_data,
            'tasksSummary': tasks_summary,
            'notifications': notifications_data,
            'moduleShortcuts': module_shortcuts,
            'effectivePermissions': eff_perms,
        })



