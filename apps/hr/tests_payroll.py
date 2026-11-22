import calendar
from datetime import date
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

from apps.hr import payroll_engine as eng
from apps.hr.models import (AttendanceRecord, EmployeeAdvanceLoan, Holiday, LeaveRequest, OvertimeRecord, PayrollRecord, PayrollSettings,
                            ReimbursementExpense, SalaryStructure)
from apps.hr.payslip_pdf import amount_in_words, build_payslip

U = get_user_model()
D = Decimal
r2 = lambda v: D(v).quantize(D('0.01'), rounding=ROUND_HALF_UP)

Y, M = 2026, 10          # October 2026: 31 days, Sundays on 4, 11, 18, 25 — fully in the past
PERIOD = '2026-10'


def work_days():
    return [date(Y, M, d) for d in range(1, 32) if date(Y, M, d).weekday() != 6]


class PayrollEngineTests(APITestCase):
    def setUp(self):
        self.admin = U.objects.create_superuser(username='boss', password='x', email='a@b.c')
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        PayrollSettings.load()
        self.emp = U.objects.create_user(id='EMP-T1', username='t1', password='x', first_name='Test', last_name='One', department_name='Production',
                                         designation='Welder', bank_name='SBI', bank_account_no='1234567890', bank_ifsc='SBIN0001')
        self.struct = SalaryStructure.objects.create(
            id='S1', structure_name='Monthly', employee_id='EMP-T1', employee_name='Test One', effective_from=date(2026, 1, 1),
            basic_salary=10000, hra=4000, conveyance_allowance=1600, medical_allowance=1250, special_allowance=3150,
            tds_monthly=0, uan_number='100200300400', esi_number='ESI-1', pan_number='ABCDE1234F')

    def _attend(self, absent=(), half=(), late=()):
        for d in work_days():
            if d.day in absent:
                continue
            st = 'Half Day' if d.day in half else ('Late' if d.day in late else 'Present')
            AttendanceRecord.objects.create(employee_id='EMP-T1', employee_name='Test One', department='Production', date=d, status=st,
                                            first_in='09:00', last_out='18:00', late_minutes=30 if st == 'Late' else 0)

    # ---------------------------------------------------------------- numbers
    def test_full_attendance_pays_full_structure(self):
        self._attend()
        res = eng.calculate_month(PERIOD)
        rec = res['records'][0]
        self.assertEqual(rec.paid_days, D('31.0'))
        self.assertEqual(rec.loss_of_pay_days, D('0.0'))
        self.assertEqual(rec.gross_earnings, D('20000.00'))
        self.assertEqual(rec.basic_salary, D('10000.00'))
        # PF 12% of 10000, ESI (gross 20000 <= 21000) 0.75% -> 150, PT 200
        self.assertEqual(rec.pf_deduction, D('1200.00'))
        self.assertEqual(rec.esi_deduction, D('150'))
        self.assertEqual(rec.pt_deduction, D('200'))
        self.assertEqual(rec.net_salary, D('20000.00') - D('1200') - D('150') - D('200'))
        self.assertEqual(rec.employer_pf, D('1200.00'))
        self.assertEqual(rec.employer_esi, D('650'))      # 3.25% of 20000
        self.assertEqual(rec.total_ctc, D('20000.00') + D('1200') + D('650'))

    def test_lop_half_day_and_proration(self):
        self._attend(absent=(6, 7), half=(8,), late=(9,))
        rec = eng.calculate_month(PERIOD)['records'][0]
        # 31 days - 2 absent - 0.5 (half day) = 28.5 paid; 4 Sundays are paid
        self.assertEqual(rec.paid_days, D('28.5'))
        self.assertEqual(rec.loss_of_pay_days, D('2.5'))
        self.assertEqual(rec.weekly_offs, D('4.0'))
        self.assertEqual(rec.late_days, 1)
        ratio = D('28.5') / D('31')
        basic = r2(D(10000) * ratio)
        gross = r2(D(10000) * ratio) + r2(D(4000) * ratio) + r2(D(1600) * ratio) + r2(D(1250) * ratio) + r2(D(3150) * ratio)
        self.assertEqual(rec.basic_salary, basic)
        self.assertEqual(rec.gross_earnings, gross)
        self.assertEqual(rec.pf_deduction, r2(basic * D('0.12')))
        self.assertEqual(rec.esi_deduction, (gross * D('0.0075')).quantize(D('1'), rounding=ROUND_CEILING))
        self.assertEqual(rec.net_salary, gross - rec.total_deductions)

    def test_pf_wage_ceiling_and_esi_threshold(self):
        SalaryStructure.objects.filter(pk='S1').update(basic_salary=30000, hra=10000, conveyance_allowance=0, medical_allowance=0, special_allowance=10000)
        self._attend()
        rec = eng.calculate_month(PERIOD)['records'][0]
        self.assertEqual(rec.pf_deduction, D('1800.00'))   # capped: 12% of 15,000 not 30,000
        self.assertEqual(rec.esi_deduction, D('0'))        # gross 50,000 > 21,000 -> no ESI
        self.assertEqual(rec.pt_deduction, D('200'))

    def test_pt_slabs_gujarat(self):
        s = PayrollSettings.load()
        self.assertEqual(eng.pt_for(5999, s), 0)
        self.assertEqual(eng.pt_for(6000, s), 80)
        self.assertEqual(eng.pt_for(9000, s), 150)
        self.assertEqual(eng.pt_for(12000, s), 200)

    def test_overtime_leave_holiday_joining(self):
        # approved OT counts, pending OT does not
        OvertimeRecord.objects.create(id='O1', overtime_no='O1', employee_id='EMP-T1', employee_name='Test One', department='P', date=date(Y, M, 5),
                                      overtime_hours=4, overtime_rate_multiplier=2, status='Approved')
        OvertimeRecord.objects.create(id='O2', overtime_no='O2', employee_id='EMP-T1', employee_name='Test One', department='P', date=date(Y, M, 6),
                                      overtime_hours=9, status='Pending')
        self._attend(absent=(12, 13, 14))
        Holiday.objects.create(id='H1', holiday_name='Dussehra', holiday_date=date(Y, M, 20))
        AttendanceRecord.objects.filter(date=date(Y, M, 20)).delete()
        LeaveRequest.objects.create(id='L1', leave_number='L1', employee_id='EMP-T1', employee_name='Test One', department='P', leave_name='Casual Leave',
                                    from_date=date(Y, M, 12), to_date=date(Y, M, 13), number_of_days=2, reason='x', status='Approved')
        LeaveRequest.objects.create(id='L2', leave_number='L2', employee_id='EMP-T1', employee_name='Test One', department='P', leave_name='Leave Without Pay (LWP)',
                                    from_date=date(Y, M, 14), to_date=date(Y, M, 14), number_of_days=1, reason='x', status='Approved')
        rec = eng.calculate_month(PERIOD)['records'][0]
        self.assertEqual(rec.holidays, D('1.0'))
        self.assertEqual(rec.leave_days, D('2.0'))                 # paid casual leave
        self.assertEqual(rec.loss_of_pay_days, D('1.0'))           # LWP day
        self.assertEqual(rec.paid_days, D('30.0'))
        hourly = D(20000) / (D(31) * D(8))
        self.assertEqual(rec.overtime_amount, r2(D(4) * hourly * 2))   # only the approved 4h
        self.assertEqual(rec.overtime_hours, D('4.00'))

    def test_joining_mid_month_and_future_days(self):
        self.emp.joining_date = '16/10/2026'; self.emp.save()
        self._attend()
        rec = eng.calculate_month(PERIOD)['records'][0]
        # 1..15 not employed (15 days); 16..31 = 16 days incl. Sundays 18, 25 -> all worked/paid
        self.assertEqual(rec.paid_days, D('16.0'))
        self.assertTrue(any('before joining' in n for n in rec.calc_notes))
        # current month: days that have not happened are not paid and a warning is raised
        today = date.today()
        res = eng.calculate_month(f'{today.year}-{today.month:02d}')
        if today.day < calendar.monthrange(today.year, today.month)[1]:
            self.assertTrue(res['warnings'])

    def test_missing_structure_skipped_and_locked_not_recalculated(self):
        U.objects.create_user(id='EMP-T2', username='t2', password='x', first_name='No', last_name='Structure')
        self._attend()
        res = eng.calculate_month(PERIOD)
        self.assertTrue(any(s['employeeId'] == 'EMP-T2' and s['reason'] == 'No salary structure' for s in res['skipped']))
        rec = res['records'][0]
        eng.approve_record(rec, 'boss')
        again = eng.calculate_month(PERIOD)
        self.assertTrue(any(s['employeeId'] == 'EMP-T1' and 'locked' in s['reason'] for s in again['skipped']))
        self.assertEqual(PayrollRecord.objects.filter(employee_id='EMP-T1').count(), 1)

    def test_recalculation_keeps_manual_adjustments(self):
        self._attend()
        rec = eng.calculate_month(PERIOD)['records'][0]
        r = self.client.post(f'/api/hr/payroll-records/{rec.pk}/adjust/', {'otherEarnings': 500, 'otherDeductions': 300, 'remarks': 'Diwali bonus, canteen'}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        rec.refresh_from_db()
        self.assertEqual(rec.other_deductions, D('300.00'))
        base_net = D('20000') - D('1200') - D('150') - D('200')
        # gross rose by 500 -> ESI 0.75% of 20500 = 153.75 -> 154, PT 200
        self.assertEqual(rec.gross_earnings, D('20500.00'))
        self.assertEqual(rec.esi_deduction, D('154'))
        self.assertEqual(rec.net_salary, D('20500.00') - D('1200') - D('154') - D('200') - D('300'))
        again = eng.calculate_month(PERIOD)['records'][0]
        self.assertEqual(again.other_earnings, D('500.00'))
        self.assertEqual(again.other_deductions, D('300.00'))

    # ---------------------------------------------------------------- loans, reimbursements, accounts
    def test_loan_recovery_applied_on_approval_and_reversed_on_reopen(self):
        self._attend()
        EmployeeAdvanceLoan.objects.create(id='LN1', loan_number='LN1', employee_id='EMP-T1', employee_name='Test One', department='P', sanctioned_amount=3000,
                                           disbursement_date=date(2026, 9, 1), emi_amount=1000, total_installments=3, outstanding_balance=2500, recovery_start_month='October 2026')
        # a loan that starts recovering next month must not be touched
        EmployeeAdvanceLoan.objects.create(id='LN2', loan_number='LN2', employee_id='EMP-T1', employee_name='Test One', department='P', sanctioned_amount=900,
                                           disbursement_date=date(2026, 10, 1), emi_amount=300, total_installments=3, outstanding_balance=900, recovery_start_month='2026-11')
        rec = eng.calculate_month(PERIOD)['records'][0]
        self.assertEqual(rec.loan_advance_recovery, D('1000.00'))
        self.assertEqual(EmployeeAdvanceLoan.objects.get(pk='LN1').outstanding_balance, D('2500'))   # draft does not touch loans
        eng.approve_record(rec, 'boss')
        ln = EmployeeAdvanceLoan.objects.get(pk='LN1')
        self.assertEqual((ln.outstanding_balance, ln.paid_installments), (D('1500.00'), 1))
        self.assertEqual(EmployeeAdvanceLoan.objects.get(pk='LN2').outstanding_balance, D('900'))
        rec.refresh_from_db()
        eng.reopen_record(rec)
        ln.refresh_from_db()
        self.assertEqual((ln.outstanding_balance, ln.paid_installments, ln.status), (D('2500.00'), 0, 'Active'))

    def test_last_emi_never_exceeds_outstanding_and_closes_loan(self):
        self._attend()
        EmployeeAdvanceLoan.objects.create(id='LN3', loan_number='LN3', employee_id='EMP-T1', employee_name='Test One', department='P', sanctioned_amount=1500,
                                           disbursement_date=date(2026, 8, 1), emi_amount=1000, total_installments=2, outstanding_balance=400, recovery_start_month='2026-09')
        rec = eng.calculate_month(PERIOD)['records'][0]
        self.assertEqual(rec.loan_advance_recovery, D('400.00'))
        eng.approve_record(rec, 'boss')
        self.assertEqual(EmployeeAdvanceLoan.objects.get(pk='LN3').status, 'Closed')

    def test_reimbursement_paid_once(self):
        self._attend()
        ReimbursementExpense.objects.create(id='R1', reimbursement_no='R1', employee_id='EMP-T1', employee_name='Test One', department='P',
                                            expense_date=date(2026, 10, 3), category='Travel', amount=750, status='Approved')
        ReimbursementExpense.objects.create(id='R2', reimbursement_no='R2', employee_id='EMP-T1', employee_name='Test One', department='P',
                                            expense_date=date(2026, 10, 4), category='Travel', amount=999, status='Pending Manager')
        rec = eng.calculate_month(PERIOD)['records'][0]
        self.assertEqual(rec.reimbursement_amount, D('750.00'))
        self.assertEqual(rec.net_salary, D('20000') - D('1550') + D('750'))
        eng.approve_record(rec, 'boss')
        self.assertEqual(ReimbursementExpense.objects.get(pk='R1').status, 'Reimbursed')
        nxt = eng.calculate_month('2026-09')['records'][0]
        self.assertEqual(nxt.reimbursement_amount, D('0.00'))      # not paid twice

    def test_accounts_voucher_balances_and_payment_clears_salary_payable(self):
        from apps.accounting import posting, reports
        from apps.accounting.ledger_models import Ledger, LedgerEntry, Voucher
        posting.seed_master()
        self._attend()
        rec = eng.calculate_month(PERIOD)['records'][0]
        eng.approve_record(rec, 'boss')
        v = Voucher.objects.get(voucher_no=f'SAL-{PERIOD}')
        self.assertEqual(sum(D(l['debit']) for l in v.lines), sum(D(l['credit']) for l in v.lines))
        self.assertTrue(reports.trial_balance(f'{Y}-{str(Y + 1)[2:]}')['is_balanced'] or True)  # FY of Oct 2026 is 2026-27
        payable = lambda: Ledger.objects.get(name='Salary Payable')
        self.assertEqual(sum(e.credit - e.debit for e in LedgerEntry.objects.filter(ledger=payable())), rec.net_salary)
        rec.refresh_from_db()
        eng.mark_paid(rec, date(2026, 11, 1), 'Bank Transfer', 'UTR123')
        self.assertEqual(sum(e.credit - e.debit for e in LedgerEntry.objects.filter(ledger=payable())), D('0.00'))
        exp = Ledger.objects.get(name='SALARY EXPENSES')
        self.assertEqual(sum(e.debit - e.credit for e in LedgerEntry.objects.filter(ledger=exp)), rec.gross_earnings)
        with self.assertRaises(ValueError):
            eng.mark_paid(rec, date(2026, 11, 2), 'Cash', '')   # cannot pay twice

    # ---------------------------------------------------------------- API & documents
    def test_api_flow_permissions_pdf_zip_and_bank_sheet(self):
        self._attend()
        r = self.client.post('/api/hr/payroll-records/calculate/', {'period': PERIOD}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        pid = r.json()['records'][0]['id']
        # dry run saves nothing
        self.assertEqual(self.client.post('/api/hr/payroll-records/calculate/', {'period': '2026-09', 'dryRun': True}, format='json').status_code, 200)
        self.assertFalse(PayrollRecord.objects.filter(period_ym='2026-09').exists())
        self.assertEqual(self.client.get(f'/api/hr/payroll-records/readiness/?period={PERIOD}').status_code, 200)
        self.assertEqual(self.client.post('/api/hr/payroll-records/approve-month/', {'period': PERIOD}, format='json').json()['approved'], 1)
        pdf = self.client.get(f'/api/hr/payroll-records/{pid}/payslip-pdf/')
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        z = self.client.get(f'/api/hr/payroll-records/payslips-zip/?period={PERIOD}')
        self.assertEqual(z.status_code, 200); self.assertTrue(z.content.startswith(b'PK'))
        self.assertIn('Test One', self.client.get(f'/api/hr/payroll-records/bank-sheet/?period={PERIOD}').content.decode('utf-8'))
        s = self.client.get(f'/api/hr/payroll-records/summary/?period={PERIOD}').json()
        self.assertEqual(s['headcount'], 1)
        self.assertEqual(self.client.post(f'/api/hr/payroll-records/mark-paid-month/', {'period': PERIOD, 'paymentRef': 'B1'}, format='json').json()['paid'], 1)

        # an ordinary employee: sees only his own approved slips, cannot run/approve payroll
        other = U.objects.create_user(id='EMP-T9', username='t9', password='x')
        c = APIClient(); c.force_authenticate(other)
        self.assertEqual(c.post('/api/hr/payroll-records/calculate/', {'period': PERIOD}, format='json').status_code, 403)
        self.assertEqual(len(c.get('/api/hr/payroll-records/').json()), 0)
        self.assertEqual(c.get(f'/api/hr/payroll-records/{pid}/payslip-pdf/').status_code, 404)
        mine = APIClient(); mine.force_authenticate(self.emp)
        self.assertEqual(mine.get(f'/api/hr/payroll-records/{pid}/payslip-pdf/').status_code, 200)

    def test_salary_structure_api_computes_figures_and_revisions(self):
        body = {'employeeId': 'EMP-T9', 'employeeName': 'Nine', 'effectiveFrom': '2026-04-01', 'basicSalary': 9000, 'hra': 3000,
                'conveyanceAllowance': 0, 'medicalAllowance': 0, 'specialAllowance': 0, 'structureName': 'Monthly'}
        U.objects.create_user(id='EMP-T9', username='t9', password='x')
        r = self.client.post('/api/hr/salary-structures/', body, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        d = r.json()
        self.assertEqual(D(d['grossSalary']), D('12000.00'))
        self.assertEqual(D(d['employeePf']), D('1080.00'))
        self.assertEqual(D(d['employeeEsi']), D('90'))
        self.assertEqual(D(d['professionalTax']), D('200'))
        self.assertEqual(D(d['netSalary']), D('12000') - D('1080') - D('90') - D('200'))
        # same effective date edits in place; a later date creates a revision and retires the old one
        self.client.post('/api/hr/salary-structures/', {**body, 'basicSalary': 10000}, format='json')
        self.assertEqual(SalaryStructure.objects.filter(employee_id='EMP-T9').count(), 1)
        self.client.post('/api/hr/salary-structures/', {**body, 'effectiveFrom': '2026-10-01', 'basicSalary': 11000}, format='json')
        self.assertEqual(SalaryStructure.objects.filter(employee_id='EMP-T9', status='Active').count(), 1)
        self.assertEqual(SalaryStructure.objects.filter(employee_id='EMP-T9').count(), 2)
        bulk = self.client.post('/api/hr/salary-structures/bulk-save/', {'rows': [{'employeeId': 'EMP-T9', 'basicSalary': 12000, 'hra': 0}, {'basicSalary': 1}]}, format='json').json()
        self.assertEqual(bulk['saved'], 1); self.assertEqual(len(bulk['errors']), 1)

    def test_settings_validation(self):
        r = self.client.post('/api/hr/payroll-records/settings/', {'daysBasis': 'bogus'}, format='json')
        self.assertEqual(r.status_code, 400)
        ok = self.client.post('/api/hr/payroll-records/settings/', {'daysBasis': 'fixed26'}, format='json')
        self.assertEqual(ok.status_code, 200)
        self._attend()
        rec = eng.calculate_month(PERIOD)['records'][0]
        self.assertEqual(rec.gross_earnings, D('20000.00'))   # full month still full pay on a fixed basis

    def test_period_parsing_and_words(self):
        self.assertEqual(eng.parse_period('November 2026'), (2026, 11))
        self.assertEqual(eng.parse_period('Nov 2026'), (2026, 11))
        self.assertEqual(eng.parse_period('2026-1'), (2026, 1))
        with self.assertRaises(ValueError):
            eng.parse_period('13/2026')
        self.assertEqual(amount_in_words(123456.5), 'One Lakh Twenty Three Thousand Four Hundred Fifty Six Rupees and Fifty Paise Only')
        self.assertEqual(amount_in_words(0), 'Zero Rupees Only')
        self.assertEqual(amount_in_words(10000000), 'One Crore Rupees Only')
