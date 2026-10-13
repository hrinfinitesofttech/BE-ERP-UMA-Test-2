# UmaERP — Phase 1: Backend Audit, Database Schema & Secure RBAC Foundation

**Date:** 2026-10-13  
**Project:** UmaERP (Custom Heavy Fabrication & Make-to-Order Equipment Manufacturing ERP)  
**Repositories:**
- Backend: `D:\UMA ERP\BE-ERP-UMA` (Django 5.x / Django REST Framework)
- Frontend: `D:\UMA ERP\ERP-Test-1` (Next.js 14 / TypeScript)

---

## 1. Executive Summary

This audit establishes the baseline for **Phase 1: Backend Audit, Database Schema & Secure RBAC Foundation** of the Department-Wise Employee Management system for UmaERP.

All existing code, database structures, models, serializers, views, and routes have been audited. No live client data was deleted or altered. A complete local backup of the active database was created at:
`d:\UMA ERP\BE-ERP-UMA\db.sqlite3.backup_phase1_audit` (1,961,984 bytes).

### Key Architectural Baseline Findings:
1. **Unified User & Employee Model:** The backend already uses a unified custom user model `apps.authentication.models.User(AbstractUser)` where primary keys represent Employee IDs (e.g., `EMP-001`, `EMP-002`, `USR-...`). There is **no duplicate Employee table**, which aligns with best practices.
2. **Existing Department Model:** `apps.organization.models.Department` already exists with 13 active departments, containing fields for `code`, `name`, `manager_id`, `manager_name`, `assigned_modules`, `default_permissions`, and `status`.
3. **Existing HR & Task Foundations:** `apps.hr` contains `AttendanceRecord`, `LeaveRequest`, `ShiftMaster`, etc. `apps.projects` contains `ProjectTask` and `DepartmentAssignment`. These are fully reusable for later phases and must not be duplicated.
4. **Primary Security Gap:** Default DRF permission class across the system was `AllowAny`. Views like `EmployeeViewSet`, `DepartmentViewSet`, and custom action endpoints lacked strict server-side RBAC scoping (`own`, `assigned`, `department`, `all`), action authorization (`view`, `create`, `edit`, `delete`, `approve`, `assign`, etc.), and privilege-escalation prevention.

---

## 2. Audit of Existing Models & Database Schema

### 2.1 Organization App (`apps/organization/models.py`)
- **`Department` Model:**
  - `id` (CharField, PK, e.g. `dept-crm`)
  - `code` (CharField, unique, e.g. `CRM`, `PRD`)
  - `name` (CharField, e.g. `CRM & Sales`, `Production & Shop Floor`)
  - `manager_id` (CharField, nullable)
  - `manager_name` (CharField, nullable)
  - `description` (TextField)
  - `parent_department_id` (CharField, nullable)
  - `assigned_modules` (JSONField, default=list)
  - `default_permissions` (JSONField, default=dict)
  - `status` (CharField, default='active')
  - `employee_count` (IntegerField, default=0)
  - `created_by` (CharField, default='Super Admin')
  - `created_at` (DateTimeField, auto_now_add=True)
  - `updated_at` (DateTimeField, auto_now=True)
  *Audit Verdict:* Complete schema matching all Phase 1 requirements. Needs no additional fields.

- **`Role` Model:**
  - `id` (CharField, PK, e.g. `role-xxx`)
  - `name` (CharField, e.g. `HOD`, `Operator`)
  - `description` (TextField)
  - `is_system` (BooleanField)
  - `department_id` (CharField, nullable)
  - `permissions` (JSONField, default=list)

### 2.2 Authentication & Employee App (`apps/authentication/models.py`)
- **`User` Model (`AbstractUser`):**
  - **Identity & Contact:** `id` (PK, e.g. `EMP-001`), `username`, `email`, `first_name`, `last_name`, `gender`, `dob`, `mobile`, `phone`, `address`, `work_location`, `emergency_contact`, `profile_photo`.
  - **Organization Linking:** `department` (FK to Department), `department_name`, `designation`, `role_profile` (FK to Role), `role_name`, `reporting_manager_id`, `reporting_manager_name`, `joining_date`, `employment_type`.
  - **Role & Scope:** `role_type` (`super_admin`, `admin`, `department_manager`, `employee`), `data_scope` (`own`, `assigned`, `department`, `all`).
  - **Permissions:** `assigned_modules` (JSONField), `custom_permissions` (JSONField), `can_assign_tasks` (bool), `can_approve_leaves` (bool), `can_manage_attendance` (bool), `can_export_data` (bool), `force_password_change` (bool), `is_family_member` (bool), `status` (CharField).
  *Missing Fields Identified:*
  1. `explicit_restrictions` (JSONField, default=list): Required to fulfill "Explicit restrictions must override ordinary grants".
  2. `permissions_review_required` (BooleanField, default=False): Required to fulfill "Department changes must trigger a permission review".
  3. `previous_department_name` (CharField, default='', blank=True): Audit trail of prior department.

