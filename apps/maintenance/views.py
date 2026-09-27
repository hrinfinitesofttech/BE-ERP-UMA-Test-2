from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import (
    InternalAsset, CustomerMachine, ServiceRequest, PreventiveMaintenancePlan,
    BreakdownRecord, ServiceVisit, AMCContract
)
from .serializers import (
    InternalAssetSerializer, CustomerMachineSerializer, ServiceRequestSerializer,
    PreventiveMaintenancePlanSerializer, BreakdownRecordSerializer, ServiceVisitSerializer,
    AMCContractSerializer
)


class InternalAssetViewSet(viewsets.ModelViewSet):
    queryset = InternalAsset.objects.all()
    serializer_class = InternalAssetSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['asset_code', 'asset_name', 'model', 'manufacturer', 'serial_number']
    filterset_fields = ['status', 'asset_type', 'department', 'criticality']


class CustomerMachineViewSet(viewsets.ModelViewSet):
    queryset = CustomerMachine.objects.all()
    serializer_class = CustomerMachineSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['customer_machine_id', 'machine_name', 'customer_name', 'serial_number']
    filterset_fields = ['status', 'customer_id', 'job_id']


class ServiceRequestViewSet(viewsets.ModelViewSet):
    queryset = ServiceRequest.objects.all().order_by('-request_date')
    serializer_class = ServiceRequestSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['request_number', 'customer_name', 'machine_name', 'serial_number']
    filterset_fields = ['status', 'priority', 'customer_id']

    @action(detail=True, methods=['post'], url_path='assign')
    def assign_technician(self, request, pk=None):
        sr = self.get_object()
        tech_id = (
            request.data.get('technician_id')
            or request.data.get('technicianId')
            or request.data.get('assigned_technician_id')
            or request.data.get('assignedTechnicianId')
        )
        tech_name = (
            request.data.get('technician_name')
            or request.data.get('technicianName')
            or request.data.get('assigned_technician_name')
            or request.data.get('assignedTechnicianName')
        )
        if tech_id:
            sr.assigned_technician_id = tech_id
        if tech_name:
            sr.assigned_technician_name = tech_name
        sr.status = 'Assigned'
        sr.save()
        return Response(ServiceRequestSerializer(sr).data)

    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve_request(self, request, pk=None):
        sr = self.get_object()
        sr.status = 'Resolved'
        sr.closed_at = timezone.now()
        sr.save()
        return Response(ServiceRequestSerializer(sr).data)


class PreventiveMaintenancePlanViewSet(viewsets.ModelViewSet):
    queryset = PreventiveMaintenancePlan.objects.all()
    serializer_class = PreventiveMaintenancePlanSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['plan_number', 'asset_name', 'customer_name']
    filterset_fields = ['status', 'frequency', 'asset_id']


class BreakdownRecordViewSet(viewsets.ModelViewSet):
    queryset = BreakdownRecord.objects.all().order_by('-breakdown_date')
    serializer_class = BreakdownRecordSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['breakdown_number', 'asset_name', 'customer_name', 'serial_number']
    filterset_fields = ['status', 'severity', 'asset_type']

    @action(detail=True, methods=['post'], url_path='close')
    def close_breakdown(self, request, pk=None):
        bd = self.get_object()
        bd.status = 'Closed'
        bd.save()
        return Response({'message': f'Breakdown {bd.breakdown_number} closed', 'status': bd.status})


class ServiceVisitViewSet(viewsets.ModelViewSet):
    queryset = ServiceVisit.objects.all().order_by('-visit_date')
    serializer_class = ServiceVisitSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['visit_number', 'customer_name', 'machine_name', 'technician_name']
    filterset_fields = ['status', 'customer_id', 'service_request_id']


class AMCContractViewSet(viewsets.ModelViewSet):
    queryset = AMCContract.objects.all()
    serializer_class = AMCContractSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['amc_number', 'customer_name', 'machine_name', 'serial_number']
    filterset_fields = ['status', 'customer_id']

    @action(detail=True, methods=['post'], url_path='record-visit')
    def record_visit(self, request, pk=None):
        amc = self.get_object()
        amc.visits_completed += 1
        amc.save()
        return Response({
            'amcNumber': amc.amc_number,
            'visitsCompleted': amc.visits_completed,
            'totalVisitsIncluded': amc.total_visits_included
        })
