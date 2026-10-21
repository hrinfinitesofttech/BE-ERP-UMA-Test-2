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

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'requestNumber': 'request_number',
            'requestDate': 'request_date',
            'customerId': 'customer_id',
            'customerName': 'customer_name',
            'contactNumber': 'contact_number',
            'homeAddress': 'home_address',
            'customerMachineId': 'customer_machine_id',
            'machineName': 'machine_name',
            'serialNumber': 'serial_number',
            'jobNumber': 'job_number',
            'contactPerson': 'contact_person',
            'requestType': 'request_type',
            'complaintType': 'complaint_type',
            'problemDescription': 'problem_description',
            'requestedDateTime': 'requested_datetime',
            'urgencyLevel': 'urgency_level',
            'applicantName': 'applicant_name',
            'requestSubmissionDate': 'request_submission_date',
            'completedBy': 'completed_by',
            'completedDate': 'completed_date',
            'approvedBy': 'approved_by',
            'approvedDate': 'approved_date',
            'warrantyStatus': 'warranty_status',
            'amcStatus': 'amc_status',
            'preferredVisitDate': 'preferred_visit_date',
            'assignedDepartment': 'assigned_department',
            'assignedTechnicianId': 'assigned_technician_id',
            'assignedTechnicianName': 'assigned_technician_name',
            'closedAt': 'closed_at',
            'createdAt': 'created_at',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)

        # Fallbacks for identifiers and mandatory fields
        if not data.get('request_number'):
            data['request_number'] = data.get('id') or f"SR-2026-{int(datetime.now().timestamp())}"
        if not data.get('id'):
            data['id'] = data['request_number']
        if not data.get('request_date'):
            data['request_date'] = datetime.now().date().isoformat()
        if not data.get('customer_name'):
            data['customer_name'] = data.get('applicant_name') or 'Customer'

        # Map mobile/location fallbacks if contact_number/home_address present
        if data.get('contact_number') and not data.get('mobile'):
            data['mobile'] = data['contact_number']
        if data.get('home_address') and not data.get('location'):
            data['location'] = data['home_address']

        # Empty strings to None for date/datetime fields
        date_fields = [
            'requested_datetime', 'request_submission_date', 'completed_date',
            'approved_date', 'preferred_visit_date', 'closed_at'
        ]
        for df in date_fields:
            if df in data and (data[df] == '' or data[df] is None):
                data[df] = None

        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['requestNumber'] = instance.request_number
        data['requestDate'] = str(instance.request_date) if instance.request_date else ''
        data['customerId'] = instance.customer_id
        data['customerName'] = instance.customer_name
        data['contactNumber'] = instance.contact_number or instance.mobile or ''
        data['homeAddress'] = instance.home_address or instance.location or ''
        data['customerMachineId'] = instance.customer_machine_id
        data['machineName'] = instance.machine_name
        data['serialNumber'] = instance.serial_number
        data['jobNumber'] = instance.job_number
        data['contactPerson'] = instance.contact_person
        data['requestType'] = instance.request_type or 'Repair'
        data['complaintType'] = instance.complaint_type
        data['problemDescription'] = instance.problem_description or instance.description
        data['requestedDateTime'] = str(instance.requested_datetime) if instance.requested_datetime else ''
        data['urgencyLevel'] = instance.urgency_level or instance.priority or 'Medium'
        data['applicantName'] = instance.applicant_name or instance.contact_person or instance.customer_name
        data['requestSubmissionDate'] = str(instance.request_submission_date) if instance.request_submission_date else (str(instance.request_date) if instance.request_date else '')
        data['completedBy'] = instance.completed_by or ''
        data['completedDate'] = str(instance.completed_date) if instance.completed_date else ''
        data['approvedBy'] = instance.approved_by or ''
        data['approvedDate'] = str(instance.approved_date) if instance.approved_date else ''
        data['warrantyStatus'] = instance.warranty_status
        data['amcStatus'] = instance.amc_status
        data['preferredVisitDate'] = str(instance.preferred_visit_date) if instance.preferred_visit_date else ''
        data['assignedDepartment'] = instance.assigned_department
        data['assignedTechnicianId'] = instance.assigned_technician_id
        data['assignedTechnicianName'] = instance.assigned_technician_name
        data['createdAt'] = str(instance.created_at) if instance.created_at else ''
        data['closedAt'] = str(instance.closed_at) if instance.closed_at else ''
        return data


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
