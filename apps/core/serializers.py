import uuid
from rest_framework import serializers
from .models import (
    CompanySetting,
    NumberingSetting,
    AuditLog,
    Notification,
    BugTicket,
    BackupRecord,
    DataImportLog,
    SecurityCheckRecord,
    GoLiveChecklistItem,
)


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

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        mappings = {
            'companyName': 'company_name',
            'logoUrl': 'logo_url',
            'financialYear': 'financial_year',
            'bankName': 'bank_name',
            'bankAccountNo': 'bank_account_no',
            'bankAccountNumber': 'bank_account_no',
            'bankIfsc': 'bank_ifsc',
            'bankIfscCode': 'bank_ifsc',
            'bankBranch': 'bank_branch',
        }
        for camel, snake in mappings.items():
            if camel in data and snake not in data:
                data[snake] = data[camel]
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['companyName'] = ret.get('company_name')
        ret['logoUrl'] = ret.get('logo_url')
        ret['financialYear'] = ret.get('financial_year')
        ret['bankName'] = ret.get('bank_name')
        ret['bankAccountNo'] = ret.get('bank_account_no')
        ret['bankAccountNumber'] = ret.get('bank_account_no')
        ret['bankIfsc'] = ret.get('bank_ifsc')
        ret['bankIfscCode'] = ret.get('bank_ifsc')
        ret['bankBranch'] = ret.get('bank_branch')
        return ret


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

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        mappings = {
            'docType': 'doc_type',
            'currentNumber': 'current_number',
            'digitCount': 'digit_count',
            'samplePreview': 'sample_preview',
        }
        for camel, snake in mappings.items():
            if camel in data and snake not in data:
                data[snake] = data[camel]
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['docType'] = ret.get('doc_type')
        ret['currentNumber'] = ret.get('current_number')
        ret['digitCount'] = ret.get('digit_count')
        ret['samplePreview'] = ret.get('sample_preview')
        return ret


class AuditLogSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False, allow_blank=True)
    timestamp = serializers.DateTimeField(read_only=True)

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

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if not data.get('id'):
            data['id'] = f"aud-{uuid.uuid4().hex[:10]}"
        mappings = {
            'userId': 'user_id',
            'userName': 'user_name',
            'recordId': 'record_id',
            'oldValue': 'old_value',
            'newValue': 'new_value',
            'ipAddress': 'ip_address',
        }
        for camel, snake in mappings.items():
            if camel in data and snake not in data:
                data[snake] = data[camel]
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['userId'] = ret.get('user_id')
        ret['userName'] = ret.get('user_name')
        ret['recordId'] = ret.get('record_id')
        ret['oldValue'] = ret.get('old_value')
        ret['newValue'] = ret.get('new_value')
        ret['ipAddress'] = ret.get('ip_address')
        return ret


class NotificationSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False, allow_blank=True)
    timestamp = serializers.DateTimeField(read_only=True)

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

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if not data.get('id'):
            data['id'] = f"notif-{uuid.uuid4().hex[:10]}"
        mappings = {
            'linkUrl': 'link_url',
            'isRead': 'is_read',
        }
        for camel, snake in mappings.items():
            if camel in data and snake not in data:
                data[snake] = data[camel]
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['linkUrl'] = ret.get('link_url')
        ret['isRead'] = ret.get('is_read')
        return ret


class BugTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = BugTicket
        fields = [
            'id',
            'bug_no',
            'title',
            'description',
            'module_page',
            'severity',
            'priority',
            'status',
            'assignee',
            'steps_to_reproduce',
            'actual_result',
            'expected_result',
            'fixed_notes',
            'created_date',
            'created_at',
            'updated_at',
        ]


class BackupRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupRecord
        fields = [
            'id',
            'backup_name',
            'backup_type',
            'file_size',
            'status',
            'backup_date',
            'file_url',
            'created_by',
            'is_automatic',
            'notes',
            'created_at',
        ]


class DataImportLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataImportLog
        fields = '__all__'


class SecurityCheckRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityCheckRecord
        fields = '__all__'


class GoLiveChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoLiveChecklistItem
        fields = '__all__'


