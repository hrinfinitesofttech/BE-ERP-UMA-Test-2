"""
Payroll engine — real salary calculation from attendance, leave, overtime, loans and the salary structure.

Order of calculation for one employee-month:
  1. Day-by-day status (same priority HR sees on the attendance sheets):
       attendance record > approved leave > public holiday > Sunday (weekly off) > Absent
  2. paid_days / LOP days  ->  pro-rata of every salary-structure component
  3. + approved overtime, + approved reimbursements, + manual adjustments
  4. PF, ESI (rounded up), Professional Tax, TDS (fixed monthly figure from the structure), loan EMI
  5. net = gross + reimbursements - deductions
Only Draft records are ever recalculated; Approved / Paid records are locked.
"""
import calendar
import logging
import re
from datetime import date, datetime
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from apps.authentication.models import User
from .models import (
    AttendanceRecord, EmployeeAdvanceLoan, Holiday, LeaveRequest, OvertimeRecord, PayrollRecord, PayrollSettings,
    ReimbursementExpense, SalaryStructure,
)

log = logging.getLogger(__name__)
ZERO = Decimal('0')
Q2 = Decimal('0.01')

MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})


def D(v):
    try:
        return Decimal(str(v if v not in (None, '') else 0))
    except Exception:
        return ZERO


def r2(v):
    return D(v).quantize(Q2, rounding=ROUND_HALF_UP)


def r1(v):
    return D(v).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)


def ceil_rupee(v):
    return D(v).quantize(Decimal('1'), rounding=ROUND_CEILING)


