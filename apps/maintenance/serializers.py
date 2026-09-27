from rest_framework import serializers
from .models import (
    InternalAsset, CustomerMachine, ServiceRequest, PreventiveMaintenancePlan,
    BreakdownRecord, ServiceVisit, AMCContract
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
