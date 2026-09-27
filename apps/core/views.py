from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import CompanySetting, NumberingSetting, AuditLog, Notification
from .serializers import (
    CompanySettingSerializer,
    NumberingSettingSerializer,
    AuditLogSerializer,
    NotificationSerializer,
)


class CompanySettingView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        setting = CompanySetting.objects.first()
        if not setting:
            setting = CompanySetting.objects.create()
        return Response(CompanySettingSerializer(setting).data)

    def put(self, request):
        setting = CompanySetting.objects.first()
        if not setting:
            setting = CompanySetting.objects.create()
        serializer = CompanySettingSerializer(setting, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
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
