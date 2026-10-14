"""
UMAERP — Automated RBAC, Permissions, and Secure Login/Logout Test Suite
Tests:
1. User creation with Department and Role
2. Permission Matrix configuration and explicit restriction precedence
3. Inactive user authentication denial (403)
4. Invalid credentials authentication denial (401)
5. Valid user authentication and effective permissions payload
6. Server-side logout and token blacklisting
7. Blocked token refresh after logout (401)
8. Scope isolation: cross-department employee access denial (403)
"""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from django.test import RequestFactory
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.authentication.models import User
from apps.organization.models import Department, Role
from apps.core.rbac_permissions import compute_effective_permissions

def run_tests():
    client = APIClient()
    print("=" * 70)
    print("STARTING UMAERP RBAC & AUTHENTICATION TEST SUITE")
    print("=" * 70)

    # Setup test department and role
    sales_dept, _ = Department.objects.get_or_create(
        id='DEPT-TEST-SALES',
        defaults={
            'code': 'DEPT-TEST-SALES',
            'name': 'Test Sales Department',
            'assigned_modules': ['crm'],
            'default_permissions': {'crm': ['view', 'create', 'edit']},
            'status': 'active'
        }
    )

    purchase_dept, _ = Department.objects.get_or_create(
        id='DEPT-TEST-PURCHASE',
        defaults={
            'code': 'DEPT-TEST-PURCHASE',
            'name': 'Test Purchase Department',
            'assigned_modules': ['purchase'],
            'default_permissions': {'purchase': ['view', 'create']},
            'status': 'active'
        }
    )

    sales_role, _ = Role.objects.get_or_create(
        id='ROLE-TEST-SALES-EXEC',
        defaults={
            'name': 'Sales Executive',
            'department_id': sales_dept.id,
            'description': 'Sales Executive role for testing',
            'permissions': ['crm.view', 'crm.create', 'crm.edit']
        }
    )

    # 1. Clean up old test users
    User.objects.filter(username__startswith='test_rbac_').delete()

    # ----------------------------------------------------
    # TEST 1: User Creation with Department & Role
    # ----------------------------------------------------
    print("\n[TEST 1] Creating User, Assigning Department & Role...")
    user = User.objects.create(
        id='EMP-TEST-001',
        username='test_rbac_user1',
        email='test_rbac_user1@umaerp.com',
        first_name='Ramesh',
        last_name='Patel',
        department=sales_dept,
        department_name=sales_dept.name,
        role_profile=sales_role,
        role_name=sales_role.name,
        role_type='employee',
        data_scope='department',
        assigned_modules=['crm'],
        custom_permissions={'crm': ['view', 'create', 'edit']},
        is_active=True,
        status='active'
    )
    user.set_password('TestPass@123')
    user.save()

    assert user.department_id == sales_dept.id, "Department not assigned!"
    assert user.role_profile_id == sales_role.id, "Role not assigned!"
    assert user.is_active is True, "User should be active!"
    print("  [OK] User created: EMP-TEST-001, Dept: Test Sales, Role: Sales Executive")

    # ----------------------------------------------------
    # TEST 2: Effective Permission Calculation & Explicit Restrictions
    # ----------------------------------------------------
    print("\n[TEST 2] Testing Effective Permission Precedence & Explicit Restrictions...")
    perms = compute_effective_permissions(user)
    assert 'crm' in perms['allowed_modules'], "CRM should be allowed!"
    assert 'purchase' not in perms['allowed_modules'], "Purchase should not be allowed!"
    assert perms['actions'].get('crm:create') is True, "crm:create should be True!"

    # Now apply explicit restriction: crm:delete and crm:create
    user.explicit_restrictions = ['crm:create', 'crm:delete']
    user.save()
    perms_restricted = compute_effective_permissions(user)
    assert not perms_restricted['actions'].get('crm:create'), "crm:create must be blocked by explicit restriction!"
    assert 'create' not in perms_restricted['permissions_matrix'].get('crm', []), "create action must not exist in crm matrix!"
    assert perms_restricted['actions'].get('crm:view') is True, "crm:view should still be permitted!"
    print("  [OK] Precedence Verified: Explicit restriction denied crm:create despite role and dept grants.")

    # ----------------------------------------------------
    # TEST 3: Login with Inactive / Deactivated User (Should Return 403)
    # ----------------------------------------------------
    print("\n[TEST 3] Testing Login with Deactivated Account...")
    user.is_active = False
    user.save()
    resp_inactive = client.post('/api/auth/login/', {'username': user.username, 'password': 'TestPass@123'}, format='json')
    assert resp_inactive.status_code == 403, f"Expected 403 Forbidden for inactive account, got {resp_inactive.status_code}"
    print(f"  [OK] Inactive login blocked: HTTP {resp_inactive.status_code} ({resp_inactive.data.get('error')})")

    # Re-activate user
    user.is_active = True
    user.save()

    # ----------------------------------------------------
    # TEST 4: Login with Bad Credentials (Should Return 401)
    # ----------------------------------------------------
    print("\n[TEST 4] Testing Login with Invalid Password...")
    resp_bad = client.post('/api/auth/login/', {'username': user.username, 'password': 'WrongPassword999'}, format='json')
    assert resp_bad.status_code == 401, f"Expected 401 Unauthorized for bad password, got {resp_bad.status_code}"
    print(f"  [OK] Invalid credentials rejected: HTTP {resp_bad.status_code} ({resp_bad.data.get('error')})")

    # ----------------------------------------------------
    # TEST 5: Successful Login & Effective Permissions Payload
    # ----------------------------------------------------
    print("\n[TEST 5] Testing Successful Authentication & JWT Payload...")
    resp_login = client.post('/api/auth/login/', {'username': user.username, 'password': 'TestPass@123'}, format='json')
    assert resp_login.status_code == 200, f"Expected 200 OK, got {resp_login.status_code}: {resp_login.data}"
    login_data = resp_login.data
    assert 'access' in login_data and 'refresh' in login_data, "Access and refresh tokens must be returned!"
    assert 'effective_permissions' in login_data['user'], "Effective permissions must be included in user payload!"
    access_token = login_data['access']
    refresh_token = login_data['refresh']
    print(f"  [OK] Valid login successful: Received JWT access ({access_token[:15]}...) and refresh tokens.")

    # ----------------------------------------------------
    # TEST 6: Secure Logout & Refresh Token Blacklisting
    # ----------------------------------------------------
    print("\n[TEST 6] Testing Secure Logout & Server-Side Token Blacklisting...")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    resp_logout = client.post('/api/auth/logout/', {'refresh': refresh_token}, format='json')
    assert resp_logout.status_code == 200, f"Expected 200 OK for logout, got {resp_logout.status_code}"
    print(f"  [OK] Logout successful: HTTP {resp_logout.status_code} ({resp_logout.data.get('message')})")

    # ----------------------------------------------------
    # TEST 7: Attempting Token Refresh with Blacklisted Token (Should Return 401)
    # ----------------------------------------------------
    print("\n[TEST 7] Testing Token Refresh after Logout (Blacklist Verification)...")
    client.credentials()  # Clear auth header
    resp_refresh = client.post('/api/auth/token/refresh/', {'refresh': refresh_token}, format='json')
    assert resp_refresh.status_code == 401, f"Expected 401 Unauthorized for blacklisted token refresh, got {resp_refresh.status_code}"
    print(f"  [OK] Blacklisted token rejected on refresh: HTTP {resp_refresh.status_code}")

    # ----------------------------------------------------
    # TEST 8: Department Scope Isolation
    # ----------------------------------------------------
    print("\n[TEST 8] Testing Department Scope Isolation...")
    # Create another employee in Purchase department
    user2 = User.objects.create(
        id='EMP-TEST-002',
        username='test_rbac_user2',
        email='test_rbac_user2@umaerp.com',
        first_name='Kishore',
        last_name='Shah',
        department_id=purchase_dept.id,
        department_name=purchase_dept.name,
        role_type='employee',
        data_scope='department',
        is_active=True,
        status='active'
    )
    user2.set_password('TestPass@456')
    user2.save()

    # User 1 (Sales, department scope) tries to fetch User 2 (Purchase)
    login1 = client.post('/api/auth/login/', {'username': user.username, 'password': 'TestPass@123'}, format='json')
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login1.data['access']}")
    resp_user2 = client.get(f"/api/auth/employees/{user2.id}/")
    assert resp_user2.status_code == 403, f"Expected 403 Forbidden for cross-department employee access, got {resp_user2.status_code}"
    print(f"  [OK] Cross-department access strictly rejected: HTTP {resp_user2.status_code}")

    # Clean up test users
    User.objects.filter(username__startswith='test_rbac_').delete()
    print("\n" + "=" * 70)
    print("ALL 8 RBAC & AUTHENTICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == '__main__':
    run_tests()
