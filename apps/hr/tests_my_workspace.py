"""
My Workspace self-service security tests.

An ordinary employee must only see / create their own records and must not be
able to approve their own requests or read other people's payroll.
"""
from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.hr.models import AttendanceRecord, MissedPunchRequest, OvertimeRecord, PayrollRecord


def _payroll(pk, emp, status='Processed'):
    return PayrollRecord.objects.create(
        id=pk, payroll_number=pk, month_year='October 2026', employee_id=emp.id,
        employee_name=emp.username, department='Ops', designation='Exec',
        status=status, processed_date=date(2026, 10, 31),
    )


class MyWorkspaceSecurityTests(TestCase):
    def setUp(self):
        mk = lambda i, role: User.objects.create(
            id=i, username=i.lower(), first_name=i, last_name='T', role_type=role,
            department_name='Ops',
        )
        self.alice = mk('EMP-A', 'employee')
        self.bob = mk('EMP-B', 'employee')
        self.mgr = mk('EMP-M', 'department_manager')
        self.admin = mk('EMP-X', 'admin')
        self.c = APIClient()

    def as_user(self, u):
        self.c.force_authenticate(user=u)
        return self.c

    # ---- payroll ----
    def test_employee_sees_only_own_non_draft_payslips(self):
        _payroll('P-A1', self.alice)
        _payroll('P-A2', self.alice, status='Draft')
        _payroll('P-B1', self.bob)
        r = self.as_user(self.alice).get('/api/payroll-records/')
        self.assertEqual(r.status_code, 200)
        ids = {x['id'] for x in (r.json() if isinstance(r.json(), list) else r.json()['results'])}
        self.assertEqual(ids, {'P-A1'})

    def test_manager_cannot_read_other_payroll(self):
        _payroll('P-B1', self.bob)
        r = self.as_user(self.mgr).get('/api/payroll-records/')
        data = r.json() if isinstance(r.json(), list) else r.json()['results']
        self.assertEqual(data, [])

    def test_employee_cannot_write_or_approve_payroll(self):
        rec = _payroll('P-A1', self.alice, status='Draft')
        rec.status = 'Processed'
        rec.save()
        self.assertEqual(self.as_user(self.alice).post('/api/payroll-records/P-A1/approve/').status_code, 403)
        self.assertEqual(self.as_user(self.alice).patch('/api/payroll-records/P-A1/', {'netSalary': 999999}, format='json').status_code, 403)
        self.assertEqual(self.as_user(self.alice).post('/api/payroll-records/generate-monthly-payroll/', {}, format='json').status_code, 403)

    # ---- missed punch ----
    def test_missed_punch_forced_to_own_identity_and_pending(self):
        r = self.as_user(self.alice).post('/api/missed-punches/', {
            'id': 'MP-1', 'request_number': 'MP-1', 'employee_id': 'EMP-B', 'employee_name': 'Bob',
            'date': '2026-11-20', 'missing_punch_type': 'Check-Out', 'requested_time': '19:00',
            'reason': 'forgot', 'status': 'Approved',
        }, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        mp = MissedPunchRequest.objects.get(id='MP-1')
        self.assertEqual(mp.employee_id, 'EMP-A')
        self.assertEqual(mp.status, 'Pending')

    def test_employee_cannot_approve_own_missed_punch(self):
        MissedPunchRequest.objects.create(
            id='MP-2', request_number='MP-2', employee_id='EMP-A', employee_name='A',
            date=date(2026, 11, 20), missing_punch_type='Check-Out', requested_time='19:00', reason='x',
        )
        self.assertEqual(self.as_user(self.alice).post('/api/missed-punches/MP-2/approve/').status_code, 403)

    def test_manager_approval_updates_attendance(self):
        AttendanceRecord.objects.create(
            id='ATT-1', employee_id='EMP-A', employee_name='A', department='Ops',
            date=date(2026, 11, 20), check_in='09:00', status='Present', is_missing_punch=True,
        )
        MissedPunchRequest.objects.create(
            id='MP-3', request_number='MP-3', employee_id='EMP-A', employee_name='A',
            date=date(2026, 11, 20), missing_punch_type='Check-Out', requested_time='19:00', reason='x',
        )
        r = self.as_user(self.mgr).post('/api/missed-punches/MP-3/approve/')
        self.assertEqual(r.status_code, 200, r.content)
        att = AttendanceRecord.objects.get(id='ATT-1')
        self.assertEqual(att.check_out, '19:00')
        self.assertEqual(float(att.total_hours), 10.0)
        self.assertFalse(att.is_missing_punch)
        # cannot be approved twice
        self.assertEqual(self.as_user(self.mgr).post('/api/missed-punches/MP-3/approve/').status_code, 400)

    # ---- overtime ----
    def test_overtime_scoped_forced_pending_and_not_self_approvable(self):
        r = self.as_user(self.alice).post('/api/overtime-records/', {
            'id': 'OT-1', 'overtime_no': 'OT-1', 'employee_id': 'EMP-B', 'department': 'Ops',
            'date': '2026-11-20', 'overtime_hours': 2, 'reason': 'urgent', 'status': 'Approved',
            'overtime_amount': 5000,
        }, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        ot = OvertimeRecord.objects.get(id='OT-1')
        self.assertEqual((ot.employee_id, ot.status, float(ot.overtime_amount)), ('EMP-A', 'Pending', 0.0))
        # bob cannot see alice's overtime
        data = self.as_user(self.bob).get('/api/overtime-records/').json()
        data = data if isinstance(data, list) else data['results']
        self.assertEqual(data, [])
        # alice cannot approve her own
        self.assertEqual(self.as_user(self.alice).post('/api/overtime-records/OT-1/approve/').status_code, 403)
        # manager can
        self.assertEqual(self.as_user(self.mgr).post('/api/overtime-records/OT-1/approve/').status_code, 200)