### 2.3 HR App (`apps/hr/models.py`)
- Audited models: `Designation`, `EmployeeDocument`, `ShiftMaster`, `AttendanceRecord`, `LeaveRequest`, `WFHRequest`, `MissedPunchRequest`, `AttendanceRegularization`, `OvertimeRecord`, `EarlyCheckoutRequest`, `SalaryComponent`, `SalaryStructure`, `PayrollRecord`, `EmployeeAdvanceLoan`, `ReimbursementExpense`, `EmployeeOnboarding`, `EmployeeTransfer`, `EmployeePromotion`, `EmployeeExit`, `Holiday`, `EmployeeAppraisal`.
- Verdict: All 21 models present and fully configured for Phase 3 (Attendance & Leave). No duplicate tables will be created.

### 2.4 Projects App (`apps/projects/models.py`)
- Audited models: `ProjectJobMaster`, `ProjectPlanningStage`, `ProjectMilestone`, `ProjectTask`, `DepartmentAssignment`, `ProjectIssue`, `ProjectDelay`, `CustomerChangeRequest`, `ProjectCost`, `ProjectDocument`.
- Verdict: `ProjectTask` includes `department`, `assigned_to_id`, `assigned_to_name`, `status`, `progress_percent`, `estimated_hours`, `actual_hours`. Ready for Phase 4 (Task Management).

---

## 3. Audit of Existing APIs, Serializers & URL Routes

### 3.1 Organization Endpoints (`/api/departments/`, `/api/roles/`)
- ViewSet: `DepartmentViewSet`, `RoleViewSet` in `apps.organization.views`
- Serializer: `DepartmentSerializer` with regex validation on name, `RoleSerializer`
- **Gaps:**
  - Permission was `AllowAny`.
  - No `deactivate` action endpoint.
  - No default permissions update endpoint with validation.

### 3.2 Employee Endpoints (`/api/employees/`)
- ViewSet: `EmployeeViewSet` in `apps.authentication.views`
- Serializer: `UserSerializer` supporting camelCase mapping and smart role inference.
- Existing custom actions:
  - `POST /api/employees/{id}/reset-password/`
  - `GET /api/employees/{id}/permissions/`
  - `POST /api/employees/{id}/permissions/` (and PATCH)
- **Gaps:**
  - Permission was `AllowAny`.
  - Missing `@action(detail=True, methods=['get']) def effective_permissions`: No calculated breakdown of department defaults vs custom permissions vs explicit restrictions.
  - Missing `@action(detail=True, methods=['post']) def deactivate`: No safe deactivation endpoint.
  - Permission elevation loophole: Anyone could POST to `/api/employees/{id}/permissions/` without checking if requester was super_admin or admin, allowing self-escalation.
  - Changing an employee's department via `PATCH /api/employees/{id}/` retained old permissions without initiating a permission review.

---

## 4. Migration Status

Inspection via `python manage.py showmigrations` confirmed all migrations are currently applied:
- `authentication`: `0001_initial`, `0002_alter_user_id`, `0003_user_assigned_modules_user_can_approve_leaves_and_more`
- `organization`: `0001_initial`, `0002_department_assigned_modules_department_created_by_and_more`
- `core`: `0001_initial` through `0003_dataimportlog_golivechecklistitem_and_more`
- `crm`: `0001` through `0006`
- `designer`: `0001` through `0006`
- `hr`: `0001` through `0005`
- `projects`: `0001` through `0006`
- `store`, `purchase`, `production`, `maintenance`, `accounting`, `integration`: all up to date.

