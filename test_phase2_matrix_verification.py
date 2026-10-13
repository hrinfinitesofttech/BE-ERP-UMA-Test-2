import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from django.test import Client
from rest_framework import status
from apps.authentication.models import User
from apps.organization.models import Department
from apps.core.rbac_permissions import compute_effective_permissions, check_explicit_restriction

def run_phase2_verification():
    print("=" * 80)
    print("RUNNING UMAERP PHASE 2 - EMPLOYEE MANAGEMENT & PERMISSION MATRIX VERIFICATION")
    print("=" * 80)

    # 1. Setup / Retrieve Departments
    dept_crm = Department.objects.filter(code='CRM').first()
    if not dept_crm:
        dept_crm = Department.objects.create(
            id='dept-crm-test',
            code='CRM-P2',
            name='CRM & Sales',
            assigned_modules=['crm'],
            default_permissions={'crm': ['view', 'create', 'edit']},
            status='active'
        )

    dept_prod = Department.objects.filter(code='PROD').first() or Department.objects.filter(name__icontains='Production').first()
    if not dept_prod:
        dept_prod = Department.objects.create(
            id='dept-prod-test',
            code='PROD-P2',
            name='Production',
            assigned_modules=['production'],
            default_permissions={'production': ['view', 'create']},
            status='active'
        )

    # 2. Setup Super Admin
    super_admin, _ = User.objects.get_or_create(
        id='EMP-TEST-SA',
        defaults={
            'username': 'test.super_admin',
            'first_name': 'Super',
            'last_name': 'Admin',
            'email': 'sa@umaerp.test',
            'role_type': 'super_admin',
            'data_scope': 'all',
            'is_superuser': True,
            'is_staff': True,
            'department': dept_crm,
            'is_active': True,
        }
    )
    super_admin.set_password('pass123')
    super_admin.save()

    # 3. Setup Department A Employee
    emp_crm, _ = User.objects.get_or_create(
        id='EMP-TEST-A',
        defaults={
            'username': 'emp.crm',
            'first_name': 'Ramesh',
            'last_name': 'CRM',
            'email': 'ramesh@umaerp.test',
            'role_type': 'employee',
            'data_scope': 'own',
            'department': dept_crm,
            'department_name': dept_crm.name,
            'assigned_modules': ['crm'],
            'custom_permissions': {'crm': ['view', 'create']},
            'is_active': True,
        }
    )
    emp_crm.department = dept_crm
    emp_crm.department_name = dept_crm.name
    emp_crm.permissions_review_required = False
    emp_crm.previous_department_name = ''
    emp_crm.set_password('pass123')
    emp_crm.save()

    # 4. Setup Department B Employee
    emp_prod, _ = User.objects.get_or_create(
        id='EMP-TEST-B',
        defaults={
            'username': 'suresh.prod',
            'first_name': 'Suresh',
            'last_name': 'Production',
            'email': 'suresh@umaerp.test',
            'role_type': 'employee',
            'data_scope': 'own',
            'department': dept_prod,
            'department_name': dept_prod.name,
            'assigned_modules': ['production'],
            'custom_permissions': {'production': ['view', 'create']},
            'is_active': True,
        }
    )
    emp_prod.set_password('pass123')
    emp_prod.save()

    client = Client()

    # Test 1: Deactivate and Activate Employee Account
    print("\n[Test 1] Employee Account Deactivation & Reactivation...")
    client.force_login(super_admin)
    deact_res = client.post(f'/api/employees/{emp_crm.id}/deactivate/')
    assert deact_res.status_code == status.HTTP_200_OK, f"Deactivation failed: {deact_res.status_code}"
    emp_crm.refresh_from_db()
    assert not emp_crm.is_active, "Employee is_active was not set to False"
    print("  -> Deactivate: OK (is_active=False persisted in DB)")

    act_res = client.post(f'/api/employees/{emp_crm.id}/activate/')
    assert act_res.status_code == status.HTTP_200_OK, f"Reactivation failed: {act_res.status_code}"
    emp_crm.refresh_from_db()
    assert emp_crm.is_active, "Employee is_active was not set to True"
    print("  -> Reactivate: OK (is_active=True persisted in DB)")

    # Test 2: Department Transfer & Review Required Trigger
    print("\n[Test 2] Department Transfer & permissions_review_required flag...")
    emp_crm.department = dept_prod
    emp_crm.department_name = dept_prod.name
    emp_crm.save()
    emp_crm.refresh_from_db()
    assert emp_crm.permissions_review_required, "permissions_review_required flag was not set on dept change"
    assert emp_crm.previous_department_name == dept_crm.name, f"previous_department_name mismatch: {emp_crm.previous_department_name}"
    print("  -> Department Transfer: OK (permissions_review_required=True, previous_department_name recorded)")

    # Test 3: Self-Escalation Block
    print("\n[Test 3] Self-Escalation Prevention (Employee cannot change role/scope)...")
    client.force_login(emp_crm)
    esc_res = client.post(f'/api/employees/{emp_crm.id}/permissions/', data={
        'role_type': 'super_admin',
        'data_scope': 'all',
    }, content_type='application/json')
    assert esc_res.status_code == status.HTTP_403_FORBIDDEN, f"Expected 403 on self escalation, got {esc_res.status_code}"
    print("  -> Self-Escalation Block: OK (HTTP 403 Forbidden)")

    # Test 4: Explicit Restriction Override
    print("\n[Test 4] Explicit Restriction Strict Override Engine...")
    emp_crm.explicit_restrictions = ['crm:delete', '*:export']
    emp_crm.save()
    emp_crm.refresh_from_db()

    is_restr = check_explicit_restriction(emp_crm, 'crm', 'delete')
    assert is_restr, "crm:delete should be blocked by explicit restriction"
    is_restr_export = check_explicit_restriction(emp_crm, 'store', 'export')
    assert is_restr_export, "*:export should be blocked across all modules"
    is_restr_view = check_explicit_restriction(emp_crm, 'crm', 'view')
    assert not is_restr_view, "crm:view should NOT be blocked"
    print("  -> Explicit Restrictions: OK (strict override logic verified)")

    # Test 5: Effective Permissions Preview API
    print("\n[Test 5] Effective Permissions Preview API Endpoint...")
    client.force_login(super_admin)
    eff_res = client.get(f'/api/employees/{emp_prod.id}/effective-permissions/')
    assert eff_res.status_code == status.HTTP_200_OK, f"Effective permissions endpoint failed: {eff_res.status_code}"
    eff_data = eff_res.json()
    assert 'allowed_modules' in eff_data, "Missing allowed_modules key in effective permissions"
    assert 'permissions_matrix' in eff_data, "Missing permissions_matrix key in effective permissions"
    print(f"  -> Effective Permissions API: OK (Allowed modules: {eff_data['allowed_modules']})")

    # Test 6: Cross-Department Isolation
    print("\n[Test 6] Cross-Department Isolation (Dept B employee cannot view Dept A employee profile)...")
    client.force_login(emp_prod)
    cross_res = client.get(f'/api/employees/{emp_crm.id}/')
    # Since emp_crm was transferred to dept_prod, let's test isolation against a distinct department user
    dept_hr = Department.objects.filter(code='HR').first() or Department.objects.filter(name__icontains='HR').first()
    if not dept_hr:
        dept_hr = Department.objects.create(id='dept-hr-test', name='HR', code='HR-P2')
    emp_hr, _ = User.objects.get_or_create(
        id='EMP-TEST-HR',
        defaults={
            'username': 'priya.hr',
            'department': dept_hr,
            'department_name': dept_hr.name,
            'role_type': 'employee',
            'data_scope': 'own',
            'is_active': True,
        }
    )
    emp_hr.set_password('pass123')
    emp_hr.save()

    client.force_login(emp_prod)
    cross_res = client.get(f'/api/employees/{emp_hr.id}/')
    assert cross_res.status_code == status.HTTP_403_FORBIDDEN, f"Expected 403 on cross-dept access, got {cross_res.status_code}"
    print("  -> Cross-Department Isolation: OK (HTTP 403 Forbidden)")

    print("\n" + "=" * 80)
    print("ALL PHASE 2 PERMISSION & SECURITY CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 80)

if __name__ == '__main__':
    run_phase2_verification()