def parse_period(value):
    """'2026-11', 'November 2026', 'Nov 2026' -> (2026, 11)."""
    s = str(value or '').strip()
    m = re.match(r'^(\d{4})-(\d{1,2})$', s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
    else:
        m = re.match(r'^([A-Za-z]+)\s+(\d{4})$', s)
        if not m or m.group(1).lower() not in MONTHS:
            raise ValueError(f'Unrecognised month "{value}". Use YYYY-MM.')
        y, mo = int(m.group(2)), MONTHS[m.group(1).lower()]
    if not 1 <= mo <= 12:
        raise ValueError(f'Invalid month in "{value}".')
    return y, mo


def parse_date_flex(s):
    s = str(s or '').strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y'):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    return None


def fin_year(y, mo):
    return f'{y}-{y + 1}' if mo >= 4 else f'{y - 1}-{y}'


def period_label(y, mo):
    return f'{calendar.month_name[mo]} {y}'


# ----------------------------------------------------------------- statutory maths
def days_base(settings, n_days):
    return {'fixed26': 26, 'fixed30': 30}.get(settings.days_basis, n_days)


def pt_for(gross, settings):
    g = D(gross)
    for slab in (settings.pt_slabs or []):
        up = slab.get('upto')
        if up is None or g <= D(up):
            return D(slab.get('pt'))
    return ZERO


def statutory(*, basic_earned, gross_earned, structure_gross, struct, settings, tds):
    """PF / ESI / PT for one month. `gross_earned` = statutory wages (components earned + overtime + other earnings)."""
    pf_e = pf_r = esi_e = esi_r = pt = ZERO
    if struct.pf_applicable:
        wage = D(basic_earned)
        if D(settings.pf_wage_ceiling) > 0:
            wage = min(wage, D(settings.pf_wage_ceiling))
        pf_e = r2(wage * D(settings.pf_rate) / 100)
        pf_r = pf_e
    if struct.esi_applicable and D(structure_gross) <= D(settings.esi_gross_ceiling):
        esi_e = ceil_rupee(D(gross_earned) * D(settings.esi_employee_rate) / 100)
        esi_r = ceil_rupee(D(gross_earned) * D(settings.esi_employer_rate) / 100)
    if struct.pt_applicable:
        pt = pt_for(gross_earned, settings)
    return {'pf_e': pf_e, 'pf_r': pf_r, 'esi_e': esi_e, 'esi_r': esi_r, 'pt': pt, 'tds': r2(tds)}


def structure_figures(struct, settings=None):
    """Full-month figures stored on the SalaryStructure itself (what the employee gets with zero LOP, no OT)."""
    settings = settings or PayrollSettings.load()
    gross = r2(D(struct.basic_salary) + D(struct.hra) + D(struct.conveyance_allowance) + D(struct.medical_allowance) + D(struct.special_allowance))
    st = statutory(basic_earned=struct.basic_salary, gross_earned=gross, structure_gross=gross, struct=struct, settings=settings, tds=struct.tds_monthly)
    total_ded = st['pf_e'] + st['esi_e'] + st['pt'] + st['tds']
    return {
        'gross_salary': gross, 'employee_pf': st['pf_e'], 'employee_esi': st['esi_e'], 'professional_tax': st['pt'],
        'total_deductions': r2(total_ded), 'net_salary': r2(gross - total_ded), 'employer_pf': st['pf_r'],
        'employer_esi': st['esi_r'], 'total_ctc': r2(gross + st['pf_r'] + st['esi_r']),
    }


# ----------------------------------------------------------------- attendance -> days
class MonthContext:
    """Everything needed for the month, loaded once for all employees."""

    def __init__(self, y, mo, employee_ids=None):
        self.y, self.mo = y, mo
        self.n = calendar.monthrange(y, mo)[1]
        self.first, self.last = date(y, mo, 1), date(y, mo, self.n)
        self.today = timezone.localdate()
        recs = AttendanceRecord.objects.filter(date__gte=self.first, date__lte=self.last)
        if employee_ids:
            recs = recs.filter(employee_id__in=employee_ids)
        self.records = {(r.employee_id, r.date): r for r in recs}
        self.holidays = {h.holiday_date: h for h in Holiday.objects.filter(holiday_date__gte=self.first, holiday_date__lte=self.last, is_optional=False)}
        leaves = LeaveRequest.objects.filter(status='Approved', from_date__lte=self.last, to_date__gte=self.first)
        if employee_ids:
            leaves = leaves.filter(employee_id__in=employee_ids)
        self.leaves = {}
        for lv in leaves:
            self.leaves.setdefault(lv.employee_id, []).append(lv)

    def leave_on(self, emp_id, d):
        for lv in self.leaves.get(emp_id, []):
            if lv.from_date <= d <= lv.to_date:
                return lv
        return None


def attendance_days(emp_id, ctx, settings, joined=None):
    unpaid_kw = [k.strip().lower() for k in (settings.unpaid_leave_keywords or '').split(',') if k.strip()]
    out = {'paid': ZERO, 'lop': ZERO, 'present': ZERO, 'leave': ZERO, 'unpaid_leave': ZERO, 'weekly_off': ZERO, 'holiday': ZERO,
           'half': ZERO, 'late': 0, 'absent': ZERO, 'not_joined': ZERO, 'upcoming': ZERO}
    for day in range(1, ctx.n + 1):
        d = date(ctx.y, ctx.mo, day)
        if joined and d < joined:
            out['not_joined'] += 1
            continue
        if d > ctx.today:
            out['upcoming'] += 1
            continue
        rec = ctx.records.get((emp_id, d))
        lv = ctx.leave_on(emp_id, d)
        st = (rec.status if rec else '') or ''
        if rec:
            if st in ('Present', 'Late'):
                out['paid'] += 1; out['present'] += 1
                if st == 'Late' or (rec.late_minutes or 0) > 0:
                    out['late'] += 1
            elif st == 'Half Day':
                out['paid'] += Decimal('0.5'); out['present'] += Decimal('0.5'); out['half'] += 1; out['lop'] += Decimal('0.5')
            elif st == 'Weekly Off':
                out['paid'] += 1; out['weekly_off'] += 1
            elif st == 'Holiday':
                out['paid'] += 1; out['holiday'] += 1
            elif 'leave' in st.lower():
                half = 'half' in st.lower()
                unpaid = bool(lv and any(k in (lv.leave_name or '').lower() for k in unpaid_kw))
                amt = Decimal('0.5') if half else Decimal('1')
                if unpaid:
                    out['lop'] += amt; out['unpaid_leave'] += amt
                else:
                    out['paid'] += amt; out['leave'] += amt
                if half:
                    out['lop'] += Decimal('0.5')
            elif st == 'Absent':
                out['lop'] += 1; out['absent'] += 1
            else:  # unknown status: trust punches
                if rec.first_in or rec.check_in:
                    out['paid'] += 1; out['present'] += 1
                else:
                    out['lop'] += 1; out['absent'] += 1
        elif lv:
            unpaid = any(k in (lv.leave_name or '').lower() for k in unpaid_kw)
            if lv.is_half_day:
                # half day on leave, no punches for the other half -> that half is LOP
                if unpaid:
                    out['unpaid_leave'] += Decimal('0.5'); out['lop'] += 1
                else:
                    out['leave'] += Decimal('0.5'); out['paid'] += Decimal('0.5'); out['lop'] += Decimal('0.5')
            elif unpaid:
                out['lop'] += 1; out['unpaid_leave'] += 1
            else:
                out['paid'] += 1; out['leave'] += 1
        elif d in ctx.holidays:
            out['paid'] += 1; out['holiday'] += 1
        elif d.weekday() == 6:
            out['paid'] += 1; out['weekly_off'] += 1
        else:
            out['lop'] += 1; out['absent'] += 1
    return out


# ----------------------------------------------------------------- one employee
def _recovery_start(loan):
    s = (loan.recovery_start_month or '').strip()
    if s:
        try:
            y, mo = parse_period(s)
            return y, mo
        except ValueError:
            d = parse_date_flex(s)
            if d:
                return d.year, d.month
    d = loan.disbursement_date
    return (d.year + (d.month // 12), d.month % 12 + 1)


def compute_employee(user, struct, ctx, settings, existing=None):
    """Return (field dict for PayrollRecord, notes, loan_detail, reimbursement_ids)."""
    notes = []
    joined = parse_date_flex(user.joining_date)
    days = attendance_days(user.id, ctx, settings, joined)
    n = Decimal(ctx.n)
    paid = days['paid']
    if paid > n:
        paid = n
    ratio = (paid / n) if n else ZERO

    def earned(v):
        return r2(D(v) * ratio)

    basic, hra = earned(struct.basic_salary), earned(struct.hra)
    conv, med, spec = earned(struct.conveyance_allowance), earned(struct.medical_allowance), earned(struct.special_allowance)
    struct_gross = D(struct.basic_salary) + D(struct.hra) + D(struct.conveyance_allowance) + D(struct.medical_allowance) + D(struct.special_allowance)
    components = basic + hra + conv + med + spec
    lop_amt = r2(struct_gross - D(struct_gross) * ratio) if struct_gross else ZERO

    # overtime (approved only)
    ot_hours = ot_amount = ZERO
    if struct.overtime_eligible:
        ots = OvertimeRecord.objects.filter(employee_id=user.id, status='Approved', date__gte=ctx.first, date__lte=ctx.last)
        base_days = Decimal(days_base(settings, ctx.n))
        hourly = (struct_gross / (base_days * D(settings.shift_hours))) if struct_gross and base_days and D(settings.shift_hours) else ZERO
        for o in ots:
            ot_hours += D(o.overtime_hours)
            ot_amount += D(o.overtime_amount) if D(o.overtime_amount) > 0 else D(o.overtime_hours) * hourly * (D(o.overtime_rate_multiplier) if D(o.overtime_rate_multiplier) > 0 else D(settings.ot_multiplier))
        ot_amount = r2(ot_amount)

    other_earn = D(existing.other_earnings) if existing else ZERO
    other_ded = D(existing.other_deductions) if existing else ZERO
    gross = r2(components + ot_amount + other_earn)

    # reimbursements (approved, not yet paid through payroll)
    reimb = ZERO
    reimb_ids = []
    for rb in ReimbursementExpense.objects.filter(employee_id=user.id, status='Approved', expense_date__lte=ctx.last):
        reimb += D(rb.amount); reimb_ids.append(rb.id)
    reimb = r2(reimb)

    st = statutory(basic_earned=basic, gross_earned=gross, structure_gross=struct_gross, struct=struct, settings=settings, tds=struct.tds_monthly)

    # loans / advances
    loan_total = ZERO
    loan_detail = []
    for ln in EmployeeAdvanceLoan.objects.filter(employee_id=user.id, status='Active'):
        if D(ln.outstanding_balance) <= 0:
            continue
        if _recovery_start(ln) > (ctx.y, ctx.mo):
            continue
        amt = min(D(ln.emi_amount), D(ln.outstanding_balance))
        if amt > 0:
            loan_total += amt
            loan_detail.append({'loanId': ln.id, 'loanNumber': ln.loan_number, 'amount': float(amt)})

    total_ded = r2(st['pf_e'] + st['esi_e'] + st['pt'] + st['tds'] + loan_total + other_ded)
    net = r2(gross + reimb - total_ded)
    if net < 0:
        notes.append(f'Deductions exceed earnings by Rs. {abs(net)} — net pay is negative. Reduce loan EMI / adjustments before approval.')
    if not joined and user.joining_date:
        notes.append(f'Joining date "{user.joining_date}" could not be read; full month assumed.')
    if days['not_joined']:
        notes.append(f'Joined on {joined}: {int(days["not_joined"])} day(s) before joining are not paid.')
    if days['upcoming']:
        notes.append(f'{int(days["upcoming"])} day(s) of this month have not happened yet and are NOT paid. Recalculate after month end.')
    if days['unpaid_leave']:
        notes.append(f'{days["unpaid_leave"]} day(s) unpaid leave treated as LOP.')
    if D(struct.basic_salary) <= 0:
        notes.append('Basic salary is zero in the salary structure.')

    working_days = n - days['weekly_off'] - days['holiday'] - days['not_joined'] - days['upcoming']
    f = dict(
        month_year=period_label(ctx.y, ctx.mo), period_ym=f'{ctx.y}-{ctx.mo:02d}', financial_year=fin_year(ctx.y, ctx.mo),
        employee_name=(user.name if hasattr(user, 'name') and user.name else f'{user.first_name} {user.last_name}'.strip()) or user.username,
        department=user.department_name or 'General', designation=user.designation or 'Staff',
        calendar_days=r1(n), working_days=r1(max(working_days, ZERO)), present_days=r1(days['present']), leave_days=r1(days['leave']),
        loss_of_pay_days=r1(days['lop'] + days['not_joined'] + days['upcoming']), paid_days=r1(paid),
        weekly_offs=r1(days['weekly_off']), holidays=r1(days['holiday']), half_days=r1(days['half']), late_days=days['late'],
        overtime_hours=r2(ot_hours), basic_salary=basic, hra=hra, conveyance_allowance=conv, medical_allowance=med,
        special_allowance=spec, allowances=r2(conv + med + spec), overtime_amount=ot_amount, other_earnings=r2(other_earn),
        reimbursement_amount=reimb, gross_earnings=gross, pf_deduction=st['pf_e'], esi_deduction=st['esi_e'], pt_deduction=st['pt'],
        tds_deduction=st['tds'], loan_advance_recovery=r2(loan_total), other_deductions=r2(other_ded), total_deductions=total_ded,
        net_salary=net, employer_pf=st['pf_r'], employer_esi=st['esi_r'], total_ctc=r2(gross + st['pf_r'] + st['esi_r']),
        lop_deduction=lop_amt, loan_recovery_detail=loan_detail, reimbursement_ids=reimb_ids, calc_notes=notes,
        joining_date=user.joining_date or '', uan_number=struct.uan_number, esi_number=struct.esi_number, pan_number=struct.pan_number,
        bank_name=user.bank_name, bank_account_no=user.bank_account_no, bank_ifsc=user.bank_ifsc,
    )
    return f


# ----------------------------------------------------------------- whole month
def active_structures(last_day):
    best = {}
    for s in SalaryStructure.objects.filter(status='Active', effective_from__lte=last_day).order_by('effective_from', 'id'):
        best[s.employee_id] = s
    return best


def eligible_users(employee_ids=None):
    qs = User.objects.filter(is_active=True)
    if employee_ids:
        qs = qs.filter(id__in=employee_ids)
    return qs.order_by('id')


def calculate_month(period, employee_ids=None, dry_run=False):
    y, mo = parse_period(period)
    settings = PayrollSettings.load()
    ctx = MonthContext(y, mo, employee_ids)
    structs = active_structures(ctx.last)
    existing = {r.employee_id: r for r in PayrollRecord.objects.filter(period_ym=f'{y}-{mo:02d}')}
    legacy = {r.employee_id: r for r in PayrollRecord.objects.filter(month_year=period_label(y, mo), period_ym='')}

    results, skipped = [], []
    created = updated = 0
    for user in eligible_users(employee_ids):
        struct = structs.get(user.id)
        name = f'{user.first_name} {user.last_name}'.strip() or user.username
        if not struct:
            skipped.append({'employeeId': user.id, 'employeeName': name, 'reason': 'No salary structure'})
            continue
        rec = existing.get(user.id) or legacy.get(user.id)
        if rec and rec.status != 'Draft':
            skipped.append({'employeeId': user.id, 'employeeName': name, 'reason': f'Already {rec.status} (locked)'})
            continue
        fields = compute_employee(user, struct, ctx, settings, rec)
        fields['employee_name'] = name
        if dry_run:
            results.append({**fields, 'employee_id': user.id, 'status': 'Preview'})
            continue
        number = f'PAY-{y}{mo:02d}-{user.id}'
        with transaction.atomic():
            if rec:
                for k, v in fields.items():
                    setattr(rec, k, v)
                rec.processed_date = timezone.localdate()
                rec.save()
                updated += 1
            else:
                # a Draft that was deleted earlier keeps its number: bring that row back instead of clashing with it
                ghost = PayrollRecord.all_objects.filter(pk=number, is_active=False).first()
                if ghost:
                    for k, v in fields.items():
                        setattr(ghost, k, v)
                    ghost.is_active, ghost.deleted_at, ghost.deleted_by = True, None, ''
                    ghost.status = 'Draft'
                    ghost.processed_date = timezone.localdate()
                    ghost.save()
                    rec = ghost
                else:
                    rec = PayrollRecord.objects.create(id=number, payroll_number=number, employee_id=user.id, status='Draft',
                                                       processed_date=timezone.localdate(), **fields)
                created += 1
        results.append(rec)
    warnings = []
    if ctx.today <= ctx.last:
        warnings.append(f'{period_label(y, mo)} is not over yet — days after {ctx.today:%d %b} are unpaid in this draft. Recalculate after the month ends.')
    return {'period': f'{y}-{mo:02d}', 'label': period_label(y, mo), 'created': created, 'updated': updated, 'skipped': skipped,
            'warnings': warnings, 'records': results}


def recompute_totals(rec):
    """After manual adjustments on a Draft: recompute only the totals from the stored components."""
    settings = PayrollSettings.load()
    struct = SalaryStructure.objects.filter(employee_id=rec.employee_id, status='Active').order_by('-effective_from').first()
    gross = r2(D(rec.basic_salary) + D(rec.hra) + D(rec.conveyance_allowance) + D(rec.medical_allowance) + D(rec.special_allowance)
               + D(rec.overtime_amount) + D(rec.other_earnings))
    if struct:
        sg = D(struct.basic_salary) + D(struct.hra) + D(struct.conveyance_allowance) + D(struct.medical_allowance) + D(struct.special_allowance)
        st = statutory(basic_earned=rec.basic_salary, gross_earned=gross, structure_gross=sg, struct=struct, settings=settings, tds=rec.tds_deduction)
        rec.pf_deduction, rec.esi_deduction, rec.pt_deduction = st['pf_e'], st['esi_e'], st['pt']
        rec.employer_pf, rec.employer_esi = st['pf_r'], st['esi_r']
    rec.gross_earnings = gross
    rec.total_deductions = r2(D(rec.pf_deduction) + D(rec.esi_deduction) + D(rec.pt_deduction) + D(rec.tds_deduction)
                              + D(rec.loan_advance_recovery) + D(rec.other_deductions))
    rec.net_salary = r2(gross + D(rec.reimbursement_amount) - D(rec.total_deductions))
    rec.total_ctc = r2(gross + D(rec.employer_pf) + D(rec.employer_esi))
    return rec


# ----------------------------------------------------------------- workflow
def approve_record(rec, approver):
    if rec.status != 'Draft':
        raise ValueError(f'Only Draft payroll can be approved (this one is {rec.status}).')
    if D(rec.net_salary) < 0:
        raise ValueError('Net salary is negative — fix deductions first.')
    with transaction.atomic():
        for item in (rec.loan_recovery_detail or []):
            ln = EmployeeAdvanceLoan.objects.select_for_update().filter(id=item.get('loanId')).first()
            if ln:
                amt = D(item.get('amount'))
                ln.outstanding_balance = max(ZERO, D(ln.outstanding_balance) - amt)
                ln.paid_installments = (ln.paid_installments or 0) + 1
                if ln.outstanding_balance <= 0:
                    ln.status = 'Closed'
                ln.save()
        if rec.reimbursement_ids:
            ReimbursementExpense.objects.filter(id__in=rec.reimbursement_ids, status='Approved').update(status='Reimbursed')
        rec.status = 'Approved'
        rec.approved_by = approver
        rec.save()
    post_month_to_accounts(rec.period_ym)
    return rec


def reopen_record(rec):
    if rec.status != 'Approved':
        raise ValueError('Only an Approved (unpaid) payroll can be reopened.')
    with transaction.atomic():
        for item in (rec.loan_recovery_detail or []):
            ln = EmployeeAdvanceLoan.objects.select_for_update().filter(id=item.get('loanId')).first()
            if ln:
                ln.outstanding_balance = D(ln.outstanding_balance) + D(item.get('amount'))
                ln.paid_installments = max(0, (ln.paid_installments or 0) - 1)
                ln.status = 'Active'
                ln.save()
        if rec.reimbursement_ids:
            ReimbursementExpense.objects.filter(id__in=rec.reimbursement_ids, status='Reimbursed').update(status='Approved')
        rec.status = 'Draft'
        rec.approved_by = ''
        rec.save()
    post_month_to_accounts(rec.period_ym)
    return rec


def mark_paid(rec, paid_date, mode, reference, bank_ledger=''):
    if rec.status != 'Approved':
        raise ValueError(f'Only Approved payroll can be paid (this one is {rec.status}).')
    rec.status = 'Paid'
    rec.payment_status = 'Paid'
    rec.paid_date = paid_date
    rec.payment_mode = mode or 'Bank Transfer'
    rec.payment_ref = reference or ''
    rec.save()
    post_payment_to_accounts(rec, bank_ledger)
    return rec


# ----------------------------------------------------------------- accounts integration
def post_month_to_accounts(period_ym):
    """One journal per month from all Approved/Paid payroll: expense + payables. Idempotent (replaced on every call)."""
    if not period_ym:
        return ''
    try:
        from apps.accounting.ledger_models import Voucher
        from apps.accounting.posting import get_ledger
        vno = f'SAL-{period_ym}'
        recs = list(PayrollRecord.objects.filter(period_ym=period_ym, status__in=['Approved', 'Paid']))
        if not recs:
            Voucher.objects.filter(voucher_no=vno).delete()
            return ''
        S = lambda attr: sum((D(getattr(r, attr)) for r in recs), ZERO)
        y, mo = parse_period(period_ym)
        vdate = min(date(y, mo, calendar.monthrange(y, mo)[1]), timezone.localdate()) if date(y, mo, 1) <= timezone.localdate() else date(y, mo, 1)
        emp_cost = S('employer_pf') + S('employer_esi')
        L = lambda name, grp: get_ledger(name, grp).pk
        rows = [
            (L('SALARY EXPENSES', 'Direct Expenses'), S('gross_earnings'), ZERO),
            (L('EMPLOYER PF & ESI CONTRIBUTION', 'Direct Expenses'), emp_cost, ZERO),
            (L('EMPLOYEE REIMBURSEMENTS', 'Indirect Expenses'), S('reimbursement_amount'), ZERO),
            (L('Salary Payable', 'Current Liabilities'), ZERO, S('net_salary')),
            (L('PF Payable', 'Duties & Taxes'), ZERO, S('pf_deduction') + S('employer_pf')),
            (L('ESI Payable', 'Duties & Taxes'), ZERO, S('esi_deduction') + S('employer_esi')),
            (L('Professional Tax Payable', 'Duties & Taxes'), ZERO, S('pt_deduction')),
            (L('TDS Payable', 'Duties & Taxes'), ZERO, S('tds_deduction')),
            (L('Loans & Advances (Asset)', 'Loans & Advances (Asset)'), ZERO, S('loan_advance_recovery')),
            (L('Other Payroll Deductions', 'Current Liabilities'), ZERO, S('other_deductions')),
        ]
        lines = [{'ledger_id': lid, 'debit': str(dr), 'credit': str(cr)} for lid, dr, cr in rows if dr or cr]
        total = sum(D(l['debit']) for l in lines)
        Voucher.objects.update_or_create(voucher_no=vno, defaults={
            'voucher_type': 'Journal', 'voucher_date': vdate, 'status': 'Posted', 'created_by': 'Payroll',
            'narration': f'Salary for {period_label(y, mo)} — {len(recs)} employees', 'lines': lines, 'total_amount': total})
        PayrollRecord.objects.filter(period_ym=period_ym, status__in=['Approved', 'Paid']).update(accounting_voucher_ref=vno)
        return vno
    except Exception:
        log.exception('Payroll -> accounts posting failed for %s', period_ym)
        return ''


def post_payment_to_accounts(rec, bank_ledger=''):
    try:
        from apps.accounting.ledger_models import Voucher
        from apps.accounting.posting import get_ledger, bank_cash_ledger
        net = D(rec.net_salary)
        if net <= 0:
            return
        bank = bank_cash_ledger(rec.payment_mode, bank_ledger)
        pay = get_ledger('Salary Payable', 'Current Liabilities')
        Voucher.objects.update_or_create(voucher_no=f'SALPAY-{rec.payroll_number}', defaults={
            'voucher_type': 'Payment', 'voucher_date': rec.paid_date or timezone.localdate(), 'status': 'Posted', 'created_by': 'Payroll',
            'reference': rec.payment_ref, 'narration': f'Salary paid to {rec.employee_name} for {rec.month_year}', 'total_amount': net,
            'lines': [{'ledger_id': pay.pk, 'debit': str(net), 'credit': '0'}, {'ledger_id': bank.pk, 'debit': '0', 'credit': str(net)}]})
    except Exception:
        log.exception('Salary payment -> accounts posting failed for %s', rec.payroll_number)
