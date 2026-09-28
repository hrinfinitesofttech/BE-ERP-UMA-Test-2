from rest_framework import serializers
from .models import (
    InternalAsset, CustomerMachine, ServiceRequest, PreventiveMaintenancePlan,
    BreakdownRecord, ServiceVisit, AMCContract, ServiceWorkOrder,
    ServicePartIssue, ServicePartReturn, ServiceReport, WarrantyRecord,
    ServiceContract, DowntimeRecord
)


class InternalAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternalAsset
        fields = '__all__'


class CustomerMachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerMachine
        fields = '__all__'


class ServiceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = '__all__'


class PreventiveMaintenancePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreventiveMaintenancePlan
        fields = '__all__'


class BreakdownRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreakdownRecord
        fields = '__all__'


class ServiceVisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceVisit
        fields = '__all__'


class AMCContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = AMCContract
        fields = '__all__'


class ServiceWorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceWorkOrder
        fields = '__all__'


class ServicePartIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePartIssue
        fields = '__all__'


class ServicePartReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePartReturn
        fields = '__all__'


class ServiceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceReport
        fields = '__all__'


class WarrantyRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarrantyRecord
        fields = '__all__'


class ServiceContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceContract
        fields = '__all__'


class DowntimeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DowntimeRecord
        fields = '__all__'
