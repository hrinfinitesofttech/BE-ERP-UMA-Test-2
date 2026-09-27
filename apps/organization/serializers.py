from rest_framework import serializers
from .models import Department, Role


class DepartmentSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = Department
        fields = [
            'id',
            'code',
            'name',
            'department_name',
            'manager_id',
            'manager_name',
            'description',
            'status',
            'employee_count',
        ]


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = [
            'id',
            'name',
            'description',
            'is_system',
            'department_id',
            'permissions',
        ]
