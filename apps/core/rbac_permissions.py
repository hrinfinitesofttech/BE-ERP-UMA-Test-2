"""
UmaERP Centralized Role-Based Access Control (RBAC) Foundation
Enforces strict server-side permission checks across modules, actions, and data scopes.

Supported Actions:
view, create, edit, delete, approve, assign, update_status, export, print, manage_settings.

Supported Scopes:
own, assigned, department, all.

Security Rules:
1. Deny access by default.
2. Super Admin privileges must be explicitly determined (is_superuser or role_type == 'super_admin').
3. Admins must not grant privileges or assign roles beyond their own authorized scope.
4. Employees must not change their own role, data scope, or permissions (prevent self-escalation).
5. Explicit restrictions strictly override all role and department grants.
6. Unauthenticated requests return HTTP 401; unauthorized requests return HTTP 403.
"""

from rest_framework import permissions, exceptions
from django.db.models import Q


ALL_ACTIONS = [
    'view',
    'create',
    'edit',
    'delete',
    'approve',
    'assign',
    'update_status',
    'export',
    'print',
    'manage_settings',
]

ALL_SCOPES = ['own', 'assigned', 'department', 'all']


def is_super_admin(user):
    """
    Explicitly and securely determine if a user has Super Admin privileges.
    """
    if not user or not user.is_authenticated:
        return False
    return bool(user.is_superuser or getattr(user, 'role_type', '') == 'super_admin')


def is_admin(user):
    """
    Check if a user has Admin or Super Admin privileges.
    """
    if not user or not user.is_authenticated:
        return False
    if is_super_admin(user):
        return True
    return getattr(user, 'role_type', '') in ('admin', 'super_admin')


def is_department_manager(user):
    """
    Check if a user is a Department Manager, Admin, or Super Admin.
    """
    if not user or not user.is_authenticated:
        return False
    if is_admin(user):
        return True
    return getattr(user, 'role_type', '') == 'department_manager'


def check_explicit_restriction(user, module, action):
    """
    Returns True if an explicit restriction blocks access to (module, action).
    Explicit restrictions ALWAYS override any ordinary grants.
    Supported patterns in explicit_restrictions:
    - "module:action" (e.g. "crm:delete")
    - "*:action" (e.g. "*:delete")
    - "module:*" (e.g. "crm:*")
    - Dict format: {"crm": ["delete", "export"]}
    """
    restrictions = getattr(user, 'explicit_restrictions', None) or []
    if isinstance(restrictions, dict):
        module_restrictions = restrictions.get(module, [])
        if action in module_restrictions or '*' in module_restrictions:
            return True
        wildcard_restrictions = restrictions.get('*', [])
        if action in wildcard_restrictions or '*' in wildcard_restrictions:
            return True
        return False

    if isinstance(restrictions, list):
        target = f"{module}:{action}".lower()
        wildcard_action = f"*:{action}".lower()
        wildcard_module = f"{module}:*".lower()
        for r in restrictions:
            r_str = str(r).strip().lower()
            if r_str in (target, wildcard_action, wildcard_module, "*:*"):
                return True
    return False


