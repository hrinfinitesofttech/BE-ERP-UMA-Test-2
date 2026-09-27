from rest_framework import viewsets, permissions
from .models import Department, Role
from .serializers import DepartmentSerializer, RoleSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by('code')
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.AllowAny]


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().order_by('name')
    serializer_class = RoleSerializer
    permission_classes = [permissions.AllowAny]
