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
            'is_active',
            'explicit_restrictions',
            'permissions_review_required',
            'previous_department_name',
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

    def to_internal_value(self, data):
        # Support camelCase input from frontend
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        camel_to_snake = {
            'firstName': 'first_name',
            'lastName': 'last_name',
            'roleType': 'role_type',
            'roleName': 'role_name',
            'roleId': 'role_id',
            'dataScope': 'data_scope',
            'assignedModules': 'assigned_modules',
            'customPermissions': 'custom_permissions',
            'canAssignTasks': 'can_assign_tasks',
            'canApproveLeaves': 'can_approve_leaves',
            'canManageAttendance': 'can_manage_attendance',
            'canExportData': 'can_export_data',
            'isFamilyMember': 'is_family_member',
            'departmentId': 'department_id',
            'departmentName': 'department_name',
            'joiningDate': 'joining_date',
            'employmentType': 'employment_type',
            'workLocation': 'work_location',
            'emergencyContact': 'emergency_contact',
            'reportingManagerId': 'reporting_manager_id',
            'reportingManagerName': 'reporting_manager_name',
            'explicitRestrictions': 'explicit_restrictions',
            'permissionsReviewRequired': 'permissions_review_required',
            'isActive': 'is_active',
        }
        for camel, snake in camel_to_snake.items():
            if camel in data and snake not in data:
                data[snake] = data[camel]
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        # Determine actual role_type with smart inference
        role_type = ret.get('role_type') or 'employee'
        role_name = ret.get('role_name') or ''
        designation = (instance.designation or '').lower()
        role_lower = role_name.lower()
        username = (instance.username or '').lower()

        if instance.is_superuser or 'super admin' in role_lower or username in ['admin', 'rajesh.admin']:
            role_type = 'super_admin'
            if not role_name:
                role_name = 'Super Admin'
        elif instance.is_family_member or 'admin' in role_lower or username == 'ketan.admin':
            role_type = 'admin'
            if not role_name:
                role_name = 'Admin (Family Member)'
        elif role_type == 'department_manager' or 'manager' in role_lower or 'manager' in designation or 'director' in designation or 'head' in designation:
            role_type = 'department_manager'
            if not role_name:
                role_name = instance.designation or 'Department Manager'
        else:
            if not role_name:
                role_name = instance.designation or 'Staff'

        ret['role_type'] = role_type
        ret['roleType'] = role_type
        ret['role_name'] = role_name
        ret['roleName'] = role_name
        ret['role'] = role_name

        ret['dataScope'] = ret.get('data_scope') or 'department'
        ret['assignedModules'] = ret.get('assigned_modules') or []
        ret['customPermissions'] = ret.get('custom_permissions') or {}

        ret['canAssignTasks'] = bool(ret.get('can_assign_tasks', role_type in ['super_admin', 'admin', 'department_manager']))
        ret['canApproveLeaves'] = bool(ret.get('can_approve_leaves', role_type in ['super_admin', 'admin', 'department_manager']))
        ret['canManageAttendance'] = bool(ret.get('can_manage_attendance', role_type in ['super_admin', 'admin', 'department_manager']))
        ret['canExportData'] = bool(ret.get('can_export_data', True))

        dept_name = ret.get('department_name') or (instance.department.name if instance.department else '')
        ret['department'] = dept_name
        ret['departmentName'] = dept_name
        ret['departmentId'] = ret.get('department_id') or (instance.department.id if instance.department else '')

        ret['joiningDate'] = ret.get('joining_date') or ''
        ret['employmentType'] = ret.get('employment_type') or 'full_time'
        ret['isFamilyMember'] = bool(ret.get('is_family_member', False))
        ret['explicitRestrictions'] = ret.get('explicit_restrictions') or []
        ret['explicit_restrictions'] = ret.get('explicit_restrictions') or []
        ret['permissionsReviewRequired'] = bool(ret.get('permissions_review_required', False))
        ret['permissions_review_required'] = bool(ret.get('permissions_review_required', False))
        ret['previousDepartmentName'] = ret.get('previous_department_name') or ''
        ret['previous_department_name'] = ret.get('previous_department_name') or ''
        ret['isActive'] = bool(instance.is_active)
        ret['is_active'] = bool(instance.is_active)

        return ret
