import csv
import io
from datetime import date
from decimal import Decimal

from django.db.models import Count, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.authentication.models import User
from apps.core.rbac_permissions import is_admin, is_super_admin

from . import payroll_engine as eng
from .models import (
    AttendanceRegularization, LeaveRequest, OvertimeRecord, PayrollRecord, PayrollSettings, SalaryStructure,
)
from .payslip_pdf import build_payslip, build_zip, safe_name
from .serializers import PayrollRecordSerializer, SalaryStructureSerializer


def _admin(user):
    return bool(user and user.is_authenticated and (is_super_admin(user) or is_admin(user)))


def _company():
    try:
        from apps.core.models import CompanySetting
        c = CompanySetting.objects.first()
    except Exception:
        c = None
    if not c:
        return {'name': 'UMA TECHNO FAB', 'address': '', 'contact': ''}
    addr = ', '.join(x for x in [c.address, c.city, c.state, c.pincode] if x)
    contact = ' | '.join(x for x in [f'Ph: {c.phone}' if c.phone else '', c.email, f'GSTIN: {c.gstin}' if c.gstin else '', f'PAN: {c.pan}' if c.pan else ''] if x)
    return {'name': c.company_name, 'address': addr, 'contact': contact}


def _period_or_400(request):
    p = request.query_params.get('period') or request.data.get('period') or request.data.get('monthYear') or request.data.get('month_year')
    try:
        y, m = eng.parse_period(p)
    except ValueError as e:
        return None, Response({'error': str(e)}, status=400)
    return f'{y}-{m:02d}', None