*Action Required:* Create migration `0004_user_explicit_restrictions_and_review.py` for `apps.authentication` to add `explicit_restrictions`, `permissions_review_required`, and `previous_department_name`.

---

## 5. Security & Authorization Gaps

| Area | Current State | Required State | Action |
|---|---|---|---|
| Default Permissions | `AllowAny` in DRF settings | Deny by default / IsAuthenticated | Protect endpoints with RBAC |
| Department Actions | `AllowAny` on all CRUD | Admin/Super Admin only for write; IsAuthenticated for read | Secure `DepartmentViewSet` |
| Employee Access | `AllowAny` on `/api/employees/` | Admin/Manager can manage; employees read own/scoped profile | Secure `EmployeeViewSet` |
| Self-Escalation | No check on caller | Non-super-admin cannot change own role/scope/permissions | Block self-escalation in view |
| Admin Authority Bounds | Any admin could grant any role | Admins cannot grant permissions beyond their own scope | Validate grant scope |
| Explicit Restrictions | Not supported in data model | Explicit restrictions override all grants | Add field & RBAC calculation |
| Department Transition | Retained old department permissions | Trigger review flag & purge obsolete privileges | Implement on `User.save()` & `update()` |
| Effective Permissions | None | Dedicated endpoint `/api/employees/{id}/effective-permissions/` | Add endpoint & logic |
| Data Scope Isolation | Unfiltered querysets on employees | Filter by `own`, `assigned`, `department`, `all` | Implement scoped querysets |

---

## 6. Implementation Plan & Affected Files

1. **`apps/authentication/models.py`:**
   - Add `explicit_restrictions = models.JSONField(default=list, blank=True)`
   - Add `permissions_review_required = models.BooleanField(default=False)`
   - Add `previous_department_name = models.CharField(max_length=100, blank=True, default='')`
   - Implement department change detection in `save()`: if department changes, set `permissions_review_required=True`, record `previous_department_name`, and reset department-bound custom permissions.

2. **`apps/core/rbac_permissions.py` (New Central RBAC Module):**
   - `IsSuperAdminUser`: Verifies `is_superuser` or `role_type == 'super_admin'`.
   - `IsAdminOrSuperAdmin`: Verifies admin or super_admin.
   - `HasModulePermission(module_name, required_action)`: General RBAC validator checking module, action, and explicit restrictions.
   - `ScopedEmployeeAccessPermission`: Enforces employee CRUD rules, preventing self-escalation and privilege overreach.
   - Helper function `compute_effective_permissions(user)`: Returns structured map of allowed modules, actions, scopes, and explicit restrictions.

3. **`apps/organization/views.py` & `serializers.py`:**
   - Enforce RBAC permissions on `DepartmentViewSet`.
   - Add `@action(detail=True, methods=['post']) def deactivate(self, request, pk=None)`.
   - Add `@action(detail=True, methods=['post']) def activate(self, request, pk=None)`.
   - Add `@action(detail=True, methods=['get', 'patch']) def configure_modules(self, request, pk=None)`.

4. **`apps/authentication/views.py` & `serializers.py`:**
   - Add `explicit_restrictions`, `permissions_review_required`, `previous_department_name` to `UserSerializer`.
   - Secure `EmployeeViewSet`:
     - Disallow unauthenticated requests (HTTP 401).
     - Queryset scoping: `super_admin` and `admin` with `all` scope see all; `department_manager` sees department; `employee` with `own` scope sees self or teammates according to `data_scope`.
     - Block self-escalation on `manage_permissions`, `update`, `partial_update`.
     - Admin authority bounds check: Admin cannot grant `super_admin` role or permissions outside their own assigned modules.
     - Add `@action(detail=True, methods=['get']) def effective_permissions(self, request, pk=None)`.
     - Add `@action(detail=True, methods=['post']) def deactivate(self, request, pk=None)`.
     - Add `@action(detail=True, methods=['post']) def activate(self, request, pk=None)`.

5. **Automated Test Suite (`apps/authentication/test_phase1_rbac.py`):**
   - Multi-role isolation tests: Super Admin, Admin, Department Manager, Employee Dept A, Employee Dept B.
   - Verify self-escalation denial (HTTP 403).
   - Verify unauthenticated requests (HTTP 401).
   - Verify cross-department data isolation.
   - Verify explicit restrictions overriding grants.
   - Verify department change triggers permission review.