def compute_effective_permissions(user):
    """
    Computes and returns the complete, resolved permissions matrix for a user.
    Resolution Order:
    1. Super Admin: full access to all system modules and actions, minus explicit restrictions.
    2. Department Defaults: base modules & actions from user.department.
    3. User Custom Permissions: additions or overrides.
    4. Explicit Restrictions: overrides and revokes any matched grant.
    """
    if not user or not user.is_authenticated:
        return {
            'role_type': 'anonymous',
            'data_scope': 'none',
            'allowed_modules': [],
            'permissions_matrix': {},
            'explicit_restrictions': [],
            'capabilities': {
                'can_assign_tasks': False,
                'can_approve_leaves': False,
                'can_manage_attendance': False,
                'can_export_data': False,
            }
        }

    role_type = getattr(user, 'role_type', 'employee')
    data_scope = getattr(user, 'data_scope', 'own')
    explicit_restrictions = getattr(user, 'explicit_restrictions', []) or []

    # System modules catalog
    all_modules = [
        'organization', 'employees', 'crm', 'projects', 'designer',
        'purchase', 'store', 'production', 'maintenance', 'hr',
        'accounting', 'integration', 'reports', 'settings'
    ]

    permissions_matrix = {}

    if is_super_admin(user):
        allowed_modules = list(all_modules)
        for mod in allowed_modules:
            actions = [act for act in ALL_ACTIONS if not check_explicit_restriction(user, mod, act)]
            permissions_matrix[mod] = actions
        scope = 'all'
        can_assign = not check_explicit_restriction(user, 'tasks', 'assign')
        can_approve = not check_explicit_restriction(user, 'leaves', 'approve')
        can_attendance = not check_explicit_restriction(user, 'attendance', 'manage_settings')
        can_export = not check_explicit_restriction(user, '*', 'export')
    else:
        # 1. Base modules: Explicit User assigned_modules strictly override department defaults
        dept = getattr(user, 'department', None)
        dept_modules = list(getattr(dept, 'assigned_modules', []) or []) if dept else []
        dept_defaults = dict(getattr(dept, 'default_permissions', {}) or {}) if dept else {}

        # 2. Check User's assigned modules
        user_modules = list(getattr(user, 'assigned_modules', []) or [])
        if user_modules:
            combined_modules = list(user_modules)
        else:
            combined_modules = list(dept_modules)

        custom_perms = dict(getattr(user, 'custom_permissions', {}) or {})

        allowed_modules = []
        for mod in combined_modules:
            mod_actions = set()
            # Department defaults
            mod_actions.update(dept_defaults.get(mod, []))
            # Custom additions
            mod_actions.update(custom_perms.get(mod, []))

            # Default view action for assigned modules
            mod_actions.add('view')

            # Manager defaults
            if role_type == 'department_manager':
                mod_actions.update(['create', 'edit', 'approve', 'assign', 'update_status'])
            elif role_type == 'admin':
                mod_actions.update(['create', 'edit', 'delete', 'approve', 'assign', 'update_status', 'export'])

            # Filter out explicit restrictions
            final_actions = [
                act for act in mod_actions
                if act in ALL_ACTIONS and not check_explicit_restriction(user, mod, act)
            ]

            if final_actions:
                allowed_modules.append(mod)
                permissions_matrix[mod] = sorted(final_actions)

        scope = data_scope
        can_assign = bool(getattr(user, 'can_assign_tasks', False) or role_type in ('admin', 'department_manager'))
        can_approve = bool(getattr(user, 'can_approve_leaves', False) or role_type in ('admin', 'department_manager'))
        can_attendance = bool(getattr(user, 'can_manage_attendance', False) or role_type in ('admin', 'department_manager'))
        can_export = bool(getattr(user, 'can_export_data', True))

        # Check explicit restrictions on capabilities
        if check_explicit_restriction(user, 'tasks', 'assign'):
            can_assign = False
        if check_explicit_restriction(user, 'leaves', 'approve'):
            can_approve = False
        if check_explicit_restriction(user, 'attendance', 'manage_settings'):
            can_attendance = False
        if check_explicit_restriction(user, '*', 'export'):
            can_export = False

    return {
        'user_id': user.id,
        'username': user.username,
        'role_type': role_type,
        'data_scope': scope,
        'department_id': getattr(user, 'department_id', None),
        'department_name': getattr(user, 'department_name', ''),
        'allowed_modules': allowed_modules,
        'permissions_matrix': permissions_matrix,
        'explicit_restrictions': explicit_restrictions,
        'permissions_review_required': getattr(user, 'permissions_review_required', False),
        'capabilities': {
            'can_assign_tasks': can_assign,
            'can_approve_leaves': can_approve,
            'can_manage_attendance': can_attendance,
            'can_export_data': can_export,
        }
    }


def map_view_action_to_rbac(action, method='GET'):
    """
    Maps DRF viewset actions and HTTP methods to standard RBAC action verbs.
    """
    action = (action or '').lower()
    method = (method or '').upper()

    if action in ('list', 'retrieve', 'get'):
        return 'view'
    if action in ('create', 'post'):
        return 'create'
    if action in ('update', 'partial_update', 'patch', 'put'):
        return 'edit'
    if action in ('destroy', 'delete'):
        return 'delete'
    if 'approve' in action:
        return 'approve'
    if 'assign' in action:
        return 'assign'
    if 'status' in action:
        return 'update_status'
    if 'export' in action or 'download' in action:
        return 'export'
    if 'print' in action:
        return 'print'
    if 'setting' in action or 'configure' in action or 'reset' in action:
        return 'manage_settings'

    if method in ('GET', 'HEAD', 'OPTIONS'):
        return 'view'
    if method == 'POST':
        return 'create'
    if method in ('PUT', 'PATCH'):
        return 'edit'
    if method == 'DELETE':
        return 'delete'

    return 'view'


