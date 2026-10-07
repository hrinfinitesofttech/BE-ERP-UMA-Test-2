from datetime import datetime
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

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'customerMachineId': 'customer_machine_id',
            'customerId': 'customer_id',
            'customerName': 'customer_name',
            'projectId': 'project_id',
            'projectName': 'project_name',
            'jobId': 'job_id',
            'jobNumber': 'job_number',
            'salesOrderId': 'sales_order_id',
            'customerPo': 'customer_po',
            'dispatchNumber': 'dispatch_number',
            'installationNumber': 'installation_number',
            'machineName': 'machine_name',
            'machineModel': 'machine_model',
            'serialNumber': 'serial_number',
            'manufacturingDate': 'manufacturing_date',
            'installationDate': 'installation_date',
            'commissioningDate': 'commissioning_date',
            'warrantyStart': 'warranty_start',
            'warrantyEnd': 'warranty_end',
            'machineLocation': 'machine_location',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if not data.get('customer_machine_id'):
            data['customer_machine_id'] = data.get('id') or f"CM-{int(datetime.now().timestamp())}"
        if not data.get('id'):
            data['id'] = data['customer_machine_id']
        return super().to_internal_value(data)


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
