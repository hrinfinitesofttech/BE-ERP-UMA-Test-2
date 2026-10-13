# UmaERP — Phase 1: Implementation & Validation Report

**Date:** 2026-10-13  
**Phase:** Phase 1: Backend Audit, Database Schema & Secure RBAC Foundation  
**System:** UmaERP — Department-Wise Employee Management  
**Status:** **PASSED (100% Verified)**  
**Local Test Suite Results:** 11 / 11 automated RBAC unit tests passed; 18 / 18 lifecycle ERP tests passed.  
**Database Backup:** `d:\UMA ERP\BE-ERP-UMA\db.sqlite3.backup_phase1_audit` (1,961,984 bytes).  

---

## 1. Executive Summary

Phase 1 establishes the rock-solid, production-grade security and data layer for UmaERP's Department-Wise Employee Management. Prior to writing any code, a complete backend, database, and API audit was conducted and documented in `UMAERP_PHASE1_BACKEND_AUDIT.md`.

All requirements of Phase 1 have been implemented and verified:
1. Reused existing `Department` and custom `User` models without creating duplicate tables or duplicate authentication systems.
2. Created only verified database migrations without touching existing client data or resetting `db.sqlite3`.
3. Created a centralized server-side RBAC engine (`apps/core/rbac_permissions.py`) supporting:
   - Actions: `view`, `create`, `edit`, `delete`, `approve`, `assign`, `update_status`, `export`, `print`, `manage_settings`.
   - Scopes: `own`, `assigned`, `department`, `all`.
   - Explicit restrictions overriding all role and department grants.
   - Self-escalation prevention for employees and non-super-admins.
   - Admin authority boundaries (admins cannot grant privileges beyond their own scope).
   - Cross-department record isolation with HTTP 403 on tampering and HTTP 401 on unauthenticated calls.
4. Delivered all required endpoints: Department CRUD/deactivate/activate/configure-modules; Employee CRUD/deactivate/activate/permissions/effective-permissions.
5. All 11 automated test cases in `apps.authentication.tests_phase1_rbac` passed cleanly.
6. All 18 existing end-to-end ERP lifecycle phases in `test_lifecycle_crud.py` passed with zero regression.

---

## 2. Files Changed & Added

| File | Change Type | Purpose |
|---|---|---|
| `UMAERP_PHASE1_BACKEND_AUDIT.md` | Created | Comprehensive pre-coding audit of models, APIs, migrations, and gaps. |
| `apps/core/rbac_permissions.py` | Created | Centralized RBAC engine: permission classes, explicit restriction evaluator, compute_effective_permissions, and queryset scoping helpers. |
| `apps/authentication/models.py` | Modified | Added `explicit_restrictions`, `permissions_review_required`, `previous_department_name`, and department change detection in `User.save()`. |
| `apps/authentication/migrations/0004_user_explicit_restrictions_and_more.py` | Created | Database migration adding the 3 new fields to `authentication_user`. |
| `apps/authentication/serializers.py` | Modified | Added new fields and camelCase mappings (`explicitRestrictions`, `permissionsReviewRequired`, `isActive`) to `UserSerializer`. |
| `apps/authentication/views.py` | Modified | Enhanced `EmployeeViewSet` and `CurrentUserView` with strict RBAC, scope filtering, self-escalation blocks, and `effective_permissions`, `deactivate`, `activate` endpoints. |
| `apps/organization/views.py` | Modified | Enhanced `DepartmentViewSet` with RBAC permissions and added `deactivate`, `activate`, and `configure_modules` actions. |
| `apps/authentication/tests_phase1_rbac.py` | Created | 11 comprehensive automated tests verifying all security rules, scope isolation, and permissions. |
| `UMAERP_PHASE1_IMPLEMENTATION_REPORT.md` | Created | Phase 1 completion and evidence report. |

---

## 3. Models & Fields Added or Reused

### 3.1 `Department` Model (`apps/organization/models.py`)
- **Status:** **Reused 100% of existing table.** Zero duplicate models created.
- **Existing Fields Verified:** `id`, `code`, `name`, `manager_id`, `manager_name`, `description`, `parent_department_id`, `assigned_modules`, `default_permissions`, `status`, `employee_count`, `created_by`, `created_at`, `updated_at`.
- **Active Record Count:** 13 departments active in database.

### 3.2 `User` Model (`apps/authentication/models.py`)
- **Status:** **Reused existing unified User model.** Serves as authenticated user account, employee profile, and RBAC subject.
- **Existing Fields Reused:** `id` (Employee ID), `username`, `email`, `department`, `department_name`, `designation`, `role_type`, `data_scope`, `assigned_modules`, `custom_permissions`, `can_assign_tasks`, `can_approve_leaves`, `can_manage_attendance`, `can_export_data`, `force_password_change`, `work_location`, `emergency_contact`, `status`.
- **New Fields Added via Migration `0004`:**
  - `explicit_restrictions`: `JSONField(default=list, blank=True)` — List of explicitly blocked actions/modules (e.g., `["crm:delete", "*:export"]`).
  - `permissions_review_required`: `BooleanField(default=False)` — Automatically set to `True` whenever an employee's department is changed.
  - `previous_department_name`: `CharField(max_length=100, blank=True, default='')` — Stores previous department name for audit tracking.
