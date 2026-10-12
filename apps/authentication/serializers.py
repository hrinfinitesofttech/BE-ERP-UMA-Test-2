from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    department_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    role_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'name',
            'username',
            'email',
            'gender',
            'dob',
            'mobile',
            'phone',
            'address',
            'department_id',
            'department_name',
            'designation',
            'role_id',
            'role_name',
            'role_type',
            'data_scope',
            'assigned_modules',
            'custom_permissions',
            'can_assign_tasks',
            'can_approve_leaves',
            'can_manage_attendance',
            'can_export_data',
            'force_password_change',
            'work_location',
            'emergency_contact',
            'reporting_manager_id',
            'reporting_manager_name',
            'joining_date',
            'employment_type',
            'status',
            'last_login_str',
            'is_family_member',
            'profile_photo',
            'password',
        ]

    def validate_address(self, value):
        if value is not None:
            val_str = str(value).strip()
            if not val_str:
                raise serializers.ValidationError("Please enter the residential address.")
            if len(val_str) < 10:
                raise serializers.ValidationError("The address must be at least 10 characters long.")
            if len(val_str) > 250:
                raise serializers.ValidationError("The address cannot be more than 250 characters.")
            if not any(c.isalnum() for c in val_str):
                raise serializers.ValidationError("Please enter a valid address.")
        return value

    def create(self, validated_data):
        from apps.organization.models import Department, Role
        password = validated_data.pop('password', None)
        dept_id = validated_data.pop('department_id', None)
        r_id = validated_data.pop('role_id', None)

        user = User(**validated_data)
        if dept_id:
            dept = Department.objects.filter(id=dept_id).first()
            if not dept:
                dept = Department.objects.filter(code__iexact=dept_id).first()
            if dept:
                user.department = dept
                user.department_name = dept.name
        if r_id:
            role = Role.objects.filter(id=r_id).first()
            if role:
                user.role_profile = role
                user.role_name = role.name

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        from apps.organization.models import Department, Role
        password = validated_data.pop('password', None)
        dept_id = validated_data.pop('department_id', None)
        r_id = validated_data.pop('role_id', None)

        if dept_id is not None:
            if dept_id == '':
                instance.department = None
                instance.department_name = ''
            else:
                dept = Department.objects.filter(id=dept_id).first() or Department.objects.filter(code__iexact=dept_id).first()
                if dept:
                    instance.department = dept
                    instance.department_name = dept.name

        if r_id is not None:
            if r_id == '':
                instance.role_profile = None
                instance.role_name = ''
            else:
                role = Role.objects.filter(id=r_id).first()
                if role:
                    instance.role_profile = role
                    instance.role_name = role.name

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()
        return instance