class IsSuperAdmin(permissions.BasePermission):
    """
    Allows access only to verified Super Admin users.
    Returns 401 if unauthenticated, 403 if unauthorized.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise exceptions.NotAuthenticated("Authentication credentials were not provided.")
        if not is_super_admin(request.user):
            raise exceptions.PermissionDenied("Super Admin privileges required.")
        return True


class IsAdminOrSuperAdmin(permissions.BasePermission):
    """
    Allows access to Admin and Super Admin users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise exceptions.NotAuthenticated("Authentication credentials were not provided.")
        if not is_admin(request.user):
            raise exceptions.PermissionDenied("Admin privileges required.")
        return True


class IsDepartmentManagerOrAdmin(permissions.BasePermission):
    """
    Allows access to Department Managers, Admins, and Super Admins.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise exceptions.NotAuthenticated("Authentication credentials were not provided.")
        if not is_department_manager(request.user):
            raise exceptions.PermissionDenied("Department Manager or Admin privileges required.")
        return True


class ServerRBACPermission(permissions.BasePermission):
    """
    Central server-side RBAC permission class.
    Checks:
    1. Authentication (401 if missing)
    2. Explicit Super Admin bypass (unless explicitly restricted)
    3. Explicit restrictions check (strictly overrides grants)
    4. Module and action permission check against effective matrix
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise exceptions.NotAuthenticated("Authentication credentials were not provided.")

        module = getattr(view, 'rbac_module', None)
        if not module:
            # Fallback to app_label
            app_label = getattr(getattr(view, 'queryset', None), 'model', None)
            module = app_label._meta.app_label if app_label else 'core'

        action = getattr(view, 'rbac_action', None) or map_view_action_to_rbac(
            getattr(view, 'action', None),
            request.method
        )

        # Check explicit restrictions first
        if check_explicit_restriction(request.user, module, action):
            raise exceptions.PermissionDenied(
                f"Action '{action}' on module '{module}' is explicitly restricted for your account."
            )

        if is_super_admin(request.user):
            return True

        eff = compute_effective_permissions(request.user)
        allowed_actions = eff['permissions_matrix'].get(module, [])

        if action not in allowed_actions:
            raise exceptions.PermissionDenied(
                f"You do not have '{action}' permission on module '{module}'."
            )

        return True

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            raise exceptions.NotAuthenticated("Authentication credentials were not provided.")

        if is_super_admin(request.user):
            return True

        scope = getattr(request.user, 'data_scope', 'own')
        if scope == 'all':
            return True

        # Check department scope
        if scope == 'department':
            user_dept = getattr(request.user, 'department_id', None)
            obj_dept = getattr(obj, 'department_id', None) or getattr(obj, 'department', None)
            if hasattr(obj_dept, 'id'):
                obj_dept = obj_dept.id
            if user_dept and obj_dept and str(user_dept) == str(obj_dept):
                return True
            raise exceptions.PermissionDenied("You are not permitted to access records outside your department.")

        # Check assigned scope
        if scope == 'assigned':
            assigned_id = getattr(obj, 'assigned_to_id', None) or getattr(obj, 'assignee_id', None)
            if assigned_id and str(assigned_id) == str(request.user.id):
                return True
            # Allow if user created it
            owner_id = getattr(obj, 'created_by_id', None) or getattr(obj, 'user_id', None)
            if owner_id and str(owner_id) == str(request.user.id):
                return True
            raise exceptions.PermissionDenied("You are not permitted to access unassigned records.")

        # Check own scope
        if scope == 'own':
            if hasattr(obj, 'id') and str(obj.id) == str(request.user.id):
                return True
            owner_id = getattr(obj, 'user_id', None) or getattr(obj, 'employee_id', None) or getattr(obj, 'created_by_id', None)
            if owner_id and str(owner_id) == str(request.user.id):
                return True
            raise exceptions.PermissionDenied("You are only permitted to access your own records.")

        raise exceptions.PermissionDenied("Access denied by data scope policy.")


def apply_data_scope_filter(queryset, user, department_field='department_id', owner_field='user_id', assigned_field='assigned_to_id'):
    """
    Applies secure data visibility scoping to querysets based on user's role and data_scope.
    """
    if not user or not user.is_authenticated:
        return queryset.none()

    if is_super_admin(user):
        return queryset

    scope = getattr(user, 'data_scope', 'own')
    if scope == 'all':
        return queryset

    if scope == 'department':
        user_dept = getattr(user, 'department_id', None)
        if not user_dept:
            return queryset.none()
        filter_kwargs = {department_field: user_dept}
        return queryset.filter(**filter_kwargs)

    if scope == 'assigned':
        q_filter = Q(**{assigned_field: user.id})
        if owner_field:
            q_filter |= Q(**{owner_field: user.id})
        return queryset.filter(q_filter)

    if scope == 'own':
        if owner_field:
            return queryset.filter(**{owner_field: user.id})
        return queryset.none()

    return queryset.none()
