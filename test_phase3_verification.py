import os
import django
import sys
from datetime import date, datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.organization.models import Department
from apps.hr.models import (
    AttendanceRecord, ShiftMaster, LeaveType, LeaveBalance, LeaveRequest,
    MissedPunchRequest, AttendanceRegularization, Holiday
)
from apps.projects.models import ProjectTask

User = get_user_model()


def run_phase3_verification():
    print("=" * 80)
    print("STARTING UMAERP PHASE 3 - ATTENDANCE, LEAVE, DASHBOARD & TASK VERIFICATION")
    print("=" * 80)

    client = APIClient()

    # 1. Setup / Retrieve Test Departments
    dept_prod = Department.objects.filter(code__iexact='PROD').first() or Department.objects.filter(name__icontains='Production').first()
    if not dept_prod:
        dept_prod = Department.objects.create(id='DEPT-TEST-PROD', code='P3PROD', name='Production', status='Active')

    dept_design = Department.objects.filter(code__iexact='DES').first() or Department.objects.filter(name__icontains='Design').first()
    if not dept_design:
        dept_design = Department.objects.create(id='DEPT-TEST-DES', code='P3DES', name='Design', status='Active')

    # 2. Setup / Retrieve Test Users
    # Super Admin
    super_admin, _ = User.objects.get_or_create(
        username='test_super_admin',
        defaults={
            'id': 'EMP-P3-SUPER',
            'email': 'super@umaerp.com',
            'role_type': 'super_admin',
            'data_scope': 'all',
            'is_superuser': True,
            'is_staff': True,
            'is_active': True,
        }
    )
    super_admin.set_password('pass123')
    super_admin.save()

    # Admin
    admin_user, _ = User.objects.get_or_create(
        username='test_admin',
        defaults={
            'id': 'EMP-P3-ADMIN',
            'email': 'admin@umaerp.com',
            'role_type': 'admin',
            'data_scope': 'all',
            'is_staff': True,
            'is_active': True,
        }
    )
    admin_user.set_password('pass123')
    admin_user.save()

    # Prod Manager
    prod_mgr, _ = User.objects.get_or_create(
        username='test_prod_mgr',
        defaults={
            'id': 'EMP-P3-MGR-PROD',
            'email': 'prod.mgr@umaerp.com',
            'role_type': 'department_manager',
            'data_scope': 'department',
            'department': dept_prod,
            'department_name': 'Production',
            'can_assign_tasks': True,
            'can_approve_leaves': True,
            'is_active': True,
        }
    )
    prod_mgr.set_password('pass123')
    prod_mgr.save()

    # Prod Employee
    prod_emp, _ = User.objects.get_or_create(
        username='test_prod_emp',
        defaults={
            'id': 'EMP-P3-EMP-PROD',
            'email': 'prod.emp@umaerp.com',
            'role_type': 'employee',
            'data_scope': 'own',
            'department': dept_prod,
            'department_name': 'Production',
            'is_active': True,
        }
    )
    prod_emp.set_password('pass123')
    prod_emp.save()

    # Design Employee (Different Department)
    des_emp, _ = User.objects.get_or_create(
        username='test_des_emp',
        defaults={
            'id': 'EMP-P3-EMP-DES',
            'email': 'des.emp@umaerp.com',
            'role_type': 'employee',
            'data_scope': 'own',
            'department': dept_design,
            'department_name': 'Design',
            'is_active': True,
        }
    )
    des_emp.set_password('pass123')
    des_emp.save()

    # Setup Leave Types & Balances
    lt_cl, _ = LeaveType.objects.get_or_create(
        id='LT-01',
        defaults={
            'leave_code': 'CL',
            'leave_name': 'Casual Leave (CL)',
            'annual_quota': 12.0,
            'status': 'Active'
        }
    )
    bal_prod, _ = LeaveBalance.objects.get_or_create(
        employee_id=prod_emp.id,
        leave_type_id=lt_cl.id,
        financial_year='2026-2027',
        defaults={
            'id': f"BAL-{prod_emp.id}-CL-26",
            'employee_name': prod_emp.name or prod_emp.username,
            'department': 'Production',
            'leave_code': 'CL',
            'leave_name': 'Casual Leave (CL)',
            'total_credited': 12.0,
            'used': 0.0,
            'pending_approval': 0.0,
            'available_balance': 12.0,
        }
    )
    bal_prod.total_credited = 12.0
    bal_prod.used = 0.0
    bal_prod.pending_approval = 0.0
    bal_prod.available_balance = 12.0
    bal_prod.save()

    # Clear today's test attendance for clean test
    today = date.today()
    AttendanceRecord.objects.filter(employee_id__in=[prod_emp.id, des_emp.id], date=today).delete()
    LeaveRequest.objects.filter(employee_id__in=[prod_emp.id, des_emp.id]).delete()
    ProjectTask.objects.filter(assigned_to_id__in=[prod_emp.id, des_emp.id]).delete()

    print("\n[Test 1] Attendance Management: Personal Check-In & Duplicate Punch Prevention...")
    # 1.1 Unauthenticated punch attempt
    client.force_authenticate(user=None)
    res = client.post('/api/attendance-records/check-in/', {})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED, f"Expected 401, got {res.status_code}"
    print("  -> Unauthenticated punch: OK (HTTP 401)")

    # 1.2 Authenticated Check-In for prod_emp
    client.force_authenticate(user=prod_emp)
    res = client.post('/api/attendance-records/check-in/', {})
    assert res.status_code == status.HTTP_200_OK, f"Expected 200, got {res.status_code}: {res.data}"
    rec_data = res.data.get('record', {})
    assert rec_data.get('employee_id') == prod_emp.id, f"Wrong employee: {rec_data}"
    assert rec_data.get('check_in'), "Check-in time missing"
    assert rec_data.get('status') in ['Present', 'Late'], f"Unexpected status: {rec_data.get('status')}"
    print(f"  -> Check-In successful: Status={rec_data.get('status')} at {rec_data.get('check_in')}")

    # 1.3 Duplicate Check-In Attempt
    res_dup = client.post('/api/attendance-records/check-in/', {})
    assert res_dup.status_code == status.HTTP_400_BAD_REQUEST, f"Expected 400 for duplicate, got {res_dup.status_code}"
    assert "Duplicate punch" in str(res_dup.data), f"Expected duplicate error message: {res_dup.data}"
    print("  -> Duplicate Check-In blocked: OK (HTTP 400)")

    print("\n[Test 2] Attendance Management: Personal Check-Out & Working Hours Calculation...")
    # 2.1 Check-Out
    res_out = client.post('/api/attendance-records/check-out/', {})
    assert res_out.status_code == status.HTTP_200_OK, f"Expected 200, got {res_out.status_code}: {res_out.data}"
    out_data = res_out.data.get('record', {})
    assert out_data.get('check_out'), "Check-out time missing"
    print(f"  -> Check-Out successful: Out={out_data.get('check_out')}, Hours={out_data.get('total_hours')}")

    # 2.2 Duplicate Check-Out Attempt
    res_out_dup = client.post('/api/attendance-records/check-out/', {})
    assert res_out_dup.status_code == status.HTTP_400_BAD_REQUEST, f"Expected 400 for duplicate checkout, got {res_out_dup.status_code}"
    print("  -> Duplicate Check-Out blocked: OK (HTTP 400)")

    # 2.3 Monthly Summary API
    res_sum = client.get('/api/attendance-records/monthly-summary/')
    assert res_sum.status_code == status.HTTP_200_OK, f"Monthly summary failed: {res_sum.data}"
    assert res_sum.data.get('workingDays') is not None
    assert len(res_sum.data.get('calendar', [])) > 0
    print(f"  -> Monthly Summary API verified: Working days={res_sum.data.get('workingDays')}, Present={res_sum.data.get('presentDays')}")

    print("\n[Test 3] Leave Management: Application, Overlap Validation & Working Days...")
    # Target dates next month to avoid conflicts
    next_month_start = date(2026, 11, 2) # A Monday
    next_month_end = date(2026, 11, 4)   # A Wednesday (3 working days)

    leave_payload = {
        'leaveTypeId': lt_cl.id,
        'fromDate': next_month_start.isoformat(),
        'toDate': next_month_end.isoformat(),
        'reason': 'Family function and travel',
    }
    client.force_authenticate(user=prod_emp)
    res_leave = client.post('/api/leave-requests/', leave_payload)
    assert res_leave.status_code == status.HTTP_201_CREATED, f"Leave creation failed: {res_leave.data}"
    leave_id = res_leave.data['id']
    num_days = float(res_leave.data['number_of_days'])
    assert num_days == 3.0, f"Expected 3 working days, got {num_days}"
    print(f"  -> Leave application created: {leave_id} for {num_days} days. Status=Pending")

    # 3.2 Overlapping Leave Validation
    res_overlap = client.post('/api/leave-requests/', {
        'leaveTypeId': lt_cl.id,
        'fromDate': date(2026, 11, 3).isoformat(),
        'toDate': date(2026, 11, 5).isoformat(),
        'reason': 'Overlapping leave attempt',
    })
    assert res_overlap.status_code == status.HTTP_400_BAD_REQUEST, f"Expected 400 for overlap, got {res_overlap.status_code}"
    assert "overlapping" in str(res_overlap.data).lower() or "already" in str(res_overlap.data).lower()
    print("  -> Overlapping leave application rejected: OK (HTTP 400)")

    # 3.3 Verify balance reservation
    bal_prod.refresh_from_db()
    assert float(bal_prod.pending_approval) == 3.0, f"Expected 3 pending approval, got {bal_prod.pending_approval}"
    assert float(bal_prod.available_balance) == 9.0, f"Expected 9 available balance, got {bal_prod.available_balance}"
    print(f"  -> Balance reservation verified: Available={bal_prod.available_balance}, Pending={bal_prod.pending_approval}")

    print("\n[Test 4] Leave Security: Prevention of Self-Approval & Multi-Stage Approval...")
    # 4.1 Employee tries to self-approve own leave -> MUST RETURN 403
    client.force_authenticate(user=prod_emp)
    res_self_app = client.post(f"/api/leave-requests/{leave_id}/approve/", {})
    assert res_self_app.status_code == status.HTTP_403_FORBIDDEN, f"Expected 403 for self-approval, got {res_self_app.status_code}"
    assert "self-approval" in str(res_self_app.data).lower()
    print("  -> Self-Approval strictly prevented: OK (HTTP 403 Forbidden)")

    # 4.2 Cross-department employee tries to approve -> MUST RETURN 403
    client.force_authenticate(user=des_emp)
    res_cross_app = client.post(f"/api/leave-requests/{leave_id}/approve/", {})
    assert res_cross_app.status_code == status.HTTP_403_FORBIDDEN, f"Expected 403 for cross-department user, got {res_cross_app.status_code}"
    print("  -> Cross-Department unauthorized approval prevented: OK (HTTP 403 Forbidden)")

    # 4.3 Authorized Department Manager approves
    client.force_authenticate(user=prod_mgr)
    res_mgr_app = client.post(f"/api/leave-requests/{leave_id}/approve/", {'remarks': 'Approved by Prod Manager'})
    assert res_mgr_app.status_code == status.HTTP_200_OK, f"Approval failed: {res_mgr_app.data}"
    assert res_mgr_app.data['status'] == 'Approved'
    print("  -> Authorized Department Manager approval: OK (Status=Approved)")

    # Verify balance deduction
    bal_prod.refresh_from_db()
    assert float(bal_prod.used) == 3.0, f"Expected 3 used, got {bal_prod.used}"
    assert float(bal_prod.pending_approval) == 0.0, f"Expected 0 pending, got {bal_prod.pending_approval}"
    assert float(bal_prod.available_balance) == 9.0, f"Expected 9 available balance, got {bal_prod.available_balance}"
    print(f"  -> Balance deduction verified: Used={bal_prod.used}, Available={bal_prod.available_balance}")

    print("\n[Test 5] Task Management: Workflow, Restricted Fields & Progress Transitions...")
    # 5.1 Regular employee without can_assign_tasks cannot create tasks
    client.force_authenticate(user=des_emp)
    res_unauth_task = client.post('/api/project-tasks/', {
        'title': 'Unauthorized Task',
        'assigned_to_id': des_emp.id,
    })
    assert res_unauth_task.status_code == status.HTTP_403_FORBIDDEN, f"Expected 403 for task creation, got {res_unauth_task.status_code}"
    print("  -> Unauthorized task creation blocked: OK (HTTP 403)")

    # 5.2 Department Manager creates task for prod_emp
    client.force_authenticate(user=prod_mgr)
    task_payload = {
        'title': 'Fabricate Reactor Shell Flange Joint',
        'description': 'Fit-up and SAW weld the dish end shell seam',
        'department': 'Production',
        'assigned_to_id': prod_emp.id,
        'assigned_to_name': prod_emp.name or prod_emp.username,
        'priority': 'high',
        'due_date': (date.today() + timedelta(days=5)).isoformat(),
        'estimated_hours': 16.0,
    }
    res_task = client.post('/api/project-tasks/', task_payload)
    assert res_task.status_code == status.HTTP_201_CREATED, f"Task creation failed: {res_task.data}"
    task_id = res_task.data['id']
    assert res_task.data['status'] == 'Assigned'
    print(f"  -> Task created: {task_id} (Status=Assigned)")

    # 5.3 Assignee accepts task: Assigned -> Accepted
    client.force_authenticate(user=prod_emp)
    res_accept = client.post(f"/api/project-tasks/{task_id}/accept/")
    assert res_accept.status_code == status.HTTP_200_OK
    assert res_accept.data['status'] == 'Accepted'
    print("  -> Task accepted: OK (Status=Accepted)")

    # 5.4 Assignee starts task: Accepted -> In Progress
    res_start = client.post(f"/api/project-tasks/{task_id}/start/")
    assert res_start.status_code == status.HTTP_200_OK
    assert res_start.data['status'] == 'In Progress'
    print("  -> Task started: OK (Status=In Progress)")

    # 5.5 Assignee updates progress & actual hours
    res_prog = client.post(f"/api/project-tasks/{task_id}/progress/", {
        'progress_percent': 65,
        'actual_hours': 10.5,
        'checklist': [{'text': 'Fit-up inspection done', 'done': True}],
        'remarks': 'Seam bevelling complete, root pass underway'
    })
    assert res_prog.status_code == status.HTTP_200_OK
    assert res_prog.data['progress_percent'] == 65
    print(f"  -> Task progress updated: 65%, 10.5h")

    # 5.6 Regular assignee cannot modify restricted fields (reassign task or change due date)
    res_tamper = client.patch(f"/api/project-tasks/{task_id}/", {
        'assigned_to_id': des_emp.id,
        'priority': 'low'
    })
    assert res_tamper.status_code == status.HTTP_403_FORBIDDEN, f"Expected 403 for modifying restricted fields, got {res_tamper.status_code}"
    print("  -> Modification of restricted fields blocked for employee: OK (HTTP 403)")

    # 5.7 Submit task for review: In Progress -> Submitted for Review
    res_submit = client.post(f"/api/project-tasks/{task_id}/submit-for-review/", {
        'remarks': 'Welding and intermediate NDT complete. Ready for final inspection.'
    })
    assert res_submit.status_code == status.HTTP_200_OK
    assert res_submit.data['status'] == 'Submitted for Review'
    print("  -> Task submitted for review: OK (Status=Submitted for Review)")

    # 5.8 Employee cannot review their own task -> MUST RETURN 403
    res_self_rev = client.post(f"/api/project-tasks/{task_id}/review/", {'action': 'approve'})
    assert res_self_rev.status_code == status.HTTP_403_FORBIDDEN, f"Expected 403 for self-review, got {res_self_rev.status_code}"
    print("  -> Self-review blocked: OK (HTTP 403)")

    # 5.9 Manager reviews: requests revision first
    client.force_authenticate(user=prod_mgr)
    res_rev = client.post(f"/api/project-tasks/{task_id}/review/", {
        'action': 'request_revision',
        'reviewNotes': 'Check RT film at seam intersection before sign-off.'
    })
    assert res_rev.status_code == status.HTTP_200_OK
    assert res_rev.data['status'] == 'Revision Required'
    print("  -> Manager requested revision: OK (Status=Revision Required)")

    # 5.10 Manager approves and completes task
    res_comp = client.post(f"/api/project-tasks/{task_id}/review/", {
        'action': 'approve',
        'reviewNotes': 'RT film verified clear. Stage cleared.'
    })
    assert res_comp.status_code == status.HTTP_200_OK
    assert res_comp.data['status'] == 'Completed'
    assert res_comp.data['progress_percent'] == 100
    print("  -> Manager approved and completed task: OK (Status=Completed)")

    print("\n[Test 6] Security & Scope Isolation: Cross-Department Data Isolation...")
    # 6.1 Design Employee cannot view Production Employee's tasks or attendance
    client.force_authenticate(user=des_emp)
    res_cross_tasks = client.get(f"/api/project-tasks/?assigned_to_id={prod_emp.id}")
    # Under employee scope, get_queryset strictly limits to user's own tasks
    assert len(res_cross_tasks.data) == 0, f"Scope leak: Design employee saw prod tasks: {res_cross_tasks.data}"
    print("  -> Cross-Department task scoping: OK (0 records leaked)")

    res_cross_att = client.get(f"/api/attendance-records/?employee_id={prod_emp.id}")
    assert len(res_cross_att.data) == 0, f"Scope leak: Design employee saw prod attendance: {res_cross_att.data}"
    print("  -> Cross-Department attendance scoping: OK (0 records leaked)")

    res_cross_dash = client.get(f"/api/hr/employee-dashboard/?employee_id={prod_emp.id}")
    assert res_cross_dash.status_code == status.HTTP_403_FORBIDDEN, f"Expected 403 for cross-emp dashboard, got {res_cross_dash.status_code}"
    print("  -> Cross-Department employee dashboard access blocked: OK (HTTP 403)")

    print("\n[Test 7] Employee Dashboard API Verification...")
    client.force_authenticate(user=prod_emp)
    res_dash = client.get('/api/hr/employee-dashboard/')
    assert res_dash.status_code == status.HTTP_200_OK, f"Dashboard failed: {res_dash.data}"
    dash_data = res_dash.data
    assert dash_data['profile']['id'] == prod_emp.id
    assert dash_data['todayAttendance'] is not None
    assert dash_data['monthlySummary'] is not None
    assert len(dash_data['leaveBalances']) > 0
    assert dash_data['tasksSummary'] is not None
    assert len(dash_data['moduleShortcuts']) > 0
    print(f"  -> Employee Dashboard verified: Name={dash_data['profile']['name']}, Dept={dash_data['profile']['department']}")
    print(f"     Attendance status today: {dash_data['todayAttendance']['status']}")
    print(f"     Leave balances returned: {len(dash_data['leaveBalances'])} types")
    print(f"     Module shortcuts returned: {len(dash_data['moduleShortcuts'])}")

    print("\n" + "=" * 80)
    print("ALL PHASE 3 BACKEND TESTS & SECURITY VERIFICATIONS PASSED WITH 100% SUCCESS!")
    print("=" * 80)


if __name__ == '__main__':
    run_phase3_verification()
