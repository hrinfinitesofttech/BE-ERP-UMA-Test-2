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
            'parent_department_id',
            'assigned_modules',
            'default_permissions',
            'status',
            'employee_count',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_name(self, value):
        import re
        val_str = str(value).strip()
        if not val_str:
            raise serializers.ValidationError("Please enter the department name.")
        if len(val_str) < 2 or len(val_str) > 50:
            raise serializers.ValidationError("The department name must be between 2 and 50 characters and cannot contain special characters.")
        if not re.match(r'^[a-zA-Z0-9\s&/-]+$', val_str):
            raise serializers.ValidationError("The department name must be between 2 and 50 characters and cannot contain special characters.")

        qs = Department.objects.filter(name__iexact=val_str)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A department with this name already exists.")
        return val_str


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
