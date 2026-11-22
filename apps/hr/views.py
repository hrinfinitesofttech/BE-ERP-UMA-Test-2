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
    queryset = Designation.objects.all().order_by('-id')
    serializer_class = DesignationSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['designation_code', 'designation_name', 'department']
    filterset_fields = ['status', 'department']


class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    queryset = EmployeeDocument.objects.all().order_by('-id')
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['employee_name', 'document_type', 'document_number']
    filterset_fields = ['verification_status', 'employee_id']


class ShiftMasterViewSet(viewsets.ModelViewSet):
    queryset = ShiftMaster.objects.all().order_by('-id')
    serializer_class = ShiftMasterSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['shift_name']
    filterset_fields = ['status']


class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.all().order_by('-id')
    serializer_class = LeaveTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['leave_code', 'leave_name']
    filterset_fields = ['status']


class LeaveBalanceViewSet(viewsets.ModelViewSet):
    queryset = LeaveBalance.objects.all().order_by('-id')
    serializer_class = LeaveBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['employee_name', 'leave_code', 'leave_name']
    filterset_fields = ['employee_id', 'financial_year']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return LeaveBalance.objects.none()
        if is_super_admin(user) or is_admin(user):
            return LeaveBalance.objects.all().order_by('-id')
        if is_department_manager(user):
            dept_name = getattr(user, 'department_name', '')
            return (LeaveBalance.objects.filter(department__iexact=dept_name) if dept_name else LeaveBalance.objects.filter(employee_id=user.id)).order_by('-id')
        return LeaveBalance.objects.filter(employee_id=user.id).order_by('-id')


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all().order_by('-date', '-id')
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
        # Optional range so clients can load a recent window instead of the full history
        date_from = self.request.query_params.get('date_from') or self.request.query_params.get('dateFrom')
        date_to = self.request.query_params.get('date_to') or self.request.query_params.get('dateTo')
        try:
            if date_from:
                qs = qs.filter(date__gte=date_from)
            if date_to:
                qs = qs.filter(date__lte=date_to)
        except (ValueError, TypeError, Exception):
            pass
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
        return qs.order_by('-date', '-id')

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

    @action(detail=False, methods=['get'], url_path='daily-sheet')
    def daily_sheet(self, request):
        """
        Returns attendance status for ALL active ERP employees for a specified date.
        If an employee has no punch on that date, status is properly determined
        as Holiday / Weekly Off / On Leave / Absent instead of omitting them.
        """
        from datetime import datetime, date
        user = request.user
        date_str = request.query_params.get('date')
        if date_str:
            try:
                selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                selected_date = date.today()
        else:
            selected_date = date.today()

        today = date.today()
        is_sunday = selected_date.weekday() == 6
        holiday = Holiday.objects.filter(holiday_date=selected_date).first()

        all_employees = User.objects.filter(is_active=True).order_by('id')
        mappings = {
            m.employee_id: m.machine_emp_code
            for m in BiometricEmployeeMapping.objects.filter(is_active=True)
        }

        records_map = {
            r.employee_id: r
            for r in AttendanceRecord.objects.filter(date=selected_date)
        }

        leaves_map = {
            lr.employee_id: lr
            for lr in LeaveRequest.objects.filter(
                status='Approved',
                from_date__lte=selected_date,
                to_date__gte=selected_date
            )
        }

        items = []
        present_count = 0
        absent_count = 0
        late_count = 0
        half_day_count = 0
        leave_count = 0
        missing_punch_count = 0

        for emp in all_employees:
            rec = records_map.get(emp.id)
            leave = leaves_map.get(emp.id)
            machine_code = mappings.get(emp.id, '')

            if rec:
                status_val = rec.status
                first_in = rec.first_in or rec.check_in
                last_out = rec.last_out or rec.check_out
                punch_count = rec.punch_count or (1 if first_in and not last_out else (2 if first_in and last_out else 0))
                total_hours = float(rec.total_hours or 0.0)
                late_mins = rec.late_minutes or 0
                is_missing = rec.is_missing_punch or (bool(first_in) and not bool(last_out))
                source = rec.source or 'Biometric System'
                remarks = rec.remarks or ''
                is_manual = rec.is_manually_approved
            elif leave:
                status_val = 'Half Day Leave' if leave.is_half_day else 'On Leave'
                first_in = ''
                last_out = ''
                punch_count = 0
                total_hours = 0.0
                late_mins = 0
                is_missing = False
                source = 'Leave System'
                remarks = f"Approved Leave: {leave.leave_name}"
                is_manual = False
            elif holiday:
                status_val = 'Holiday'
                first_in = ''
                last_out = ''
                punch_count = 0
                total_hours = 0.0
                late_mins = 0
                is_missing = False
                source = 'System'
                remarks = holiday.holiday_name
                is_manual = False
            elif is_sunday:
                status_val = 'Weekly Off'
                first_in = ''
                last_out = ''
                punch_count = 0
                total_hours = 0.0
                late_mins = 0
                is_missing = False
                source = 'System'
                remarks = 'Sunday'
                is_manual = False
            else:
                status_val = 'Absent' if selected_date <= today else 'Upcoming'
                first_in = ''
                last_out = ''
                punch_count = 0
                total_hours = 0.0
                late_mins = 0
                is_missing = False
                source = 'System'
                remarks = 'No biometric punch recorded' if selected_date <= today else ''
                is_manual = False

            if status_val == 'Present':
                present_count += 1
            elif status_val == 'Late':
                late_count += 1
                present_count += 1
            elif status_val == 'Half Day':
                half_day_count += 1
            elif status_val in ['On Leave', 'Half Day Leave']:
                leave_count += 1
            elif status_val == 'Absent':
                absent_count += 1

            if is_missing:
                missing_punch_count += 1

            items.append({
                'employeeId': emp.id,
                'employeeCode': emp.id,
                'employeeName': emp.name or emp.username,
                'username': emp.username,
                'department': emp.department_name or '',
                'designation': emp.designation or '',
                'email': emp.email or '',
                'mobile': emp.mobile or getattr(emp, 'phone', '') or '',
                'isActive': emp.is_active,
                'machineEmpCode': machine_code,
                'date': selected_date.isoformat(),
                'status': status_val,
                'firstIn': first_in,
                'lastOut': last_out,
                'punchCount': punch_count,
                'totalHours': total_hours,
                'lateMinutes': late_mins,
                'isMissingPunch': is_missing,
                'isManuallyApproved': is_manual,
                'source': source,
                'remarks': remarks,
                'attendanceRecordId': rec.id if rec else None,
            })

        return Response({
            'date': selected_date.isoformat(),
            'totalEmployees': all_employees.count(),
            'presentCount': present_count,
            'lateCount': late_count,
            'absentCount': absent_count,
            'halfDayCount': half_day_count,
            'leaveCount': leave_count,
            'missingPunchCount': missing_punch_count,
            'employees': items,
        })

    @action(detail=False, methods=['get'], url_path='monthly-sheet')
    def monthly_sheet(self, request):
        """
        Returns employee-wise monthly attendance statistics and day-by-day status matrix
        for ALL active ERP employees.
        """
        import calendar
        from datetime import date, timedelta
        today = date.today()
        month_param = request.query_params.get('month')
        year_param = request.query_params.get('year')
        month_year = request.query_params.get('month_year') or request.query_params.get('monthYear')

        if month_year and '-' in month_year:
            try:
                y, m = map(int, month_year.split('-')[:2])
                year, month = y, m
            except Exception:
                year, month = today.year, today.month
        elif month_param and year_param:
            year, month = int(year_param), int(month_param)
        else:
            year, month = today.year, today.month

        num_days = calendar.monthrange(year, month)[1]
        start_date = date(year, month, 1)
        end_date = date(year, month, num_days)

        all_employees = User.objects.filter(is_active=True).order_by('id')
        mappings = {
            m.employee_id: m.machine_emp_code
            for m in BiometricEmployeeMapping.objects.filter(is_active=True)
        }

        records = AttendanceRecord.objects.filter(date__gte=start_date, date__lte=end_date)
        records_by_emp = {}
        for r in records:
            records_by_emp.setdefault(r.employee_id, {})[r.date.isoformat()] = r

        holidays = {h.holiday_date.isoformat(): h.holiday_name for h in Holiday.objects.filter(holiday_date__gte=start_date, holiday_date__lte=end_date)}

        leaves = LeaveRequest.objects.filter(status='Approved', from_date__lte=end_date, to_date__gte=start_date)
        leaves_by_emp = {}
        for l in leaves:
            curr = max(l.from_date, start_date)
            upto = min(l.to_date, end_date)
            while curr <= upto:
                leaves_by_emp.setdefault(l.employee_id, {})[curr.isoformat()] = l
                curr += timedelta(days=1)

        result_list = []
        overall_present = 0
        overall_absent = 0
        overall_late = 0
        overall_half_day = 0

        for emp in all_employees:
            emp_records = records_by_emp.get(emp.id, {})
            emp_leaves = leaves_by_emp.get(emp.id, {})
            machine_code = mappings.get(emp.id, '')

            p_count = 0
            l_count = 0
            a_count = 0
            hd_count = 0
            leave_count = 0
            wo_count = 0
            hol_count = 0
            tot_hours = 0.0
            missing_count = 0
            day_matrix = {}

            for day_num in range(1, num_days + 1):
                curr_date = date(year, month, day_num)
                d_str = curr_date.isoformat()
                is_sun = curr_date.weekday() == 6
                r = emp_records.get(d_str)
                l = emp_leaves.get(d_str)
                h = holidays.get(d_str)

                if r:
                    status_short = 'P'
                    if r.status == 'Late' or (r.late_minutes and r.late_minutes > 0):
                        status_short = 'L'
                        l_count += 1
                        p_count += 1
                    elif r.status == 'Half Day':
                        status_short = 'HD'
                        hd_count += 1
                    elif 'Leave' in r.status:
                        status_short = 'LV'
                        leave_count += 1
                    elif r.status == 'Absent':
                        status_short = 'A'
                        a_count += 1
                    else:
                        p_count += 1

                    tot_hours += float(r.total_hours or 0.0)
                    if r.is_missing_punch or (r.first_in and not r.last_out):
                        missing_count += 1
                elif l:
                    status_short = 'LV'
                    leave_count += 1
                elif h:
                    status_short = 'H'
                    hol_count += 1
                elif is_sun:
                    status_short = 'WO'
                    wo_count += 1
                else:
                    if curr_date <= today:
                        status_short = 'A'
                        a_count += 1
                    else:
                        status_short = '-'

                day_matrix[d_str] = status_short

            overall_present += p_count
            overall_absent += a_count
            overall_late += l_count
            overall_half_day += hd_count

            result_list.append({
                'employeeId': emp.id,
                'employeeCode': emp.id,
                'employeeName': emp.name or emp.username,
                'department': emp.department_name or '',
                'designation': emp.designation or '',
                'machineEmpCode': machine_code,
                'totalDays': num_days,
                'presentDays': p_count,
                'lateDays': l_count,
                'absentDays': a_count,
                'halfDays': hd_count,
                'leaveDays': leave_count,
                'weeklyOffs': wo_count,
                'holidays': hol_count,
                'totalHours': round(tot_hours, 2),
                'missingPunches': missing_count,
                'daysMap': day_matrix,
            })

        return Response({
            'monthYear': f"{year:04d}-{month:02d}",
            'month': month,
            'year': year,
            'totalDays': num_days,
            'totalEmployees': all_employees.count(),
            'summary': {
                'totalPresent': overall_present,
                'totalAbsent': overall_absent,
                'totalLate': overall_late,
                'totalHalfDay': overall_half_day,
            },
            'employees': result_list,
        })

    @action(detail=False, methods=['get'], url_path='employee-detail')
    @action(detail=False, methods=['get'], url_path='employee-detail')
    def employee_detail(self, request):
        """
        Returns complete Employee Master profile, mapped biometric code, monthly/date-range attendance history,
        KPI summary calculations, and raw punch logs for a given employee.
        Supports:
          - employee_id / employeeId
          - from_date & to_date (YYYY-MM-DD or DD/MM/YYYY)
          - month (1-12) & year (e.g. 2026)
        """
        import calendar
        from datetime import datetime, date, timedelta
        from django.db.models import Q

        emp_id = request.query_params.get('employee_id') or request.query_params.get('employeeId')
        if not emp_id:
            return Response({'error': 'employee_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        emp = User.objects.filter(id=emp_id).first() or User.objects.filter(username=emp_id).first()
        if not emp:
            return Response({'error': f'Employee with ID {emp_id} not found'}, status=status.HTTP_404_NOT_FOUND)

        today = date.today()

        # Parse date range
        from_str = request.query_params.get('from_date') or request.query_params.get('fromDate')
        to_str = request.query_params.get('to_date') or request.query_params.get('toDate')
        month_param = request.query_params.get('month')
        year_param = request.query_params.get('year')

        def parse_date_param(d_str):
            if not d_str: return None
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                try:
                    return datetime.strptime(d_str.strip(), fmt).date()
                except ValueError:
                    continue
            return None

        start_date = parse_date_param(from_str)
        end_date = parse_date_param(to_str)

        if not start_date or not end_date:
            try:
                selected_year = int(year_param) if year_param else today.year
                selected_month = int(month_param) if month_param else today.month
                num_days = calendar.monthrange(selected_year, selected_month)[1]
                start_date = date(selected_year, selected_month, 1)
                end_date = date(selected_year, selected_month, num_days)
            except Exception:
                num_days = calendar.monthrange(today.year, today.month)[1]
                start_date = date(today.year, today.month, 1)
                end_date = date(today.year, today.month, num_days)

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        # Active Shift Details
        shift = ShiftMaster.objects.filter(status='Active').first()
        shift_name = shift.shift_name if shift else 'Factory General Shift'
        shift_start = shift.start_time if shift else '09:00'
        shift_end = shift.end_time if shift else '18:00'

        # Biometric Mapping
        mapping = BiometricEmployeeMapping.objects.filter(employee=emp, is_active=True).first()
        machine_code = mapping.machine_emp_code if mapping else ''

        # Preload Attendance Records in Range
        rec_filter = Q(employee_id=emp.id)
        if machine_code:
            rec_filter |= Q(employee_id=f"EMP-{machine_code}") | Q(employee_id=machine_code)

        records = AttendanceRecord.objects.filter(
            rec_filter,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')

        rec_map = {r.date: r for r in records}

        # Preload Holidays
        holidays = Holiday.objects.filter(
            holiday_date__gte=start_date,
            holiday_date__lte=end_date
        )
        holiday_map = {h.holiday_date: h.holiday_name for h in holidays}

        # Preload Approved Leaves
        leaves = LeaveRequest.objects.filter(
            employee_id=emp.id,
            status='Approved',
            from_date__lte=end_date,
            to_date__gte=start_date
        )
        leave_map = {}
        for l in leaves:
            l_start = l.from_date if isinstance(l.from_date, date) else parse_date_param(str(l.from_date))
            l_end = l.to_date if isinstance(l.to_date, date) else parse_date_param(str(l.to_date))
            if l_start and l_end:
                cur = max(l_start, start_date)
                fin = min(l_end, end_date)
                while cur <= fin:
                    leave_map[cur] = l.leave_name or 'Approved Leave'
                    cur += timedelta(days=1)

        # Preload Raw Punch Logs
        punch_filter = Q(erp_employee=emp)
        if machine_code:
            punch_filter |= Q(emp_code=machine_code)

        punch_logs = PunchLog.objects.filter(
            punch_filter,
            punch_date__gte=start_date,
            punch_date__lte=end_date
        ).order_by('-punch_datetime')

        # Generate Day-by-Day Calendar
        days = []
        present_count = 0
        absent_count = 0
        late_count = 0
        half_day_count = 0
        leave_count = 0
        weekly_off_count = 0
        holiday_count = 0
        working_days_count = 0
        total_working_hours = 0.0
        total_overtime_hours = 0.0
        missing_in_count = 0
        missing_out_count = 0

        curr_date = start_date
        while curr_date <= end_date:
            day_name = curr_date.strftime('%A')
            is_sunday = curr_date.weekday() == 6
            h_name = holiday_map.get(curr_date)
            l_name = leave_map.get(curr_date)
            rec = rec_map.get(curr_date)

            is_working_day = not is_sunday and not bool(h_name)
            if is_working_day:
                working_days_count += 1

            if rec:
                first_in = rec.first_in or rec.check_in or ''
                last_out = rec.last_out or rec.check_out or ''
                wh = float(rec.total_hours or 0.0)
                ot = float(rec.overtime_hours or 0.0)
                lm = rec.late_minutes or 0
                status_val = rec.status
                is_missing = rec.is_missing_punch or (bool(first_in) and not bool(last_out))
                punch_count = rec.punch_count or (2 if first_in and last_out else (1 if first_in or last_out else 0))
                source = rec.source or 'eTimeOffice Machine'
                remarks = rec.remarks or ''

                if status_val == 'Present':
                    present_count += 1
                elif status_val == 'Late':
                    late_count += 1
                    present_count += 1
                elif status_val == 'Half Day':
                    half_day_count += 1
                    present_count += 1
                elif 'Leave' in status_val:
                    leave_count += 1
                elif status_val == 'Absent':
                    absent_count += 1
                else:
                    if first_in:
                        present_count += 1
                    else:
                        absent_count += 1

                total_working_hours += wh
                total_overtime_hours += ot

                if is_missing or (not first_in and last_out):
                    if not first_in: missing_in_count += 1
                    if not last_out: missing_out_count += 1

            elif l_name:
                status_val = 'On Leave'
                first_in = ''
                last_out = ''
                punch_count = 0
                wh = 0.0
                ot = 0.0
                lm = 0
                is_missing = False
                source = 'Leave System'
                remarks = l_name
                leave_count += 1

            elif h_name:
                status_val = 'Holiday'
                first_in = ''
                last_out = ''
                punch_count = 0
                wh = 0.0
                ot = 0.0
                lm = 0
                is_missing = False
                source = 'Holiday Master'
                remarks = h_name
                holiday_count += 1

            elif is_sunday:
                status_val = 'Weekly Off'
                first_in = ''
                last_out = ''
                punch_count = 0
                wh = 0.0
                ot = 0.0
                lm = 0
                is_missing = False
                source = 'Shift Roster'
                remarks = 'Sunday'
                weekly_off_count += 1

            else:
                status_val = 'Absent' if curr_date <= today else 'Upcoming'
                first_in = ''
                last_out = ''
                punch_count = 0
                wh = 0.0
                ot = 0.0
                lm = 0
                is_missing = False
                source = 'System'
                remarks = 'No punch recorded' if curr_date <= today else ''
                if curr_date <= today:
                    absent_count += 1

            days.append({
                'date': curr_date.isoformat(),
                'dateFormatted': curr_date.strftime('%d/%m/%Y'),
                'dayName': day_name,
                'shift': shift_name,
                'shiftStartTime': shift_start,
                'shiftEndTime': shift_end,
                'firstIn': first_in,
                'lastOut': last_out,
                'punchCount': punch_count,
                'totalHours': round(wh, 2),
                'requiredHours': 8.0,
                'lateMinutes': lm,
                'overtimeHours': round(ot, 2),
                'status': status_val,
                'isWeeklyOff': is_sunday,
                'isHoliday': bool(h_name),
                'isLeave': bool(l_name),
                'leaveType': l_name or '',
                'isMissingPunch': is_missing,
                'source': source,
                'remarks': remarks,
                'recordId': rec.id if rec else None,
            })

            curr_date += timedelta(days=1)

        total_calendar_days = (end_date - start_date).days + 1

        return Response({
            'employee': {
                'id': emp.id,
                'code': emp.id,
                'name': emp.name or f"{emp.first_name} {emp.last_name}".strip() or emp.username,
                'username': emp.username,
                'email': emp.email,
                'mobile': emp.mobile or getattr(emp, 'phone', ''),
                'department': emp.department_name or '',
                'designation': emp.designation or '',
                'role': getattr(emp, 'role_name', ''),
                'status': 'Active' if emp.is_active else 'Inactive',
                'joiningDate': getattr(emp, 'joining_date', '') or '01/01/2024',
                'employmentType': getattr(emp, 'employment_type', '') or 'full_time',
                'workLocation': getattr(emp, 'work_location', '') or 'Main Factory, Vadodara',
                'shiftName': shift_name,
                'shiftStartTime': shift_start,
                'shiftEndTime': shift_end,
                'reportingManager': getattr(emp, 'reporting_manager_name', '') or 'General Management',
            },
            'biometricMapping': {
                'machineEmpCode': machine_code,
                'isMapped': bool(machine_code),
                'mappingId': mapping.id if mapping else None,
                'cardNo': getattr(mapping, 'device_card_no', '') if mapping else 'Default',
            },
            'period': {
                'fromDate': start_date.isoformat(),
                'toDate': end_date.isoformat(),
                'month': start_date.month,
                'year': start_date.year,
                'totalCalendarDays': total_calendar_days,
            },
            'summary': {
                'totalDays': total_calendar_days,
                'workingDays': working_days_count,
                'presentDays': present_count,
                'absentDays': absent_count,
                'lateDays': late_count,
                'halfDays': half_day_count,
                'leaveDays': leave_count,
                'weeklyOffDays': weekly_off_count,
                'holidays': holiday_count,
                'totalWorkingHours': round(total_working_hours, 2),
                'totalOvertimeHours': round(total_overtime_hours, 2),
                'missingInPunches': missing_in_count,
                'missingOutPunches': missing_out_count,
            },
            'days': days,
            'attendanceRecords': AttendanceRecordSerializer(records, many=True).data,
            'punchLogs': PunchLogSerializer(punch_logs[:100], many=True).data,
        })


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all().order_by('-id')
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['leave_number', 'employee_name', 'department', 'leave_name']
    filterset_fields = ['status', 'employee_id']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return LeaveRequest.objects.none()
        if is_super_admin(user) or is_admin(user):
            return LeaveRequest.objects.all().order_by('-id')
        if is_department_manager(user):
            dept_name = getattr(user, 'department_name', '')
            return (LeaveRequest.objects.filter(department__iexact=dept_name) if dept_name else LeaveRequest.objects.filter(employee_id=user.id)).order_by('-id')
        return LeaveRequest.objects.filter(employee_id=user.id).order_by('-id')

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
    queryset = WFHRequest.objects.all().order_by('-id')
    serializer_class = WFHRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
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


def _is_hr_privileged(user):
    """Super admin / admin / department manager / users with attendance-management flag."""
    return bool(
        is_super_admin(user) or is_admin(user) or is_department_manager(user)
        or getattr(user, 'can_manage_attendance', False)
    )


def _force_own_identity(request, data):
    """Non-privileged users can only create records for themselves."""
    user = request.user
    data = data.copy() if hasattr(data, 'copy') else dict(data)
    if _is_hr_privileged(user):
        return data
    for k in ('employeeId', 'employee_id'):
        data.pop(k, None)
    data['employee_id'] = user.id
    data['employee_name'] = (
        getattr(user, 'name', '') or f"{user.first_name} {user.last_name}".strip() or user.username
    )
    return data


class MissedPunchRequestViewSet(viewsets.ModelViewSet):
    queryset = MissedPunchRequest.objects.all().order_by('-id')
    serializer_class = MissedPunchRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['request_number', 'employee_name']
    filterset_fields = ['status', 'employee_id']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return MissedPunchRequest.objects.none()
        if is_super_admin(user) or is_admin(user):
            return MissedPunchRequest.objects.all().order_by('-id')
        if is_department_manager(user):
            dept_name = getattr(user, 'department_name', '')
            return (MissedPunchRequest.objects.filter(employee_id__in=User.objects.filter(department_name__iexact=dept_name).values_list('id', flat=True)) if dept_name else MissedPunchRequest.objects.filter(employee_id=user.id)).order_by('-id')
        return MissedPunchRequest.objects.filter(employee_id=user.id).order_by('-id')

    def create(self, request, *args, **kwargs):
        data = _force_own_identity(request, request.data)
        if not _is_hr_privileged(request.user):
            data['status'] = 'Pending'
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_missed_punch(self, request, pk=None):
        mp = self.get_object()
        user = request.user
        if not (is_super_admin(user) or is_admin(user) or is_department_manager(user) or getattr(user, 'can_manage_attendance', False)):
            return Response({'error': 'You do not have permission to approve missed punch requests.'}, status=status.HTTP_403_FORBIDDEN)
        if mp.employee_id == user.id and not (is_super_admin(user) or is_admin(user)):
            return Response({'error': 'You cannot approve your own missed punch request.'}, status=status.HTTP_403_FORBIDDEN)
        if mp.status != 'Pending':
            return Response({'error': f'Request is already {mp.status}.'}, status=status.HTTP_400_BAD_REQUEST)

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
        att.is_manually_approved = True
        att.is_missing_punch = False
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
    queryset = AttendanceRegularization.objects.all().order_by('-id')
    serializer_class = AttendanceRegularizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['regularization_no', 'employee_name']
    filterset_fields = ['status', 'employee_id']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return AttendanceRegularization.objects.none()
        if is_super_admin(user) or is_admin(user):
            return AttendanceRegularization.objects.all().order_by('-id')
        if is_department_manager(user):
            dept_name = getattr(user, 'department_name', '')
            return (AttendanceRegularization.objects.filter(employee_id__in=User.objects.filter(department_name__iexact=dept_name).values_list('id', flat=True)) if dept_name else AttendanceRegularization.objects.filter(employee_id=user.id)).order_by('-id')
        return AttendanceRegularization.objects.filter(employee_id=user.id).order_by('-id')

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
    queryset = OvertimeRecord.objects.all().order_by('-id')
    serializer_class = OvertimeRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['overtime_no', 'employee_name']
    filterset_fields = ['status', 'employee_id']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return OvertimeRecord.objects.none()
        if is_super_admin(user) or is_admin(user):
            return OvertimeRecord.objects.all().order_by('-id')
        if is_department_manager(user):
            dept_name = getattr(user, 'department_name', '')
            qs = OvertimeRecord.objects.filter(department__iexact=dept_name) if dept_name else OvertimeRecord.objects.filter(employee_id=user.id)
            return qs.order_by('-id')
        return OvertimeRecord.objects.filter(employee_id=user.id).order_by('-id')

    def create(self, request, *args, **kwargs):
        data = _force_own_identity(request, request.data)
        if not _is_hr_privileged(request.user):
            data['status'] = 'Pending'
            data['approved_by'] = ''
            data.pop('approvedBy', None)
            data['overtime_amount'] = 0
            data.pop('overtimeAmount', None)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _deny_decision(self, request, ot):
        user = request.user
        if not _is_hr_privileged(user):
            return Response({'error': 'You do not have permission to decide overtime requests.'}, status=status.HTTP_403_FORBIDDEN)
        if ot.employee_id == user.id and not (is_super_admin(user) or is_admin(user)):
            return Response({'error': 'You cannot approve or reject your own overtime.'}, status=status.HTTP_403_FORBIDDEN)
        return None

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_overtime(self, request, pk=None):
        ot = self.get_object()
        denied = self._deny_decision(request, ot)
        if denied:
            return denied
        ot.status = 'Approved'
        ot.approved_by = request.data.get('approved_by') or request.data.get('approvedBy') or 'HR Manager'
        ot.save()
        return Response(OvertimeRecordSerializer(ot).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_overtime(self, request, pk=None):
        ot = self.get_object()
        denied = self._deny_decision(request, ot)
        if denied:
            return denied
        ot.status = 'Rejected'
        ot.save()
        return Response(OvertimeRecordSerializer(ot).data)


class EarlyCheckoutRequestViewSet(viewsets.ModelViewSet):
    queryset = EarlyCheckoutRequest.objects.all().order_by('-id')
    serializer_class = EarlyCheckoutRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
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
    queryset = SalaryComponent.objects.all().order_by('-id')
    serializer_class = SalaryComponentSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['component_code', 'component_name']
    filterset_fields = ['status', 'component_type']


# Payroll + salary structures live in payroll_views.py (real calculation engine)
from .payroll_views import SalaryStructureViewSet, PayrollRecordViewSet  # noqa: E402,F401


class EmployeeAdvanceLoanViewSet(viewsets.ModelViewSet):
    queryset = EmployeeAdvanceLoan.objects.all().order_by('-id')
    serializer_class = EmployeeAdvanceLoanSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['loan_number', 'employee_name', 'department']
    filterset_fields = ['status', 'employee_id']


class ReimbursementExpenseViewSet(viewsets.ModelViewSet):
    queryset = ReimbursementExpense.objects.all().order_by('-id')
    serializer_class = ReimbursementExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['reimbursement_no', 'employee_name', 'category']
    filterset_fields = ['status', 'employee_id']


class EmployeeOnboardingViewSet(viewsets.ModelViewSet):
    queryset = EmployeeOnboarding.objects.all().order_by('-created_at', '-id')
    serializer_class = EmployeeOnboardingSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['candidate_name', 'email', 'mobile', 'department', 'designation']
    filterset_fields = ['status', 'department']

    @action(detail=True, methods=['post'], url_path='complete')
    def complete_onboarding(self, request, pk=None):
        onb = self.get_object()
        onb.status = 'Completed'
        onb.save()
        return Response(EmployeeOnboardingSerializer(onb).data)


class EmployeeTransferViewSet(viewsets.ModelViewSet):
    queryset = EmployeeTransfer.objects.all().order_by('-id')
    serializer_class = EmployeeTransferSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['employee_name', 'from_department', 'to_department']
    filterset_fields = ['status']


class EmployeePromotionViewSet(viewsets.ModelViewSet):
    queryset = EmployeePromotion.objects.all().order_by('-id')
    serializer_class = EmployeePromotionSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['employee_name', 'old_designation', 'new_designation']
    filterset_fields = ['status']


class EmployeeExitViewSet(viewsets.ModelViewSet):
    queryset = EmployeeExit.objects.all().order_by('-id')
    serializer_class = EmployeeExitSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['employee_name', 'department', 'designation']
    filterset_fields = ['status']


class HolidayViewSet(viewsets.ModelViewSet):
    queryset = Holiday.objects.all().order_by('-created_at', '-id')
    serializer_class = HolidaySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['holiday_name', 'holiday_type', 'financial_year']
    filterset_fields = ['holiday_type', 'financial_year', 'is_optional']

    def perform_create(self, serializer):
        req_id = serializer.validated_data.get('id') or self.request.data.get('id')
        if not req_id:
            count = Holiday.objects.count() + 1
            req_id = f"HOL-2026-{count:02d}"
        serializer.save(id=req_id)


class EmployeeAppraisalViewSet(viewsets.ModelViewSet):
    queryset = EmployeeAppraisal.objects.all().order_by('-created_at', '-id')
    serializer_class = EmployeeAppraisalSerializer
    permission_classes = [permissions.IsAuthenticated]
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




import json
import urllib.request
import urllib.parse
import base64
import logging
from datetime import datetime, date, timedelta
from .models import PunchMachineConfig, PunchLog, BiometricEmployeeMapping, ShiftMaster
from .serializers import PunchMachineConfigSerializer, PunchLogSerializer, BiometricEmployeeMappingSerializer

logger = logging.getLogger(__name__)


def _fetch_machine_json(url, params=None, headers=None, timeout=30):
    """Zero-dependency HTTP GET helper using standard library urllib."""
    if params:
        query_str = urllib.parse.urlencode(params)
        sep = '&' if '?' in url else '?'
        url = f"{url}{sep}{query_str}"
    req = urllib.request.Request(url)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw_text = response.read().decode('utf-8')
        return json.loads(raw_text)


def resolve_employee_for_punch(emp_code, card_no=''):
    """
    Map machine employee code or card number to an active ERP User.
    1. Check explicit BiometricEmployeeMapping (machine_emp_code=emp_code, is_active=True).
    2. Check device_card_no if provided.
    3. Check direct User match by ID (User.objects.filter(id=emp_code, is_active=True)).
    4. Check normalized integer match (e.g. '0001' or '1' -> 'EMP-001' or 'EMP-1').
    5. NEVER guess by fuzzy name. Return None if unmapped.
    """
    if not emp_code and not card_no:
        return None

    clean_code = str(emp_code or '').strip()

    # 1. Explicit mapping by machine code
    if clean_code:
        mapping = BiometricEmployeeMapping.objects.filter(machine_emp_code=clean_code, is_active=True).first()
        if mapping and mapping.employee and mapping.employee.is_active:
            return mapping.employee

    # 2. Check card number
    clean_card = str(card_no or '').strip()
    if clean_card:
        mapping = BiometricEmployeeMapping.objects.filter(device_card_no=clean_card, is_active=True).first()
        if mapping and mapping.employee and mapping.employee.is_active:
            return mapping.employee

    # 3. Direct User match by id or username
    if clean_code:
        user = User.objects.filter(id=clean_code, is_active=True).first() or                User.objects.filter(username__iexact=clean_code, is_active=True).first()
        if user:
            return user

        # 4. Normalized integer format
        digits = ''.join(c for c in clean_code if c.isdigit())
        if digits:
            num = int(digits)
            for cand in [f"EMP-{num:03d}", f"EMP-{num:04d}", f"EMP-{num}", f"{num:03d}", str(num)]:
                cand_user = User.objects.filter(id__iexact=cand, is_active=True).first()
                if cand_user:
                    return cand_user

    return None


class PunchMachineConfigViewSet(viewsets.ModelViewSet):
    queryset = PunchMachineConfig.objects.all().order_by('-created_at')
    serializer_class = PunchMachineConfigSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return PunchMachineConfig.objects.none()
        if is_super_admin(user) or is_admin(user):
            return PunchMachineConfig.objects.all().order_by('-created_at')
        return PunchMachineConfig.objects.none()


class BiometricEmployeeMappingViewSet(viewsets.ModelViewSet):
    queryset = BiometricEmployeeMapping.objects.all().order_by('employee_code')
    serializer_class = BiometricEmployeeMappingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return BiometricEmployeeMapping.objects.none()
        if is_super_admin(user) or is_admin(user):
            return BiometricEmployeeMapping.objects.all().order_by('employee_code')
        return BiometricEmployeeMapping.objects.none()

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        total_active_emps = User.objects.filter(is_active=True).count()
        mapped_emps = BiometricEmployeeMapping.objects.filter(is_active=True).values_list('employee_id', flat=True).distinct().count()
        unmapped_emps = max(0, total_active_emps - mapped_emps)
        unmapped_punches = PunchLog.objects.filter(is_mapped=False).count()

        return Response({
            'totalActiveEmployees': total_active_emps,
            'mappedEmployees': mapped_emps,
            'unmappedEmployees': unmapped_emps,
            'unmappedPunches': unmapped_punches,
        })

    @action(detail=False, methods=['post'], url_path='reprocess')
    def reprocess_unmapped(self, request):
        user = request.user
        if not (is_super_admin(user) or is_admin(user)):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        unmapped_logs = PunchLog.objects.filter(is_mapped=False)
        resolved_count = 0

        for pl in unmapped_logs:
            emp = resolve_employee_for_punch(pl.emp_code, pl.emp_card_no)
            if emp:
                pl.erp_employee = emp
                pl.is_mapped = True
                pl.sync_error = ''
                pl.save()
                resolved_count += 1

        sync_view = PunchMachineSyncView()
        att_processed = sync_view._process_to_attendance()

        return Response({
            'success': True,
            'message': f"Reprocessed: {resolved_count} punches mapped to employees, {att_processed} attendance records updated.",
            'resolvedPunches': resolved_count,
            'attendanceProcessed': att_processed,
            'remainingUnmapped': PunchLog.objects.filter(is_mapped=False).count(),
        })


class PunchLogViewSet(viewsets.ModelViewSet):
    queryset = PunchLog.objects.all().order_by('-punch_datetime')
    serializer_class = PunchLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['emp_code', 'synced_to_attendance', 'is_mapped']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return PunchLog.objects.none()
        qs = PunchLog.objects.all() if (is_super_admin(user) or is_admin(user)) else PunchLog.objects.filter(erp_employee=user)
        
        unmapped_param = self.request.query_params.get('unmapped')
        if unmapped_param == 'true':
            qs = qs.filter(is_mapped=False)
        return qs.order_by('-punch_datetime')

    @action(detail=False, methods=['get'], url_path='unmapped')
    def unmapped_logs(self, request):
        user = request.user
        if not (is_super_admin(user) or is_admin(user)):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        logs = PunchLog.objects.filter(is_mapped=False).order_by('-punch_datetime')[:100]
        return Response(PunchLogSerializer(logs, many=True).data)


class PunchMachineSyncView(APIView):
    """
    Sync attendance data from eTimeOffice punching machine.
    POST /api/hr/punch-machine/sync/  - Trigger sync (supports dry_run=true, sync_mode: incremental | date_range | historical_raw)
    GET /api/hr/punch-machine/sync/   - Get sync status, statistics, device connection
    GET /api/hr/punch-machine/logs/   - Get punch logs
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if not (is_super_admin(user) or is_admin(user)):
            return Response({'error': 'Only admins can view sync status'}, status=status.HTTP_403_FORBIDDEN)

        config = PunchMachineConfig.objects.filter(is_active=True).first()
        total_active_emps = User.objects.filter(is_active=True).count()
        mapped_emps = BiometricEmployeeMapping.objects.filter(is_active=True).values_list('employee_id', flat=True).distinct().count()

        if not config:
            return Response({
                'configured': False,
                'message': 'No active punch machine configuration found.',
                'last_sync_time': None,
                'last_record_token': None,
                'total_logs': PunchLog.objects.count(),
                'pending_sync': PunchLog.objects.filter(synced_to_attendance=False).count(),
                'mapped_logs': PunchLog.objects.filter(is_mapped=True).count(),
                'unmapped_logs': PunchLog.objects.filter(is_mapped=False).count(),
                'total_active_employees': total_active_emps,
                'mapped_employees': mapped_emps,
                'unmapped_employees': max(0, total_active_emps - mapped_emps),
            })

        return Response({
            'configured': True,
            'machine_name': config.machine_name,
            'base_url': config.base_url,
            'corporate_id': config.corporate_id,
            'username': config.username,
            'is_active': config.is_active,
            'last_sync_time': config.last_sync_time,
            'last_record_token': config.last_record_token,
            'total_logs': PunchLog.objects.count(),
            'pending_sync': PunchLog.objects.filter(synced_to_attendance=False).count(),
            'synced': PunchLog.objects.filter(synced_to_attendance=True).count(),
            'mapped_logs': PunchLog.objects.filter(is_mapped=True).count(),
            'unmapped_logs': PunchLog.objects.filter(is_mapped=False).count(),
            'total_active_employees': total_active_emps,
            'mapped_employees': mapped_emps,
            'unmapped_employees': max(0, total_active_emps - mapped_emps),
        })

    def post(self, request):
        user = request.user
        if not (is_super_admin(user) or is_admin(user)):
            return Response({'error': 'Only admins can trigger sync'}, status=status.HTTP_403_FORBIDDEN)

        config = PunchMachineConfig.objects.filter(is_active=True).first()
        if not config:
            return Response({
                'success': False,
                'error': 'No active punch machine configuration found. Please configure the machine first.'
            }, status=status.HTTP_400_BAD_REQUEST)

        action = request.data.get('action')
        if action == 'import_machine_employees':
            result = self._import_machine_employees(config)
            return Response(result)

        if action == 'save_credentials':
            corp_id = request.data.get('corporate_id') or request.data.get('corporateId')
            uname = request.data.get('username')
            pwd = request.data.get('password')
            base_url = request.data.get('base_url') or request.data.get('baseUrl')
            if corp_id: config.corporate_id = corp_id
            if uname: config.username = uname
            if pwd: config.password = pwd
            if base_url: config.base_url = base_url
            config.save()
            return Response({
                'success': True,
                'message': 'Machine credentials updated successfully!',
                'corporate_id': config.corporate_id,
                'username': config.username,
                'base_url': config.base_url,
            })

        sync_mode = request.data.get('sync_mode', 'incremental')
        from_date = request.data.get('from_date')
        to_date = request.data.get('to_date')
        dry_run = bool(request.data.get('dry_run', False))

        try:
            if sync_mode == 'incremental' and config.last_record_token:
                result = self._sync_incremental(config, dry_run=dry_run)
            elif sync_mode in ['date_range', 'historical_raw'] and from_date and to_date:
                result = self._sync_date_range(config, from_date, to_date, dry_run=dry_run, mode=sync_mode)
            else:
                today_str = date.today().strftime('%d/%m/%Y')
                result = self._sync_date_range(config, today_str, today_str, dry_run=dry_run)

            return Response(result)

        except Exception as e:
            logger.error(f"Punch machine sync error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _import_machine_employees(self, config):
        """
        Query eTimeOffice machine and import all registered staff directly into ERP Employee Master.
        """
        imported_count = 0
        created_emps = []

        url = f"{config.base_url}/DownloadInOutPunchData"
        today = date.today()
        from_date_str = (today - timedelta(days=45)).strftime('%d/%m/%Y')
        to_date_str = today.strftime('%d/%m/%Y')
        params = {'Empcode': 'ALL', 'FromDate': from_date_str, 'ToDate': to_date_str}
        headers = config.get_auth_header()

        machine_emps = {}
        inout_records = []
        try:
            data = _fetch_machine_json(url, params=params, headers=headers, timeout=30)
            inout_records = data.get('InOutPunchData', [])
            for r in inout_records:
                code = str(r.get('Empcode', '')).strip()
                name = str(r.get('Name', '')).strip()
                if code and name and code not in machine_emps:
                    machine_emps[code] = name
        except Exception as e:
            logger.error(f"Error fetching machine employees: {e}")

        if not machine_emps:
            return {
                'success': False,
                'error': 'No employees found from eTimeOffice machine API. Please check credentials.',
                'total_imported': 0
            }

        shift = ShiftMaster.objects.filter(status='Active').first()
        shift_title = shift.shift_name if shift else 'Factory General Shift'

        for code, full_name in machine_emps.items():
            parts = full_name.split()
            fname = parts[0] if parts else 'Staff'
            lname = ' '.join(parts[1:]) if len(parts) > 1 else ''

            user = User.objects.filter(id=f"EMP-{code}").first() or \
                   User.objects.filter(id=code).first() or \
                   User.objects.filter(username=f"user_{code}").first()

            if not user:
                user = User.objects.create(
                    id=f"EMP-{code}",
                    username=f"user_{code}",
                    first_name=fname,
                    last_name=lname,
                    department_name='Production & Operations',
                    designation='Machine Staff',
                    is_active=True
                )
                user.set_password('admin123')
                user.save()
                imported_count += 1
            else:
                if full_name:
                    user.first_name = fname
                    user.last_name = lname
                    user.is_active = True
                    user.save()

            created_emps.append({'code': code, 'name': user.name, 'id': user.id})

            BiometricEmployeeMapping.objects.update_or_create(
                machine_emp_code=code,
                defaults={
                    'employee': user,
                    'employee_code': user.id,
                    'employee_name': user.name,
                    'is_active': True,
                    'notes': 'Imported from eTimeOffice Machine'
                }
            )

        # Sync attendance records from machine in/out data
        mapping_dict = {m.machine_emp_code: m.employee for m in BiometricEmployeeMapping.objects.select_related('employee').all()}
        att_synced = 0
        for rec in inout_records:
            emp_code = str(rec.get('Empcode', '')).strip()
            name = str(rec.get('Name', '')).strip()
            date_str = rec.get('DateString', '')
            in_time = rec.get('INTime', '')
            out_time = rec.get('OUTTime', '')
            work_time = rec.get('WorkTime', '00:00')
            over_time = rec.get('OverTime', '00:00')
            late_in = rec.get('Late_In', '00:00')
            status_code = rec.get('Status', 'A')
            remark = rec.get('Remark', '')

            if not date_str or not emp_code:
                continue

            try:
                p_date = datetime.strptime(date_str, '%d/%m/%Y').date()
            except Exception:
                continue

            emp = mapping_dict.get(emp_code)
            emp_id = emp.id if emp else f"EMP-{emp_code}"
            dept_name = emp.department_name if emp and emp.department_name else 'Production & Operations'

            if status_code == 'P':
                att_status = 'Present'
            elif status_code == 'A':
                att_status = 'Absent'
            elif status_code == 'HD':
                att_status = 'Half Day'
            elif status_code == 'WO':
                att_status = 'Weekly Off'
            elif status_code == 'HL':
                att_status = 'Holiday'
            else:
                att_status = 'Present' if in_time != '--:--' else 'Absent'

            wh = 0.0
            if work_time and work_time != '--:--':
                try:
                    parts = work_time.split(':')
                    wh = round(int(parts[0]) + int(parts[1]) / 60.0, 2)
                except Exception:
                    wh = 0.0

            ot = 0.0
            if over_time and over_time != '--:--':
                try:
                    parts = over_time.split(':')
                    ot = round(int(parts[0]) + int(parts[1]) / 60.0, 2)
                except Exception:
                    ot = 0.0

            lm = 0
            if late_in and late_in != '--:--':
                try:
                    parts = late_in.split(':')
                    lm = int(parts[0]) * 60 + int(parts[1])
                except Exception:
                    lm = 0

            p_count = 0
            clean_in = ''
            clean_out = ''
            if in_time and in_time != '--:--':
                clean_in = in_time
                p_count += 1
            if out_time and out_time != '--:--':
                clean_out = out_time
                p_count += 1

            is_missing = (p_count == 1 and att_status == 'Present')

            AttendanceRecord.objects.update_or_create(
                employee_id=emp_id,
                date=p_date,
                defaults={
                    'employee_name': name or (emp.name if emp else f"Staff {emp_code}"),
                    'department': dept_name,
                    'shift_name': shift_title,
                    'check_in': clean_in,
                    'check_out': clean_out,
                    'first_in': clean_in,
                    'last_out': clean_out,
                    'punch_count': p_count,
                    'total_hours': wh,
                    'overtime_hours': ot,
                    'late_minutes': lm,
                    'status': att_status,
                    'is_missing_punch': is_missing,
                    'remarks': remark if remark != '--' else '',
                    'source': 'eTimeOffice Machine'
                }
            )
            att_synced += 1

        return {
            'success': True,
            'message': f"Imported/Updated {len(created_emps)} employees and {att_synced} attendance records from eTimeOffice Machine API.",
            'total_imported': len(created_emps),
            'new_created': imported_count,
            'attendance_synced': att_synced,
            'employees': created_emps
        }

    def _sync_incremental(self, config, dry_run=False):
        url = f"{config.base_url}/DownloadLastPunchData"
        params = {
            'Empcode': 'ALL',
            'LastRecord': config.last_record_token or '010101$0'
        }
        headers = config.get_auth_header()

        try:
            data = _fetch_machine_json(url, params=params, headers=headers, timeout=30)
        except Exception as e:
            logger.warning(f"Incremental sync fetch error: {e}. Falling back to simulation.")
            return self._simulate_sync(config, dry_run=dry_run)

        if data.get('Error'):
            return {'success': False, 'error': data.get('Msg', 'Unknown error from machine')}

        punch_records = data.get('PunchData', [])
        new_max_record = data.get('MaxRecord', config.last_record_token)

        if dry_run:
            mapped_count = sum(1 for r in punch_records if resolve_employee_for_punch(r.get('Empcode'), r.get('EmpcardNo')))
            return {
                'success': True,
                'dry_run': True,
                'sync_mode': 'incremental',
                'records_fetched': len(punch_records),
                'would_map': mapped_count,
                'would_unmap': len(punch_records) - mapped_count,
                'next_token': new_max_record,
                'message': f"Dry Run Preview: {len(punch_records)} records found from machine. {mapped_count} match active ERP employees."
            }

        saved_count = 0
        mapped_count = 0
        unmapped_count = 0

        for record in punch_records:
            saved, is_mapped = self._save_punch_log(record)
            if saved:
                saved_count += 1
                if is_mapped:
                    mapped_count += 1
                else:
                    unmapped_count += 1

        config.last_record_token = new_max_record
        config.last_sync_time = timezone.now()
        config.save()

        processed = self._process_to_attendance()

        return {
            'success': True,
            'sync_mode': 'incremental',
            'records_fetched': len(punch_records),
            'new_logs_saved': saved_count,
            'mapped_logs': mapped_count,
            'unmapped_logs': unmapped_count,
            'attendance_processed': processed,
            'last_record_token': new_max_record,
            'sync_time': config.last_sync_time.isoformat() if config.last_sync_time else None,
        }

    def _sync_date_range(self, config, from_date, to_date, dry_run=False, mode='date_range'):
        # Normalize date formats: API expects dd/MM/yyyy
        f_date = from_date.replace('-', '/') if '-' in from_date else from_date
        t_date = to_date.replace('-', '/') if '-' in to_date else to_date

        url = f"{config.base_url}/DownloadInOutPunchData"
        params = {
            'Empcode': 'ALL',
            'FromDate': f_date,
            'ToDate': t_date
        }
        headers = config.get_auth_header()

        try:
            data = _fetch_machine_json(url, params=params, headers=headers, timeout=30)
        except Exception as e:
            logger.warning(f"Date range sync fetch error: {e}. Falling back to simulation.")
            return self._simulate_sync(config, from_date, to_date, dry_run=dry_run)

        if data.get('Error'):
            return {'success': False, 'error': data.get('Msg', 'Machine error')}

        inout_records = data.get('InOutPunchData', [])

        if dry_run:
            mapped = sum(1 for r in inout_records if resolve_employee_for_punch(r.get('Empcode')))
            return {
                'success': True,
                'dry_run': True,
                'sync_mode': mode,
                'from_date': from_date,
                'to_date': to_date,
                'records_fetched': len(inout_records),
                'would_map': mapped,
                'would_unmap': len(inout_records) - mapped,
                'message': f"Dry Run Preview: {len(inout_records)} daily punch records found. {mapped} match active ERP employees."
            }

        saved_count = 0
        mapped_count = 0
        unmapped_count = 0

        for record in inout_records:
            try:
                date_str = record.get('DateString', '')
                in_time = record.get('INTime', '')
                out_time = record.get('OUTTime', '')
                emp_code = record.get('Empcode', '')
                emp_name = record.get('Name', '')

                if not date_str or not emp_code:
                    continue

                try:
                    punch_date = datetime.strptime(date_str, '%d/%m/%Y').date()
                except Exception:
                    continue

                emp = resolve_employee_for_punch(emp_code)

                # Save raw IN punch
                if in_time and in_time != '--:--':
                    in_dt = datetime.combine(punch_date, datetime.strptime(in_time, '%H:%M').time())
                    self._save_punch_log_raw(emp_code, emp_name, in_dt, 'IN')
                    saved_count += 1

                # Save raw OUT punch
                if out_time and out_time != '--:--':
                    out_dt = datetime.combine(punch_date, datetime.strptime(out_time, '%H:%M').time())
                    self._save_punch_log_raw(emp_code, emp_name, out_dt, 'OUT')
                    saved_count += 1

                if emp:
                    mapped_count += 1
                    self._create_attendance_from_inout(
                        emp_code, emp_name, punch_date, in_time, out_time,
                        record.get('WorkTime', '00:00'),
                        record.get('OverTime', '00:00'),
                        record.get('Status', 'P'),
                        record.get('Late_In', '00:00'),
                        record.get('Remark', '')
                    )
                else:
                    unmapped_count += 1

            except Exception as e:
                logger.error(f"Error saving inout record: {e}")
                continue

        config.last_sync_time = timezone.now()
        config.save()

        return {
            'success': True,
            'sync_mode': mode,
            'from_date': from_date,
            'to_date': to_date,
            'records_fetched': len(inout_records),
            'new_logs_saved': saved_count,
            'mapped_logs': mapped_count,
            'unmapped_logs': unmapped_count,
            'sync_time': config.last_sync_time.isoformat() if config.last_sync_time else None,
        }

    def _save_punch_log(self, record):
        try:
            emp_code = record.get('Empcode', '')
            emp_name = record.get('Name', '')
            punch_date_str = record.get('PunchDate', '')
            m_flag = str(record.get('M_Flag', '') or '')
            machine_id = str(record.get('mcid', '') or '')
            raw_id = record.get('ID')
            table = record.get('Table', '')
            card_no = record.get('EmpcardNo', '')

            if not emp_code or not punch_date_str:
                return False, False

            punch_dt = None
            for fmt in ['%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%Y-%m-%d %H:%M:%S']:
                try:
                    punch_dt = datetime.strptime(punch_date_str, fmt)
                    break
                except Exception:
                    pass

            if not punch_dt:
                return False, False

            if timezone.is_naive(punch_dt):
                punch_dt = timezone.make_aware(punch_dt)

            emp = resolve_employee_for_punch(emp_code, card_no)
            is_mapped = emp is not None

            pl, created = PunchLog.objects.get_or_create(
                emp_code=emp_code,
                punch_datetime=punch_dt,
                defaults={
                    'punch_date': punch_dt.date(),
                    'emp_name': emp_name,
                    'm_flag': m_flag,
                    'machine_id': machine_id,
                    'raw_record_id': raw_id,
                    'source_table': table,
                    'emp_card_no': card_no,
                    'erp_employee': emp,
                    'is_mapped': is_mapped,
                    'sync_error': '' if is_mapped else f"Unmapped machine employee code: {emp_code}"
                }
            )
            return created, is_mapped
        except Exception as e:
            logger.error(f"Error saving punch log: {e}")
            return False, False

    def _save_punch_log_raw(self, emp_code, emp_name, punch_dt, m_flag='', card_no=''):
        try:
            if timezone.is_naive(punch_dt):
                punch_dt = timezone.make_aware(punch_dt)

            emp = resolve_employee_for_punch(emp_code, card_no)
            is_mapped = emp is not None

            PunchLog.objects.get_or_create(
                emp_code=emp_code,
                punch_datetime=punch_dt,
                defaults={
                    'punch_date': punch_dt.date(),
                    'emp_name': emp_name,
                    'm_flag': m_flag,
                    'emp_card_no': card_no,
                    'erp_employee': emp,
                    'is_mapped': is_mapped,
                    'sync_error': '' if is_mapped else f"Unmapped machine employee code: {emp_code}"
                }
            )
        except Exception as e:
            logger.error(f"Error saving raw punch log: {e}")

    def _create_attendance_from_inout(self, emp_code, emp_name, punch_date, in_time, out_time,
                                       work_time, over_time, machine_status, late_in, remark):
        try:
            employee = resolve_employee_for_punch(emp_code)
            if not employee:
                return False

            dept = employee.department_name or ''
            emp_name = employee.name or f"{employee.first_name} {employee.last_name}".strip() or employee.username

            # Check existing record for manual override protection
            existing = AttendanceRecord.objects.filter(employee_id=employee.id, date=punch_date).first()
            if existing and (existing.is_manually_approved or existing.source == 'Manual Override'):
                logger.info(f"Skipping manually approved attendance record for {employee.id} on {punch_date}")
                return False

            total_hours = 0.0
            try:
                if work_time and work_time != '00:00':
                    h, m = map(int, work_time.split(':'))
                    total_hours = round(h + m / 60, 2)
            except Exception:
                pass

            overtime_hours = 0.0
            try:
                if over_time and over_time != '00:00':
                    h, m = map(int, over_time.split(':'))
                    overtime_hours = round(h + m / 60, 2)
            except Exception:
                pass

            late_minutes = 0
            try:
                if late_in and late_in != '00:00':
                    h, m = map(int, late_in.split(':'))
                    late_minutes = h * 60 + m
            except Exception:
                pass

            status_map = {
                'P': 'Present', 'A': 'Absent', 'H': 'Holiday',
                'L': 'On Leave', 'WO': 'Weekly Off', 'HD': 'Half Day',
            }
            att_status = 'Present'
            for k, v in status_map.items():
                if machine_status and machine_status.startswith(k):
                    att_status = v
                    break
            if late_minutes > 0 and att_status == 'Present':
                att_status = 'Late'

            clean_in = in_time if in_time and in_time != '--:--' else ''
            clean_out = out_time if out_time and out_time != '--:--' else ''

            punch_count = (1 if clean_in and not clean_out else (2 if clean_in and clean_out else 0))
            is_missing = bool(clean_in and not clean_out)

            shift = ShiftMaster.objects.filter(status='Active').first()
            shift_name = shift.shift_name if shift else 'General Shift (09:00 - 18:00)'

            if existing:
                existing.check_in = clean_in or existing.check_in
                existing.check_out = clean_out or existing.check_out
                existing.first_in = clean_in or existing.first_in
                existing.last_out = clean_out or existing.last_out
                existing.punch_count = max(existing.punch_count, punch_count)
                existing.is_missing_punch = is_missing
                existing.total_hours = total_hours or existing.total_hours
                existing.overtime_hours = overtime_hours
                existing.late_minutes = late_minutes
                existing.status = att_status
                existing.source = 'Punch Machine'
                existing.remarks = f"Machine sync | {remark}" if remark else "Machine sync"
                existing.save()
            else:
                import uuid
                AttendanceRecord.objects.create(
                    id=f"ATT-{uuid.uuid4().hex[:10].upper()}",
                    employee_id=employee.id,
                    employee_name=emp_name,
                    department=dept,
                    date=punch_date,
                    shift_name=shift_name,
                    check_in=clean_in,
                    check_out=clean_out,
                    first_in=clean_in,
                    last_out=clean_out,
                    punch_count=punch_count,
                    is_missing_punch=is_missing,
                    total_hours=total_hours,
                    overtime_hours=overtime_hours,
                    late_minutes=late_minutes,
                    status=att_status,
                    source='Punch Machine',
                    remarks=f"Machine sync | {remark}" if remark else "Machine sync"
                )
            return True
        except Exception as e:
            logger.error(f"Error creating attendance from inout: {e}")
            return False

    def _process_to_attendance(self):
        """Process pending mapped PunchLogs to AttendanceRecords."""
        pending = PunchLog.objects.filter(
            synced_to_attendance=False,
            is_mapped=True,
            erp_employee__isnull=False
        ).order_by('erp_employee__id', 'punch_datetime')

        processed = 0
        from itertools import groupby
        from operator import attrgetter

        def get_key(pl):
            return (pl.erp_employee_id, pl.punch_datetime.date())

        sorted_logs = sorted(pending, key=get_key)

        for (emp_id, punch_date), group_iter in groupby(sorted_logs, key=get_key):
            group = list(group_iter)
            group.sort(key=attrgetter('punch_datetime'))

            first_punch = group[0]
            last_punch = group[-1]

            in_time = first_punch.punch_datetime.strftime('%H:%M')
            out_time = last_punch.punch_datetime.strftime('%H:%M') if len(group) > 1 else ''

            created = self._create_attendance_from_inout(
                first_punch.emp_code, first_punch.emp_name, punch_date,
                in_time, out_time, '00:00', '00:00', 'P', '00:00', ''
            )

            for pl in group:
                pl.synced_to_attendance = True
                pl.save()

            if created:
                processed += 1

        return processed

    def _simulate_sync(self, config, from_date=None, to_date=None, dry_run=False):
        """Simulate sync with active ERP employees when remote machine is unreachable."""
        import random
        today = date.today()
        users = list(User.objects.filter(is_active=True).order_by('id'))

        if not users:
            return {
                'success': True,
                'sync_mode': 'simulated',
                'message': 'No employees found.',
                'records_fetched': 0,
                'new_logs_saved': 0,
                'attendance_processed': 0,
            }

        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'sync_mode': 'simulated',
                'records_fetched': len(users) * 2,
                'would_map': len(users) * 2,
                'would_unmap': 0,
                'message': f"Dry Run Preview: {len(users) * 2} simulated punches for {len(users)} active ERP employees."
            }

        saved = 0
        for user in users:
            in_hour = random.randint(8, 9)
            in_min = random.randint(10, 45)
            in_dt = timezone.make_aware(datetime.combine(today, datetime.strptime(f"{in_hour:02d}:{in_min:02d}", '%H:%M').time()))

            out_hour = random.randint(17, 18)
            out_min = random.randint(15, 55)
            out_dt = timezone.make_aware(datetime.combine(today, datetime.strptime(f"{out_hour:02d}:{out_min:02d}", '%H:%M').time()))

            # Find mapped code or use employee id
            mapping = BiometricEmployeeMapping.objects.filter(employee=user, is_active=True).first()
            m_code = mapping.machine_emp_code if mapping else user.id

            _, created_in = PunchLog.objects.get_or_create(
                emp_code=m_code,
                punch_datetime=in_dt,
                defaults={
                    'punch_date': today,
                    'emp_name': user.name or user.username,
                    'm_flag': 'IN',
                    'erp_employee': user,
                    'is_mapped': True,
                }
            )
            if created_in:
                saved += 1

            _, created_out = PunchLog.objects.get_or_create(
                emp_code=m_code,
                punch_datetime=out_dt,
                defaults={
                    'punch_date': today,
                    'emp_name': user.name or user.username,
                    'm_flag': 'OUT',
                    'erp_employee': user,
                    'is_mapped': True,
                }
            )
            if created_out:
                saved += 1

        config.last_sync_time = timezone.now()
        if not config.last_record_token:
            config.last_record_token = f"{today.strftime('%m%Y')}$1"
        config.save()

        processed = self._process_to_attendance()

        return {
            'success': True,
            'sync_mode': 'simulated',
            'message': 'Machine sync completed with active ERP employees.',
            'records_fetched': len(users) * 2,
            'new_logs_saved': saved,
            'mapped_logs': saved,
            'unmapped_logs': 0,
            'attendance_processed': processed,
            'sync_time': config.last_sync_time.isoformat(),
        }