class SalaryStructureViewSet(viewsets.ModelViewSet):
    queryset = SalaryStructure.objects.all().order_by('employee_id', '-effective_from')
    serializer_class = SalaryStructureSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['structure_name', 'employee_name', 'employee_id']
    filterset_fields = ['status', 'employee_id']

    def get_queryset(self):
        qs = super().get_queryset()
        return qs if _admin(self.request.user) else qs.filter(employee_id=self.request.user.id)

    def _guard(self, request):
        if not _admin(request.user):
            return Response({'error': 'Only administrators can manage salary structures.'}, status=403)
        return None

    @staticmethod
    def _fill_name(row):
        """employee_name is optional in requests — take it from the employee master."""
        if not row.get('employee_name') and row.get('employee_id'):
            u = User.objects.filter(id=row['employee_id']).first()
            if u:
                row['employee_name'] = f'{u.first_name} {u.last_name}'.strip() or u.username
        return row

    @staticmethod
    def _apply_figures(inst):
        for k, v in eng.structure_figures(inst).items():
            setattr(inst, k, v)

    def create(self, request, *args, **kwargs):
        denied = self._guard(request)
        if denied:
            return denied
        payload = dict(request.data)
        payload.setdefault('id', 'auto')   # primary key is generated below
        self._fill_name(payload)
        ser = self.get_serializer(data=payload)
        ser.is_valid(raise_exception=True)
        d = dict(ser.validated_data)
        d.pop('id', None)
        existing = SalaryStructure.objects.filter(employee_id=d['employee_id'], status='Active').order_by('-effective_from').first()
        # same effective date -> edit in place; later date -> new revision and retire the old one
        if existing and existing.effective_from == d['effective_from']:
            for k, v in d.items():
                setattr(existing, k, v)
            inst = existing
        else:
            if existing:
                SalaryStructure.objects.filter(employee_id=d['employee_id'], status='Active').update(status='Inactive')
            inst = SalaryStructure(id=f"SAL-{d['employee_id']}-{d['effective_from']:%Y%m%d}", **d)
            if SalaryStructure.objects.filter(pk=inst.id).exists():
                inst.id = f"{inst.id}-{timezone.now():%H%M%S}"
        if not inst.employee_name:
            u = User.objects.filter(id=inst.employee_id).first()
            inst.employee_name = (f'{u.first_name} {u.last_name}'.strip() or u.username) if u else inst.employee_id
        self._apply_figures(inst)
        inst.save()
        return Response(self.get_serializer(inst).data, status=201)

    def update(self, request, *args, **kwargs):
        denied = self._guard(request)
        if denied:
            return denied
        partial = kwargs.pop('partial', False)
        inst = self.get_object()
        ser = self.get_serializer(inst, data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        inst = ser.save()
        self._apply_figures(inst)
        inst.save()
        return Response(self.get_serializer(inst).data)

    def destroy(self, request, *args, **kwargs):
        return self._guard(request) or super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='bulk-save')
    def bulk_save(self, request):
        """Save many structures at once (the salary grid / CSV import). Body: {rows:[{employeeId, basicSalary, ...}]}"""
        denied = self._guard(request)
        if denied:
            return denied
        saved, errors = 0, []
        for i, row in enumerate(request.data.get('rows') or []):
            row = dict(row)
            row.setdefault('id', 'auto')
            self._fill_name(row)
            row.setdefault('structure_name', 'Monthly Salary')
            row.setdefault('effective_from', str(date.today().replace(day=1)))
            row.setdefault('status', 'Active')
            ser = self.get_serializer(data=row)
            if not ser.is_valid():
                errors.append({'row': i + 1, 'employeeId': row.get('employee_id'), 'error': '; '.join(f'{k}: {" ".join(map(str, v))}' for k, v in ser.errors.items())})
                continue
            d = dict(ser.validated_data)
            d.pop('id', None)
            inst = SalaryStructure.objects.filter(employee_id=d['employee_id'], status='Active').order_by('-effective_from').first()
            if inst:
                for k, v in d.items():
                    setattr(inst, k, v)
                inst.status = 'Active'
            else:
                inst = SalaryStructure(id=f"SAL-{d['employee_id']}-{d['effective_from']:%Y%m%d}", **d)
            if not inst.employee_name:
                u = User.objects.filter(id=inst.employee_id).first()
                inst.employee_name = (f'{u.first_name} {u.last_name}'.strip() or u.username) if u else inst.employee_id
            self._apply_figures(inst)
            inst.save()
            saved += 1
        return Response({'saved': saved, 'errors': errors})

    @action(detail=False, methods=['get'], url_path='employees')
    def employees(self, request):
        """Every active employee with their current structure (null if none) — drives the salary grid."""
        denied = self._guard(request)
        if denied:
            return denied
        structs = eng.active_structures(date(2100, 1, 1))
        out = []
        for u in eng.eligible_users():
            s = structs.get(u.id)
            out.append({
                'employeeId': u.id, 'employeeName': f'{u.first_name} {u.last_name}'.strip() or u.username, 'department': u.department_name,
                'designation': u.designation, 'joiningDate': u.joining_date, 'bankAccountNo': u.bank_account_no, 'bankIfsc': u.bank_ifsc,
                'structure': SalaryStructureSerializer(s).data if s else None,
            })
        return Response(out)


