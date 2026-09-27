from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    department_id = serializers.CharField(source='department.id', read_only=True)
    role_id = serializers.CharField(source='role_profile.id', read_only=True)

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

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
