from datetime import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import (
    DesignJob,
    CustomerRequirement,
    Drawing2D,
    Design3DModel,
    BOMHeader,
    DesignRevisionLog,
    TechnicalDocumentItem,
)
from .serializers import (
    DesignJobSerializer,
    CustomerRequirementSerializer,
    Drawing2DSerializer,
    Design3DModelSerializer,
    BOMHeaderSerializer,
    DesignRevisionLogSerializer,
    TechnicalDocumentItemSerializer,
)


class DesignJobViewSet(viewsets.ModelViewSet):
    queryset = DesignJob.objects.all().order_by('-created_at')
    serializer_class = DesignJobSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id') or not data.get('design_job_number') and not data.get('designJobNumber'):
            code = f"DES-2026-{DesignJob.objects.count() + 1:04d}"
            data['id'] = code
            data['design_job_number'] = code
        if not data.get('created_date') and not data.get('createdDate'):
            data['created_date'] = datetime.now().strftime('%Y-%m-%d')
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='release-to-production')
    def release_to_production(self, request, pk=None):
        job = self.get_object()
        job.status = 'released_to_production'
        job.save(update_fields=['status'])

        # Also release linked BOM
        bom = BOMHeader.objects.filter(design_job_id=job.id).first()
        if bom:
            bom.status = 'released'
            bom.release_date = datetime.now().strftime('%Y-%m-%d')
            bom.save(update_fields=['status', 'release_date'])

        return Response({
            'success': True,
            'message': f'Design Job {job.design_job_number} officially released to Production!',
            'job': DesignJobSerializer(job).data,
            'bom': BOMHeaderSerializer(bom).data if bom else None,
        })


class CustomerRequirementViewSet(viewsets.ModelViewSet):
    queryset = CustomerRequirement.objects.all().order_by('-created_at')
    serializer_class = CustomerRequirementSerializer
    permission_classes = [permissions.AllowAny]


class Drawing2DViewSet(viewsets.ModelViewSet):
    queryset = Drawing2D.objects.all().order_by('-created_at')
    serializer_class = Drawing2DSerializer
    permission_classes = [permissions.AllowAny]


class Design3DModelViewSet(viewsets.ModelViewSet):
    queryset = Design3DModel.objects.all().order_by('-created_at')
    serializer_class = Design3DModelSerializer
    permission_classes = [permissions.AllowAny]


class BOMHeaderViewSet(viewsets.ModelViewSet):
    queryset = BOMHeader.objects.all().order_by('-created_at')
    serializer_class = BOMHeaderSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not data.get('id') or not data.get('bom_number') and not data.get('bomNumber'):
            code = f"BOM-2026-{BOMHeader.objects.count() + 1:04d}"
            data['id'] = code
            data['bom_number'] = code
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        bom = self.get_object()
        item = request.data
        items = list(bom.items or [])
        items.append(item)
        bom.items = items
        bom.total_items = len(items)
        bom.save(update_fields=['items', 'total_items'])
        return Response(BOMHeaderSerializer(bom).data)


class DesignRevisionLogViewSet(viewsets.ModelViewSet):
    queryset = DesignRevisionLog.objects.all().order_by('-date')
    serializer_class = DesignRevisionLogSerializer
    permission_classes = [permissions.AllowAny]


class TechnicalDocumentItemViewSet(viewsets.ModelViewSet):
    queryset = TechnicalDocumentItem.objects.all().order_by('-created_date')
    serializer_class = TechnicalDocumentItemSerializer
    permission_classes = [permissions.AllowAny]