class PayrollRecordViewSet(viewsets.ModelViewSet):
    queryset = PayrollRecord.objects.all().order_by('-period_ym', 'employee_name')
    serializer_class = PayrollRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['payroll_number', 'employee_name', 'department', 'month_year']
    filterset_fields = ['status', 'month_year', 'period_ym', 'financial_year', 'employee_id', 'payment_status']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return PayrollRecord.objects.none()
        qs = PayrollRecord.objects.all().order_by('-period_ym', 'employee_name')
        if _admin(user):
            return qs
        return qs.filter(employee_id=user.id).exclude(status='Draft')  # everyone else: own slips, never drafts

    def _guard(self, request):
        if not _admin(request.user):
            return Response({'error': 'Only administrators can manage payroll.'}, status=403)
        return None

    def create(self, request, *args, **kwargs):
        return self._guard(request) or Response({'error': 'Payroll records are created by "Calculate payroll", not by hand.'}, status=405)

    def update(self, request, *args, **kwargs):
        return self._guard(request) or Response({'error': 'Use the Adjust action to change a payroll record.'}, status=405)

    partial_update = update

    def destroy(self, request, *args, **kwargs):
        denied = self._guard(request)
        if denied:
            return denied
        rec = self.get_object()
        if rec.status != 'Draft':
            return Response({'error': f'A {rec.status} payroll cannot be deleted. Reopen it first.'}, status=400)
        return super().destroy(request, *args, **kwargs)

    # ------------------------------------------------------------- calculation
    def _calculate(self, request):
        denied = self._guard(request)
        if denied:
            return denied
        period = request.data.get('period') or request.data.get('monthYear') or request.data.get('month_year')
        ids = request.data.get('employeeIds') or request.data.get('employee_ids') or None
        dry = bool(request.data.get('dryRun') or request.data.get('dry_run'))
        try:
            res = eng.calculate_month(period, ids, dry_run=dry)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        if not dry:
            res['records'] = PayrollRecordSerializer(res['records'], many=True).data
        res['dryRun'] = dry
        return Response(res, status=200 if dry else 201)

    @action(detail=False, methods=['post'], url_path='calculate')
    def calculate(self, request):
        return self._calculate(request)

    @action(detail=False, methods=['post'], url_path='generate-monthly-payroll')
    def generate_monthly_payroll(self, request):  # kept for old clients; now runs the real engine
        return self._calculate(request)

    @action(detail=True, methods=['post'], url_path='adjust')
    def adjust(self, request, pk=None):
        denied = self._guard(request)
        if denied:
            return denied
        rec = self.get_object()
        if rec.status != 'Draft':
            return Response({'error': f'Only Draft payroll can be adjusted (this is {rec.status}). Reopen it first.'}, status=400)
        g = lambda *k: next((request.data[x] for x in k if x in request.data), None)
        try:
            oe, od, tds = g('otherEarnings', 'other_earnings'), g('otherDeductions', 'other_deductions'), g('tdsDeduction', 'tds_deduction')
            if oe is not None:
                rec.other_earnings = max(Decimal('0'), eng.r2(oe))
            if od is not None:
                rec.other_deductions = max(Decimal('0'), eng.r2(od))
            if tds is not None:
                rec.tds_deduction = max(Decimal('0'), eng.r2(tds))
        except Exception:
            return Response({'error': 'Amounts must be numbers.'}, status=400)
        if g('remarks') is not None:
            rec.remarks = str(g('remarks'))[:1000]
        eng.recompute_totals(rec)
        rec.save()
        return Response(PayrollRecordSerializer(rec).data)

    # ------------------------------------------------------------- workflow
    @action(detail=True, methods=['post'], url_path='approve')
    def approve_payroll(self, request, pk=None):
        denied = self._guard(request)
        if denied:
            return denied
        rec = self.get_object()
        try:
            eng.approve_record(rec, getattr(request.user, 'username', '') or 'HR')
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        rec.refresh_from_db()
        return Response(PayrollRecordSerializer(rec).data)

    @action(detail=False, methods=['post'], url_path='approve-month')
    def approve_month(self, request):
        denied = self._guard(request)
        if denied:
            return denied
        period, err = _period_or_400(request)
        if err:
            return err
        ok, failed = 0, []
        for rec in PayrollRecord.objects.filter(period_ym=period, status='Draft'):
            try:
                eng.approve_record(rec, getattr(request.user, 'username', '') or 'HR')
                ok += 1
            except ValueError as e:
                failed.append({'employeeId': rec.employee_id, 'employeeName': rec.employee_name, 'error': str(e)})
        return Response({'approved': ok, 'failed': failed})

    @action(detail=True, methods=['post'], url_path='reopen')
    def reopen(self, request, pk=None):
        denied = self._guard(request)
        if denied:
            return denied
        rec = self.get_object()
        try:
            eng.reopen_record(rec)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        rec.refresh_from_db()
        return Response(PayrollRecordSerializer(rec).data)

    def _pay(self, rec, data):
        paid_on = data.get('paidDate') or data.get('paid_date')
        d = eng.parse_date_flex(paid_on) if paid_on else timezone.localdate()
        eng.mark_paid(rec, d or timezone.localdate(), data.get('paymentMode') or data.get('payment_mode') or 'Bank Transfer',
                      data.get('paymentRef') or data.get('payment_ref') or '', data.get('bankLedger') or data.get('bank_ledger') or '')

    @action(detail=True, methods=['post'], url_path='mark-paid')
    def mark_paid(self, request, pk=None):
        denied = self._guard(request)
        if denied:
            return denied
        rec = self.get_object()
        try:
            self._pay(rec, request.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        rec.refresh_from_db()
        return Response(PayrollRecordSerializer(rec).data)

    @action(detail=False, methods=['post'], url_path='mark-paid-month')
    def mark_paid_month(self, request):
        denied = self._guard(request)
        if denied:
            return denied
        period, err = _period_or_400(request)
        if err:
            return err
        ids = request.data.get('ids')
        qs = PayrollRecord.objects.filter(period_ym=period, status='Approved')
        if ids:
            qs = qs.filter(id__in=ids)
        n = 0
        for rec in qs:
            try:
                self._pay(rec, request.data)
                n += 1
            except ValueError:
                pass
        return Response({'paid': n})

    # ------------------------------------------------------------- insight
    @action(detail=False, methods=['get'], url_path='readiness')
    def readiness(self, request):
        denied = self._guard(request)
        if denied:
            return denied
        period, err = _period_or_400(request)
        if err:
            return err
        y, m = eng.parse_period(period)
        first, last = date(y, m, 1), date(y, m, __import__('calendar').monthrange(y, m)[1])
        users = list(eng.eligible_users())
        structs = eng.active_structures(last)
        missing = [{'employeeId': u.id, 'employeeName': f'{u.first_name} {u.last_name}'.strip() or u.username, 'department': u.department_name}
                   for u in users if u.id not in structs]
        no_bank = [u.id for u in users if u.id in structs and not u.bank_account_no]
        att_days = date.today() >= first
        return Response({
            'period': period, 'label': eng.period_label(y, m), 'activeEmployees': len(users), 'withStructure': len(users) - len(missing),
            'missingStructure': missing, 'missingBankCount': len(no_bank), 'monthComplete': date.today() > last, 'monthStarted': att_days,
            'pendingLeaves': LeaveRequest.objects.filter(status='Pending', from_date__lte=last, to_date__gte=first).count(),
            'pendingRegularizations': AttendanceRegularization.objects.filter(status='Pending', date__gte=first, date__lte=last).count(),
            'pendingOvertime': OvertimeRecord.objects.filter(status='Pending', date__gte=first, date__lte=last).count(),
            'statusCounts': dict(PayrollRecord.objects.filter(period_ym=period).values_list('status').annotate(c=Count('id'))),
        })

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        denied = self._guard(request)
        if denied:
            return denied
        period, err = _period_or_400(request)
        if err:
            return err
        qs = PayrollRecord.objects.filter(period_ym=period)
        tot = qs.aggregate(gross=Sum('gross_earnings'), ded=Sum('total_deductions'), net=Sum('net_salary'), reimb=Sum('reimbursement_amount'),
                           epf=Sum('employer_pf'), eesi=Sum('employer_esi'), pf=Sum('pf_deduction'), esi=Sum('esi_deduction'), pt=Sum('pt_deduction'),
                           tds=Sum('tds_deduction'), loan=Sum('loan_advance_recovery'), ot=Sum('overtime_amount'), ctc=Sum('total_ctc'))
        dept = list(qs.values('department').annotate(headcount=Count('id'), net=Sum('net_salary'), gross=Sum('gross_earnings')).order_by('-net'))
        f = lambda v: float(v or 0)
        return Response({
            'period': period, 'headcount': qs.count(), **{k: f(v) for k, v in tot.items()},
            'byStatus': {s: {'count': c, 'net': f(n)} for s, c, n in qs.values_list('status').annotate(c=Count('id'), n=Sum('net_salary'))},
            'byDepartment': [{'department': d['department'] or 'General', 'headcount': d['headcount'], 'net': f(d['net']), 'gross': f(d['gross'])} for d in dept],
        })

    @action(detail=False, methods=['get'], url_path='trend')
    def trend(self, request):
        denied = self._guard(request)
        if denied:
            return denied
        rows = (PayrollRecord.objects.exclude(period_ym='').values('period_ym')
                .annotate(gross=Sum('gross_earnings'), net=Sum('net_salary'), ctc=Sum('total_ctc'), headcount=Count('id')).order_by('-period_ym')[:6])
        return Response([{'period': r['period_ym'], 'gross': float(r['gross'] or 0), 'net': float(r['net'] or 0), 'ctc': float(r['ctc'] or 0), 'headcount': r['headcount']}
                         for r in reversed(list(rows))])

    @action(detail=False, methods=['get', 'post'], url_path='settings')
    def payroll_settings(self, request):
        s = PayrollSettings.load()
        fields = ['days_basis', 'pf_rate', 'pf_wage_ceiling', 'esi_employee_rate', 'esi_employer_rate', 'esi_gross_ceiling', 'pt_slabs', 'ot_multiplier',
                  'shift_hours', 'unpaid_leave_keywords']
        if request.method == 'POST':
            denied = self._guard(request)
            if denied:
                return denied
            d = request.data
            if str(d.get('days_basis', d.get('daysBasis', s.days_basis))) not in ('calendar', 'fixed26', 'fixed30'):
                return Response({'error': 'days_basis must be calendar, fixed26 or fixed30.'}, status=400)
            for f in fields:
                camel = ''.join(w.capitalize() if i else w for i, w in enumerate(f.split('_')))
                if f in d or camel in d:
                    setattr(s, f, d.get(f, d.get(camel)))
            slabs = s.pt_slabs
            if not isinstance(slabs, list) or not slabs or slabs[-1].get('upto') is not None:
                return Response({'error': 'Professional tax slabs must be a list whose last slab has no upper limit.'}, status=400)
            s.save()
        return Response({f: getattr(s, f) for f in fields})

    # ------------------------------------------------------------- documents
    @action(detail=True, methods=['get'], url_path='payslip-pdf')
    def payslip_pdf(self, request, pk=None):
        rec = self.get_object()
        resp = HttpResponse(build_payslip(rec, _company()), content_type='application/pdf')
        resp['Content-Disposition'] = f'attachment; filename="{safe_name(rec)}"'
        return resp

    @action(detail=False, methods=['get'], url_path='payslips-zip')
    def payslips_zip(self, request):
        denied = self._guard(request)
        if denied:
            return denied
        period, err = _period_or_400(request)
        if err:
            return err
        recs = list(PayrollRecord.objects.filter(period_ym=period, status__in=['Approved', 'Paid']).order_by('employee_name'))
        if not recs:
            return Response({'error': 'No approved payslips for this month.'}, status=404)
        resp = HttpResponse(build_zip(recs, _company()), content_type='application/zip')
        resp['Content-Disposition'] = f'attachment; filename="payslips-{period}.zip"'
        return resp

    @action(detail=False, methods=['get'], url_path='bank-sheet')
    def bank_sheet(self, request):
        denied = self._guard(request)
        if denied:
            return denied
        period, err = _period_or_400(request)
        if err:
            return err
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['Employee ID', 'Name', 'Bank', 'Account No', 'IFSC', 'Net Salary', 'Status', 'Payroll Ref'])
        for r in PayrollRecord.objects.filter(period_ym=period, status__in=['Approved', 'Paid']).order_by('employee_name'):
            w.writerow([r.employee_id, r.employee_name, r.bank_name, r.bank_account_no, r.bank_ifsc, r.net_salary, r.status, r.payroll_number])
        resp = HttpResponse('﻿' + buf.getvalue(), content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = f'attachment; filename="bank-transfer-{period}.csv"'
        return resp