- **Department Transition Logic in `save()`:**
  - Detects if `department_id` has changed on an existing employee.
  - Sets `permissions_review_required = True`.
  - Records `previous_department_name`.
  - Clears obsolete department-specific custom permissions and re-seeds with the new department's defaults, preventing unauthorized retention of old department rights.

---

## 4. Migrations Created & Execution Status

- **Migration File:** `apps/authentication/migrations/0004_user_explicit_restrictions_and_more.py`
- **Execution Log:**
  ```text
  Operations to perform:
    Apply all migrations: authentication
  Running migrations:
    Applying authentication.0004_user_explicit_restrictions_and_more... OK
  ```
- **Execution Status:** Successfully applied.
- **Data Safety:** `db.sqlite3` was fully preserved. Zero rows deleted. All 6 existing user accounts remain intact and active.

---

## 5. APIs Added or Modified

| Endpoint | Method | Permission | Description |
|---|---|---|---|
| `/api/departments/` | GET | IsAuthenticated | Lists active departments with assigned modules and default permissions. |
| `/api/departments/` | POST | IsAdminOrSuperAdmin | Creates new department with database persistence. |
| `/api/departments/{id}/` | GET | IsAuthenticated | Retrieves department details. |
| `/api/departments/{id}/` | PATCH | IsAdminOrSuperAdmin | Updates department details. |
| `/api/departments/{id}/deactivate/` | POST | IsAdminOrSuperAdmin | Deactivates department (`status = 'inactive'`). |
| `/api/departments/{id}/activate/` | POST | IsAdminOrSuperAdmin | Activates department (`status = 'active'`). |
| `/api/departments/{id}/configure-modules/` | GET, PATCH, POST | IsAdminOrSuperAdmin | Configures department's `assigned_modules` and `default_permissions`. |
| `/api/employees/` | GET | IsAuthenticated (Scoped) | Returns employees filtered strictly by user's `data_scope` and department. |
| `/api/employees/` | POST | IsAdminOrSuperAdmin | Creates employee with auto-seeded department default permissions. |
| `/api/employees/{id}/` | GET | IsAuthenticated (Scoped) | Retrieves employee profile. Returns HTTP 403 if target is outside user's scope. |
| `/api/employees/{id}/` | PATCH | IsAuthenticated (Scoped) | Updates employee. Blocks self-escalation and privilege overreach. |
| `/api/employees/{id}/permissions/` | GET | IsAuthenticated (Scoped) | Retrieves employee's permissions and effective permissions preview. |
| `/api/employees/{id}/permissions/` | POST, PATCH | IsAdminOrSuperAdmin | Modifies employee permissions. Enforces admin bounds and blocks self-escalation. |
| `/api/employees/{id}/effective-permissions/` | GET | IsAuthenticated (Scoped) | Returns calculated effective permissions matrix. |
| `/api/employees/{id}/deactivate/` | POST | IsAdminOrSuperAdmin | Deactivates employee account (`is_active=False`, `status='inactive'`). |
| `/api/employees/{id}/activate/` | POST | IsAdminOrSuperAdmin | Activates employee account (`is_active=True`, `status='active'`). |
| `/api/employees/{id}/reset-password/` | POST | IsAdminOrSuperAdmin / Self | Resets employee password and sets `force_password_change=True`. |
| `/api/auth/login/` | POST | AllowAny | Authenticates user and returns JWT tokens + user profile + `effective_permissions`. |
| `/api/auth/me/` | GET | IsAuthenticated | Returns current user profile with calculated `effective_permissions`. |

---

## 6. Permission Rules Implemented

1. **Deny by Default:**
   - Unauthenticated requests to protected endpoints return `HTTP 401 Unauthorized`.
   - Access to modules not granted by department or custom permissions returns `HTTP 403 Forbidden`.
2. **Explicit Super Admin Determination:**
   - Determined strictly via `user.is_superuser` or `user.role_type == 'super_admin'`.
3. **Admin Authority Bounds:**
   - Admins cannot create or promote anyone to `super_admin`.
   - Admins cannot grant `data_scope = 'all'` unless they possess `data_scope = 'all'`.
   - Admins cannot grant modules outside their own authorized scope.
4. **Self-Escalation Prevention:**
   - Non-super-admins attempting to change their own `role_type`, `data_scope`, `custom_permissions`, `assigned_modules`, or `explicit_restrictions` via `PATCH /api/employees/{id}/` or `POST /api/employees/{id}/permissions/` are blocked with `HTTP 403 Forbidden`.
5. **Explicit Restrictions Precedence:**
   - Evaluated before ordinary grants. If an action or module is matched in `explicit_restrictions` (e.g. `crm:delete`, `*:export`), the grant is revoked, even for managers and admins.
6. **Cross-Department Isolation:**
   - Users with `data_scope = 'department'` or `data_scope = 'own'` cannot access records or employee details belonging to other departments. Changing IDs in URL endpoints returns `HTTP 403 Forbidden`.
