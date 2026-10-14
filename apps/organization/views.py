from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotAuthenticated

from .models import Department, Role
from .serializers import DepartmentSerializer, RoleSerializer
from apps.core.rbac_permissions import is_admin, is_super_admin, IsAdminOrSuperAdmin


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by('-created_at', '-id')
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        # Read-only actions require authentication; Write/Admin actions require Admin or Super Admin
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrSuperAdmin()]

    def perform_create(self, serializer):
        creator_name = 'Super Admin'
        if self.request.user and self.request.user.is_authenticated:
            creator_name = getattr(self.request.user, 'name', self.request.user.username) or self.request.user.username
        serializer.save(created_by=creator_name)

    @action(detail=True, methods=['post', 'patch'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        department = self.get_object()
        department.status = 'inactive'
        department.save(update_fields=['status', 'updated_at'])

        # Audit log
        try:
            from apps.core.models import AuditLog
            admin_name = getattr(request.user, 'name', request.user.username)
            AuditLog.objects.create(
                user_id=request.user.id,
                user_name=admin_name,
                role=getattr(request.user, 'role_type', 'admin'),
                department=getattr(request.user, 'department_name', 'Management'),
                action='DEACTIVATE',
                module='Organization',
                page='Departments',
                record_id=department.id,
                notes=f"Deactivated department {department.name} ({department.code})",
            )
        except Exception:
            pass

        return Response({
            'success': True,
            'message': f"Department {department.name} has been deactivated.",
            'department': DepartmentSerializer(department).data
        })

    @action(detail=True, methods=['post', 'patch'], url_path='activate')
    def activate(self, request, pk=None):
        department = self.get_object()
        department.status = 'active'
        department.save(update_fields=['status', 'updated_at'])
        return Response({
            'success': True,
            'message': f"Department {department.name} has been activated.",
            'department': DepartmentSerializer(department).data
        })

    @action(detail=True, methods=['get', 'patch', 'post'], url_path='configure-modules')
    def configure_modules(self, request, pk=None):
        department = self.get_object()
        if request.method == 'GET':
            return Response({
                'id': department.id,
                'code': department.code,
                'name': department.name,
                'assigned_modules': department.assigned_modules,
                'default_permissions': department.default_permissions,
            })

        data = request.data
        if 'assigned_modules' in data:
            if not isinstance(data['assigned_modules'], list):
                return Response(
                    {'error': 'assigned_modules must be a list of module keys.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            department.assigned_modules = data['assigned_modules']

        if 'default_permissions' in data:
            if not isinstance(data['default_permissions'], dict):
                return Response(
                    {'error': 'default_permissions must be a dictionary of module actions.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            department.default_permissions = data['default_permissions']

        department.save(update_fields=['assigned_modules', 'default_permissions', 'updated_at'])

        return Response({
            'success': True,
            'message': f"Modules and default permissions configured for {department.name}.",
            'department': DepartmentSerializer(department).data
        })


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().order_by('-created_at', '-id')
    serializer_class = RoleSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrSuperAdmin()]

    def destroy(self, request, *args, **kwargs):
        role = self.get_object()
        if getattr(role, 'is_system', False) or role.id in ['role-superadmin', 'role-admin-family', 'role-crm-manager', 'role-crm-employee', 'role-super_admin']:
            return Response(
                {'error': 'System defined core roles cannot be deleted.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)
