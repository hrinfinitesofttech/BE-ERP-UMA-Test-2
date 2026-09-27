from rest_framework import serializers
from .models import CompanySetting, NumberingSetting, AuditLog, Notification


class CompanySettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanySetting
        fields = [
            'id',
            'company_name',
            'tagline',
            'logo_url',
            'address',
            'city',
            'state',
            'country',
            'pincode',
            'phone',
            'email',
            'website',
            'gstin',
            'pan',
            'cin',
            'financial_year',
            'currency',
            'timezone',
            'bank_name',
            'bank_account_no',
            'bank_ifsc',
            'bank_branch',
            'updated_at',
        ]


class NumberingSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NumberingSetting
        fields = [
            'id',
            'module',
            'doc_type',
            'prefix',
            'suffix',
            'current_number',
            'digit_count',
            'sample_preview',
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'timestamp',
            'user_id',
            'user_name',
            'role',
            'department',
            'action',
            'module',
            'page',
            'record_id',
            'old_value',
            'new_value',
            'ip_address',
            'notes',
        ]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'timestamp',
            'title',
            'message',
            'type',
            'department',
            'link_url',
            'is_read',
            'priority',
        ]
