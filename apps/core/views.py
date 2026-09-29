from datetime import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action

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
from .serializers import (
    CompanySettingSerializer,
    NumberingSettingSerializer,
    AuditLogSerializer,
    NotificationSerializer,
    BugTicketSerializer,
    BackupRecordSerializer,
    DataImportLogSerializer,
    SecurityCheckRecordSerializer,
    GoLiveChecklistItemSerializer,
)


class CompanySettingView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        setting = CompanySetting.objects.first()
        if not setting:
            setting = CompanySetting.objects.create()
        data = CompanySettingSerializer(setting).data
        # Return both snake_case and camelCase for seamless frontend compatibility
        camel_data = {
            **data,
            'companyName': data.get('company_name'),
            'logoUrl': data.get('logo_url'),
            'financialYear': data.get('financial_year'),
            'bankName': data.get('bank_name'),
            'bankAccountNo': data.get('bank_account_no'),
            'bankIfsc': data.get('bank_ifsc'),
            'bankBranch': data.get('bank_branch'),
        }
        return Response(camel_data)

    def put(self, request):
        setting = CompanySetting.objects.first()
        if not setting:
            setting = CompanySetting.objects.create()
        data = request.data.copy()
        field_mappings = {
            'companyName': 'company_name',
            'logoUrl': 'logo_url',
            'financialYear': 'financial_year',
            'bankName': 'bank_name',
            'bankAccountNo': 'bank_account_no',
            'bankIfsc': 'bank_ifsc',
            'bankBranch': 'bank_branch',
        }
        for camel, snake in field_mappings.items():
            if camel in data and not data.get(snake):
                data[snake] = data[camel]

        serializer = CompanySettingSerializer(setting, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            res_data = serializer.data
            camel_data = {
                **res_data,
                'companyName': res_data.get('company_name'),
                'logoUrl': res_data.get('logo_url'),
                'financialYear': res_data.get('financial_year'),
                'bankName': res_data.get('bank_name'),
                'bankAccountNo': res_data.get('bank_account_no'),
                'bankIfsc': res_data.get('bank_ifsc'),
                'bankBranch': res_data.get('bank_branch'),
            }
            return Response(camel_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        return self.put(request)


class NumberingSettingViewSet(viewsets.ModelViewSet):
    queryset = NumberingSetting.objects.all().order_by('id')
    serializer_class = NumberingSettingSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get', 'post'], url_path='next-number')
    def next_number(self, request):
        doc_type = request.query_params.get('docType') or request.data.get('docType') or request.query_params.get('doc_type')
        if not doc_type:
            return Response(
                {'error': 'docType parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        setting = NumberingSetting.objects.filter(doc_type=doc_type).first()
        if not setting:
            # Auto-create fallback numbering setting
            prefix = f"{doc_type.upper()[:3]}-2026-"
            setting = NumberingSetting.objects.create(
                id=f"num-{doc_type}",
                module='General',
                doc_type=doc_type,
                prefix=prefix,
                current_number=1,
                digit_count=4,
                sample_preview=f"{prefix}0001",
            )

        # POST increments the number, GET just previews or generates next
        increment = request.method == 'POST' or request.query_params.get('increment', 'false').lower() == 'true'
        next_code = setting.generate_next_number(increment=increment)
        return Response({
            'docType': doc_type,
            'nextNumber': next_code,
            'currentNumber': setting.current_number,
            'samplePreview': setting.sample_preview,
        })


class AuditLogViewSet(viewsets.ModelViewSet):
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        module = self.request.query_params.get('module')
        action_name = self.request.query_params.get('action')
        user_id = self.request.query_params.get('userId')
        if module:
            qs = qs.filter(module=module)
        if action_name:
            qs = qs.filter(action=action_name)
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by('-timestamp')
    serializer_class = NotificationSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        dept = self.request.query_params.get('department')
        unread_only = self.request.query_params.get('unread')
        if dept and dept != 'all':
            qs = qs.filter(department__in=[dept, 'all'])
        if unread_only == 'true':
            qs = qs.filter(is_read=False)
        return qs

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return Response({'success': True, 'id': notif.id})

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        Notification.objects.filter(is_read=False).update(is_read=True)
        return Response({'success': True, 'message': 'All notifications marked as read'})


class BugTicketViewSet(viewsets.ModelViewSet):
    queryset = BugTicket.objects.all().order_by('-created_at')
    serializer_class = BugTicketSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            data['id'] = f"BUG-{BugTicket.objects.count() + 1:03d}"
        if not data.get('bug_no'):
            data['bug_no'] = data.get('bugNo') or f"BUG-2026-{BugTicket.objects.count() + 1:03d}"
        if 'module_page' not in data:
            data['module_page'] = data.get('modulePage') or data.get('module') or 'General'
        if 'steps_to_reproduce' not in data:
            data['steps_to_reproduce'] = data.get('stepsToReproduce') or ''
        if 'actual_result' not in data:
            data['actual_result'] = data.get('actualResult') or ''
        if 'expected_result' not in data:
            data['expected_result'] = data.get('expectedResult') or ''
        if 'fixed_notes' not in data:
            data['fixed_notes'] = data.get('fixedNotes') or ''
        if 'created_date' not in data:
            data['created_date'] = data.get('createdDate') or ''

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BackupRecordViewSet(viewsets.ModelViewSet):
    queryset = BackupRecord.objects.all().order_by('-created_at')
    serializer_class = BackupRecordSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            data['id'] = f"BKP-{BackupRecord.objects.count() + 1:03d}"
        if 'backup_name' not in data:
            data['backup_name'] = data.get('backupName') or f"Manual ERP Backup {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        if 'backup_type' not in data:
            data['backup_type'] = data.get('backupType') or 'Full Database & Media'
        if 'file_size' not in data:
            data['file_size'] = data.get('fileSize') or '24.5 MB'
        if 'backup_date' not in data:
            data['backup_date'] = data.get('backupDate') or datetime.now().strftime('%Y-%m-%d %H:%M')
        if 'created_by' not in data:
            data['created_by'] = data.get('createdBy') or 'Super Admin'

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DataImportLogViewSet(viewsets.ModelViewSet):
    queryset = DataImportLog.objects.all().order_by('-created_at')
    serializer_class = DataImportLogSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if not data.get('id'):
            data['id'] = f"IMP-{DataImportLog.objects.count() + 1:03d}"
        if 'entity_type' not in data:
            data['entity_type'] = data.get('entityType') or 'Customers'
        if 'file_name' not in data:
            data['file_name'] = data.get('fileName') or 'import_data.csv'
        if 'records_count' not in data:
            data['records_count'] = data.get('recordsCount') or data.get('recordCount') or 0
        if 'imported_by' not in data:
            data['imported_by'] = data.get('importedBy') or 'Super Admin'
        if 'imported_at' not in data:
            data['imported_at'] = data.get('importedAt') or datetime.now().strftime('%Y-%m-%d %H:%M')

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SecurityCheckRecordViewSet(viewsets.ModelViewSet):
    queryset = SecurityCheckRecord.objects.all().order_by('-created_at')
    serializer_class = SecurityCheckRecordSerializer
    permission_classes = [permissions.AllowAny]


class GoLiveChecklistItemViewSet(viewsets.ModelViewSet):
    queryset = GoLiveChecklistItem.objects.all().order_by('module_name')
    serializer_class = GoLiveChecklistItemSerializer
    permission_classes = [permissions.AllowAny]