7. **Foreign Key Integrity:**
   - Endpoints validate `department_id`, `reporting_manager_id`, and `role_id` against database records, rejecting invalid references with `HTTP 400 Bad Request`.

---

## 7. Automated Test Results with Evidence

### Test Suite Execution:
```bash
python manage.py test apps.authentication.tests_phase1_rbac
```

### Raw Output:
```text
Found 11 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
...........
----------------------------------------------------------------------
Ran 11 tests in 39.451s

OK
Destroying test database for alias 'default'...
```

### Detailed Breakdown of Tests:
| Test ID | Test Name | Scenarios Verified | Result |
|---|---|---|---|
| `test_01` | `test_01_unauthenticated_requests_return_401` | Unauthenticated calls to `/api/employees/` and `/api/departments/` return HTTP 401. | **PASSED** |
| `test_02` | `test_02_department_creation_and_config_persist` | Super admin creates department with assigned modules and default permissions; verified persistence in DB. | **PASSED** |
| `test_03` | `test_03_department_deactivate_and_activate` | Admin deactivates/activates department; non-admin employee receives HTTP 403. | **PASSED** |
| `test_04` | `test_04_new_employee_receives_department_defaults` | New employee created in Dept A receives Dept A's default modules and permissions. | **PASSED** |
| `test_05` | `test_05_unauthorized_user_cannot_escalate_own_permissions` | Employee attempts to promote self to super_admin or expand scope to 'all'; returns HTTP 403. | **PASSED** |
| `test_06` | `test_06_restricted_admin_cannot_grant_privileges_beyond_authority` | Restricted admin (scope='department') attempts to assign super_admin or scope='all'; returns HTTP 403. | **PASSED** |
| `test_07` | `test_07_department_cross_isolation_and_url_tampering` | Dept A employee tries to access Dept B employee record by ID; returns HTTP 403; list query excludes Dept B. | **PASSED** |
| `test_08` | `test_08_explicit_restrictions_override_ordinary_grants` | Manager with explicit restriction on `crm:delete` and `*:export` has those rights revoked in effective matrix. | **PASSED** |
| `test_09` | `test_09_department_change_triggers_permission_review` | Changing department triggers `permissions_review_required=True` and resets old department custom perms. | **PASSED** |
| `test_10` | `test_10_effective_permissions_endpoint_preview` | `/api/employees/{id}/effective-permissions/` returns calculated permissions matrix matching role and department. | **PASSED** |
| `test_11` | `test_11_existing_auth_login_me_remain_functional` | Login returns JWT tokens and `effective_permissions`; `/api/auth/me/` returns user profile. | **PASSED** |

### Complete ERP Regression Suite:
```bash
python test_lifecycle_crud.py
```
**Result:** `SUCCESS: ALL 18 PHASES VERIFIED AND SAVED DIRECTLY IN SQLITE DATABASE!` (Lead, Quotation, Sales Order, Project, Design, BOM, MRP, Purchase, GRN, Issue, Production, QC, Dispatch, Invoice, Payment, Commissioning).

---

## 8. Existing Failures & Unresolved Risks

- **Failures:** 0. All 11 unit tests and all 18 ERP lifecycle stages passed.
- **Risks & Mitigations:**
  - *Risk:* In legacy frontend pages, unauthenticated requests might not pass the `Authorization: Bearer <token>` header, leading to HTTP 401.
  - *Mitigation:* `apiClient.ts` in Next.js frontend already automatically attaches stored Bearer tokens to all requests. Login endpoint returns access tokens that are stored in local storage and cookies.
  - *Risk:* Live database schema sync on PythonAnywhere.
  - *Mitigation:* Migration `0004` will be applied via `run_remote_migrate.py` or `deploy_backend_sync.py` after database backup.

---

## 9. Deployment Instructions & Rollback Procedure

### Deployment to PythonAnywhere (Production):
1. **Remote Database Backup:**
   Create a timestamped backup of `/home/erpuma/BE-ERP-UMA/db.sqlite3` on PythonAnywhere before applying changes.
2. **Push Code to GitHub:**
   ```bash
   git add apps/core/rbac_permissions.py apps/authentication/ apps/organization/ UMAERP_PHASE1_BACKEND_AUDIT.md UMAERP_PHASE1_IMPLEMENTATION_REPORT.md
   git commit -m "feat(phase1): Backend Audit, Database Schema & Secure RBAC Foundation"
   git push origin main
   ```
3. **Synchronize & Migrate on PythonAnywhere:**
   ```bash
   python deploy_backend_sync.py
   python run_remote_migrate.py
   ```
4. **Verify Health & Endpoints:**
   Send authenticated GET to `https://erpuma.pythonanywhere.com/api/employees/` and `https://erpuma.pythonanywhere.com/api/departments/`.

### Rollback Procedure:
If any unforeseen issue arises in production:
1. Restore database from backup: `cp db.sqlite3.backup_phase1_audit db.sqlite3`.
2. Rollback git commit: `git revert HEAD --no-edit && git push origin main`.
3. Reload WSGI application on PythonAnywhere.
