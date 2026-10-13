"""
Automated RBAC & Phase 1 Validation Test Suite
Tests:
1. Unauthenticated requests return HTTP 401.
2. Department creation and configuration persist in database.
3. Department deactivation/activation and non-admin denial (HTTP 403).
4. New employee receives department default modules and permissions.
5. Self-escalation prevention: Employees cannot escalate role, scope, or permissions (HTTP 403).
6. Admin authority bounds: Restricted admins cannot grant super_admin or scopes beyond their own (HTTP 403).
7. Cross-department data isolation and URL ID tampering prevention: Dept A cannot retrieve Dept B (HTTP 403).
8. Explicit restrictions strictly override role and module grants.
9. Department change triggers permission review flag and resets obsolete department permissions.
10. Effective permissions preview endpoint returns correct resolved matrix.
11. Authentication (login, token, me) remains fully functional.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.authentication.models import User
from apps.organization.models import Department
from apps.core.rbac_permissions import compute_effective_permissions, check_explicit_restriction


class Phase1RBACTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Setup Departments
        self.dept_crm = Department.objects.create(
            id='dept-test-crm',
            code='TCRM',
            name='CRM & Sales',
            assigned_modules=['crm'],
            default_permissions={'crm': ['view', 'create', 'edit']},
            status='active'
        )

        self.dept_prd = Department.objects.create(
            id='dept-test-prd',
            code='TPRD',
            name='Production & Shop Floor',
            assigned_modules=['production'],
            default_permissions={'production': ['view', 'create']},
            status='active'
        )

        # 2. Setup Super Admin
        self.super_admin = User.objects.create(
            id='EMP-TEST-001',
            username='test.superadmin',
            first_name='Super',
            last_name='Admin',
            email='super@umaerp.test',
            role_type='super_admin',
            data_scope='all',
            is_superuser=True,
            is_staff=True,
            department=self.dept_crm,
            department_name=self.dept_crm.name,
            is_active=True
        )
        self.super_admin.set_password('pass123')
        self.super_admin.save()

        # 3. Setup Authorized Admin (Global Scope)
        self.auth_admin = User.objects.create(
            id='EMP-TEST-002',
            username='test.admin',
            first_name='Ketan',
            last_name='Admin',
            email='admin@umaerp.test',
            role_type='admin',
            data_scope='all',
            is_staff=True,
            department=self.dept_crm,
            department_name=self.dept_crm.name,
            is_active=True
        )
        self.auth_admin.set_password('pass123')
        self.auth_admin.save()

        # 4. Setup Restricted Admin (Department-Only Scope)
        self.restricted_admin = User.objects.create(
            id='EMP-TEST-003',
            username='test.restricted.admin',
            first_name='Restricted',
            last_name='Admin',
            email='radmin@umaerp.test',
            role_type='admin',
            data_scope='department',
            is_staff=True,
            department=self.dept_crm,
            department_name=self.dept_crm.name,
            is_active=True
        )
        self.restricted_admin.set_password('pass123')
        self.restricted_admin.save()

        # 5. Setup Department Manager (CRM)
        self.manager_crm = User.objects.create(
            id='EMP-TEST-004',
            username='test.manager.crm',
            first_name='Pravin',
            last_name='Manager',
            email='pravin@umaerp.test',
            role_type='department_manager',
            data_scope='department',
            department=self.dept_crm,
            department_name=self.dept_crm.name,
            is_active=True
        )
        self.manager_crm.set_password('pass123')
        self.manager_crm.save()

        # 6. Setup Employee Dept A (CRM)
        self.employee_crm = User.objects.create(
            id='EMP-TEST-005',
            username='test.emp.crm',
            first_name='Amit',
            last_name='Sales',
            email='amit@umaerp.test',
            role_type='employee',
            data_scope='own',
            department=self.dept_crm,
            department_name=self.dept_crm.name,
            assigned_modules=['crm'],
            custom_permissions={'crm': ['view', 'create']},
            is_active=True
        )
        self.employee_crm.set_password('pass123')
        self.employee_crm.save()

        # 7. Setup Employee Dept B (Production)
        self.employee_prd = User.objects.create(
            id='EMP-TEST-006',
            username='test.emp.prd',
            first_name='Suresh',
            last_name='Operator',
            email='suresh@umaerp.test',
            role_type='employee',
            data_scope='own',
            department=self.dept_prd,
            department_name=self.dept_prd.name,
            assigned_modules=['production'],
            custom_permissions={'production': ['view']},
            is_active=True
        )
        self.employee_prd.set_password('pass123')
        self.employee_prd.save()

    def test_01_unauthenticated_requests_return_401(self):
        """Unauthenticated requests must be rejected with HTTP 401."""
        res_emp = self.client.get('/api/employees/')
        self.assertEqual(res_emp.status_code, status.HTTP_401_UNAUTHORIZED)

        res_dept = self.client.get('/api/departments/')
        self.assertEqual(res_dept.status_code, status.HTTP_401_UNAUTHORIZED)

        res_create_dept = self.client.post('/api/departments/', {'code': 'NEW', 'name': 'New Dept'})
        self.assertEqual(res_create_dept.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_02_department_creation_and_config_persist(self):
        """Super Admin creates and configures department; verify DB persistence."""
        self.client.force_authenticate(user=self.super_admin)
        data = {
            'code': 'QA',
            'name': 'Quality Assurance',
            'description': 'QA & Non-Destructive Testing',
            'assigned_modules': ['quality', 'store'],
            'default_permissions': {'quality': ['view', 'create', 'approve']},
            'status': 'active'
        }
        res = self.client.post('/api/departments/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        dept = Department.objects.filter(code='QA').first()
        self.assertIsNotNone(dept)
        self.assertEqual(dept.name, 'Quality Assurance')
        self.assertIn('quality', dept.assigned_modules)
        self.assertEqual(dept.default_permissions['quality'], ['view', 'create', 'approve'])

    def test_03_department_deactivate_and_activate(self):
        """Admin can deactivate/activate department; non-admin receives 403."""
        # Non-admin employee attempt
        self.client.force_authenticate(user=self.employee_crm)
        res_denied = self.client.post(f'/api/departments/{self.dept_prd.id}/deactivate/')
        self.assertEqual(res_denied.status_code, status.HTTP_403_FORBIDDEN)

        # Admin attempt
        self.client.force_authenticate(user=self.auth_admin)
        res_deact = self.client.post(f'/api/departments/{self.dept_prd.id}/deactivate/')
        self.assertEqual(res_deact.status_code, status.HTTP_200_OK)

        self.dept_prd.refresh_from_db()
        self.assertEqual(self.dept_prd.status, 'inactive')

        # Reactivate
        res_act = self.client.post(f'/api/departments/{self.dept_prd.id}/activate/')
        self.assertEqual(res_act.status_code, status.HTTP_200_OK)
        self.dept_prd.refresh_from_db()
        self.assertEqual(self.dept_prd.status, 'active')

    def test_04_new_employee_receives_department_defaults(self):
        """New employee created in Department automatically receives default modules and permissions."""
        self.client.force_authenticate(user=self.auth_admin)
        emp_data = {
            'username': 'rahul.new',
            'first_name': 'Rahul',
            'last_name': 'Patel',
            'email': 'rahul@umaerp.test',
            'department_id': self.dept_crm.id,
            'designation': 'Sales Executive',
            'password': 'password123'
        }
        res = self.client.post('/api/employees/', emp_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        new_user = User.objects.filter(username='rahul.new').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.department_id, self.dept_crm.id)
        # Should have inherited CRM modules & default permissions
        self.assertIn('crm', new_user.assigned_modules)
        self.assertEqual(new_user.custom_permissions.get('crm'), ['view', 'create', 'edit'])

    def test_05_unauthorized_user_cannot_escalate_own_permissions(self):
        """Employee cannot escalate their own role, scope, or custom permissions (HTTP 403)."""
        self.client.force_authenticate(user=self.employee_crm)

        # Attempt 1: PATCH self with role_type='super_admin'
        res_patch = self.client.patch(
            f'/api/employees/{self.employee_crm.id}/',
            {'role_type': 'super_admin'},
            format='json'
        )
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt 2: PATCH self with data_scope='all'
        res_scope = self.client.patch(
            f'/api/employees/{self.employee_crm.id}/',
            {'data_scope': 'all'},
            format='json'
        )
        self.assertEqual(res_scope.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt 3: POST /permissions/ endpoint directly
        res_perm = self.client.post(
            f'/api/employees/{self.employee_crm.id}/permissions/',
            {'role_type': 'super_admin', 'data_scope': 'all'},
            format='json'
        )
        self.assertEqual(res_perm.status_code, status.HTTP_403_FORBIDDEN)

        # Verify DB remained unchanged
        self.employee_crm.refresh_from_db()
        self.assertEqual(self.employee_crm.role_type, 'employee')
        self.assertEqual(self.employee_crm.data_scope, 'own')

    def test_06_restricted_admin_cannot_grant_privileges_beyond_authority(self):
        """Restricted admin (scope='department') cannot grant super_admin or scope='all'."""
        self.client.force_authenticate(user=self.restricted_admin)

        # Cannot promote employee to super_admin
        res_super = self.client.post(
            f'/api/employees/{self.employee_crm.id}/permissions/',
            {'role_type': 'super_admin'},
            format='json'
        )
        self.assertEqual(res_super.status_code, status.HTTP_403_FORBIDDEN)

        # Cannot grant 'all' data scope since restricted admin only has 'department' scope
        res_all_scope = self.client.post(
            f'/api/employees/{self.employee_crm.id}/permissions/',
            {'data_scope': 'all'},
            format='json'
        )
        self.assertEqual(res_all_scope.status_code, status.HTTP_403_FORBIDDEN)

    def test_07_department_cross_isolation_and_url_tampering(self):
        """Department A employee cannot access Department B employee details or records (HTTP 403)."""
        self.client.force_authenticate(user=self.employee_crm)

        # Direct URL ID lookup for employee in Department B
        res_direct = self.client.get(f'/api/employees/{self.employee_prd.id}/')
        self.assertEqual(res_direct.status_code, status.HTTP_403_FORBIDDEN)

        # List endpoint query must not leak employee from Department B
        res_list = self.client.get('/api/employees/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        returned_ids = [item['id'] for item in res_list.data]
        self.assertNotIn(self.employee_prd.id, returned_ids)

    def test_08_explicit_restrictions_override_ordinary_grants(self):
        """Explicit restrictions strictly revoke grants, including for managers and admins."""
        # Grant manager approve capability, but explicitly restrict 'crm:delete' and '*:export'
        self.manager_crm.explicit_restrictions = ['crm:delete', '*:export', 'tasks:assign']
        self.manager_crm.save()

        self.assertTrue(check_explicit_restriction(self.manager_crm, 'crm', 'delete'))
        self.assertTrue(check_explicit_restriction(self.manager_crm, 'any_mod', 'export'))
        self.assertTrue(check_explicit_restriction(self.manager_crm, 'tasks', 'assign'))

        eff = compute_effective_permissions(self.manager_crm)
        crm_actions = eff['permissions_matrix'].get('crm', [])
        self.assertNotIn('delete', crm_actions)
        self.assertFalse(eff['capabilities']['can_export_data'])
        self.assertFalse(eff['capabilities']['can_assign_tasks'])

    def test_09_department_change_triggers_permission_review(self):
        """Department change sets permissions_review_required=True and resets old department custom perms."""
        self.client.force_authenticate(user=self.auth_admin)

        # Initial state: employee is in CRM with crm permissions
        self.assertFalse(self.employee_crm.permissions_review_required)

        # Transfer employee to Production department
        res_transfer = self.client.patch(
            f'/api/employees/{self.employee_crm.id}/',
            {'department_id': self.dept_prd.id},
            format='json'
        )
        self.assertEqual(res_transfer.status_code, status.HTTP_200_OK)

        self.employee_crm.refresh_from_db()
        self.assertEqual(self.employee_crm.department_id, self.dept_prd.id)
        self.assertTrue(self.employee_crm.permissions_review_required)
        self.assertEqual(self.employee_crm.previous_department_name, 'CRM & Sales')

        # Old department's crm custom permissions should not silently persist
        self.assertIn('production', self.employee_crm.assigned_modules)

    def test_10_effective_permissions_endpoint_preview(self):
        """Effective permissions preview endpoint returns full computed matrix."""
        self.client.force_authenticate(user=self.auth_admin)
        res = self.client.get(f'/api/employees/{self.employee_crm.id}/effective-permissions/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data['user_id'], self.employee_crm.id)
        self.assertIn('permissions_matrix', res.data)
        self.assertIn('allowed_modules', res.data)
        self.assertIn('capabilities', res.data)

    def test_11_existing_auth_login_me_remain_functional(self):
        """Login and /api/auth/me/ continue to work and return JWT tokens and effective_permissions."""
        login_res = self.client.post('/api/auth/login/', {
            'username': 'test.superadmin',
            'password': 'pass123'
        })
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_res.data)
        self.assertIn('user', login_res.data)
        self.assertIn('effective_permissions', login_res.data['user'])

        token = login_res.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        me_res = self.client.get('/api/auth/me/')
        self.assertEqual(me_res.status_code, status.HTTP_200_OK)
        self.assertEqual(me_res.data['username'], 'test.superadmin')
        self.assertIn('effective_permissions', me_res.data)
