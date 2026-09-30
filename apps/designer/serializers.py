from rest_framework import serializers
from .models import (
    DesignJob,
    CustomerRequirement,
    Drawing2D,
    Design3DModel,
    AssemblyDrawing,
    BOMHeader,
    DesignRevisionLog,
    TechnicalDocumentItem,
    DesignTask,
)


class AssemblyDrawingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssemblyDrawing
        fields = '__all__'


class DesignTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignTask
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'designJobId' in data and 'design_job_id' not in data:
            data['design_job_id'] = data.pop('designJobId')
        if 'projectId' in data and 'project_id' not in data:
            data['project_id'] = data.pop('projectId')
        if 'jobNumber' in data and 'job_number' not in data:
            data['job_number'] = data.pop('jobNumber')
        if 'taskName' in data and 'task_name' not in data:
            data['task_name'] = data.pop('taskName')
        if 'customerName' in data and 'customer_name' not in data:
            data['customer_name'] = data.pop('customerName')
        if 'machineName' in data and 'machine_name' not in data:
            data['machine_name'] = data.pop('machineName')
        if 'startDate' in data and 'start_date' not in data:
            data['start_date'] = data.pop('startDate')
        if 'targetDate' in data and 'target_date' not in data:
            data['target_date'] = data.pop('targetDate')
        if 'dueDate' in data and 'due_date' not in data:
            data['due_date'] = data.pop('dueDate')
        if 'estimatedHours' in data and 'estimated_hours' not in data:
            data['estimated_hours'] = data.pop('estimatedHours')
        if 'actualHours' in data and 'actual_hours' not in data:
            data['actual_hours'] = data.pop('actualHours')
        if 'progressPercent' in data and 'progress_percent' not in data:
            data['progress_percent'] = data.pop('progressPercent')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {
            'id': ret.get('id'),
            'designJobId': ret.get('design_job_id', ''),
            'projectId': ret.get('project_id', ''),
            'jobNumber': ret.get('job_number', ''),
            'taskName': ret.get('task_name', ''),
            'customerName': ret.get('customer_name', ''),
            'machineName': ret.get('machine_name', ''),
            'designer': ret.get('designer', 'Dharmesh Joshi'),
            'startDate': ret.get('start_date', ''),
            'targetDate': ret.get('target_date', ''),
            'dueDate': ret.get('due_date', ''),
            'priority': ret.get('priority', 'high'),
            'estimatedHours': ret.get('estimated_hours', 16),
            'actualHours': ret.get('actual_hours', 0),
            'progressPercent': ret.get('progress_percent', 0),
            'status': ret.get('status', 'pending'),
            'remarks': ret.get('remarks', ''),
            'createdAt': ret.get('created_at', ''),
            'updatedAt': ret.get('updated_at', ''),
        }


class CustomerRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerRequirement
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'designJobId' in data and 'design_job_id' not in data:
            data['design_job_id'] = data.pop('designJobId')
        if 'projectId' in data and 'project_id' not in data:
            data['project_id'] = data.pop('projectId')
        if 'jobNumber' in data and 'job_number' not in data:
            data['job_number'] = data.pop('jobNumber')
        if 'customerName' in data and 'customer_name' not in data:
            data['customer_name'] = data.pop('customerName')
        if 'contactPerson' in data and 'contact_person' not in data:
            data['contact_person'] = data.pop('contactPerson')
        if 'contactMobile' in data and 'contact_mobile' not in data:
            data['contact_mobile'] = data.pop('contactMobile')
        if 'machineName' in data and 'machine_name' not in data:
            data['machine_name'] = data.pop('machineName')
        if 'machineType' in data and 'machine_type' not in data:
            data['machine_type'] = data.pop('machineType')
        if 'powerRequirement' in data and 'power_requirement' not in data:
            data['power_requirement'] = data.pop('powerRequirement')
        if 'productionRequirement' in data and 'production_requirement' not in data:
            data['production_requirement'] = data.pop('productionRequirement')
        if 'automationLevel' in data and 'automation_level' not in data:
            data['automation_level'] = data.pop('automationLevel')
        if 'controlSystem' in data and 'control_system' not in data:
            data['control_system'] = data.pop('controlSystem')
        if 'safetyRequirements' in data and 'safety_requirements' not in data:
            data['safety_requirements'] = data.pop('safetyRequirements')
        if 'specialRequirements' in data and 'special_requirements' not in data:
            data['special_requirements'] = data.pop('specialRequirements')
        if 'customerDrawingUrl' in data and 'customer_drawing_url' not in data:
            data['customer_drawing_url'] = data.pop('customerDrawingUrl')
        if 'customerNotes' in data and 'customer_notes' not in data:
            data['customer_notes'] = data.pop('customerNotes')
        if 'designerNotes' in data and 'designer_notes' not in data:
            data['designer_notes'] = data.pop('designerNotes')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {
            'id': ret.get('id'),
            'designJobId': ret.get('design_job_id', ''),
            'projectId': ret.get('project_id', ''),
            'jobNumber': ret.get('job_number', ''),
            'customerName': ret.get('customer_name', ''),
            'contactPerson': ret.get('contact_person', ''),
            'contactMobile': ret.get('contact_mobile', ''),
            'machineName': ret.get('machine_name', ''),
            'machineType': ret.get('machine_type', ''),
            'model': ret.get('model', ''),
            'quantity': ret.get('quantity', 1),
            'capacity': ret.get('capacity', ''),
            'application': ret.get('application', ''),
            'productionRequirement': ret.get('production_requirement', ''),
            'dimensions': ret.get('dimensions', ''),
            'material': ret.get('material', ''),
            'powerRequirement': ret.get('power_requirement', ''),
            'speed': ret.get('speed', ''),
            'output': ret.get('output', ''),
            'automationLevel': ret.get('automation_level', ''),
            'controlSystem': ret.get('control_system', ''),
            'safetyRequirements': ret.get('safety_requirements', ''),
            'specialRequirements': ret.get('special_requirements', ''),
            'customerDrawingUrl': ret.get('customer_drawing_url', ''),
            'customerNotes': ret.get('customer_notes', ''),
            'designerNotes': ret.get('designer_notes', ''),
            'status': 'approved',
            'createdAt': ret.get('created_at', ''),
        }


class Drawing2DSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drawing2D
        fields = [
            'id',
            'design_job_id',
            'drawing_number',
            'title',
            'revision',
            'status',
            'scale',
            'sheet_size',
            'prepared_by',
            'checked_by',
            'approved_by',
            'release_date',
            'file_url',
        ]


class Design3DModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Design3DModel
        fields = [
            'id',
            'design_job_id',
            'model_number',
            'model_name',
            'software',
            'version',
            'status',
            'mass_kg',
            'volume_m3',
            'modeled_by',
            'file_url',
        ]


class BOMHeaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOMHeader
        fields = [
            'id',
            'bom_number',
            'design_job_id',
            'project_id',
            'job_number',
            'active_revision',
            'status',
            'total_items',
            'total_weight_kg',
            'total_estimated_cost',
            'prepared_by',
            'approved_by',
            'release_date',
            'items',
            'revisions',
        ]


class DesignRevisionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignRevisionLog
        fields = [
            'id',
            'design_job_id',
            'revision_number',
            'reason',
            'changes_summary',
            'requested_by',
            'approved_by',
            'date',
        ]


class TechnicalDocumentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalDocumentItem
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'designJobId' in data and 'design_job_id' not in data:
            data['design_job_id'] = data.pop('designJobId')
        if 'projectId' in data and 'project_id' not in data:
            data['project_id'] = data.pop('projectId')
        if 'jobNumber' in data and 'job_number' not in data:
            data['job_number'] = data.pop('jobNumber')
        if 'docNumber' in data and 'doc_number' not in data:
            data['doc_number'] = data.pop('docNumber')
        if 'documentName' in data and 'document_name' not in data:
            data['document_name'] = data.pop('documentName')
            if 'title' not in data or not data['title']:
                data['title'] = data['document_name']
        if 'title' in data and ('document_name' not in data or not data['document_name']):
            data['document_name'] = data['title']
        if 'uploadedBy' in data and 'uploaded_by' not in data:
            data['uploaded_by'] = data.pop('uploadedBy')
        if 'uploadDate' in data and 'upload_date' not in data:
            data['upload_date'] = data.pop('uploadDate')
        if 'accessPermission' in data and 'access_permission' not in data:
            data['access_permission'] = data.pop('accessPermission')
        if 'fileSize' in data and 'file_size' not in data:
            data['file_size'] = data.pop('fileSize')
        if 'fileUrl' in data and 'file_url' not in data:
            data['file_url'] = data.pop('fileUrl')
        if 'createdDate' in data and 'created_date' not in data:
            data['created_date'] = data.pop('createdDate')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        doc_name = ret.get('document_name') or ret.get('title') or ret.get('doc_number') or ''
        return {
            'id': ret.get('id'),
            'designJobId': ret.get('design_job_id', ''),
            'projectId': ret.get('project_id', ''),
            'jobNumber': ret.get('job_number', ''),
            'docNumber': ret.get('doc_number', ret.get('id')),
            'documentName': doc_name,
            'title': doc_name,
            'category': ret.get('category', 'Calculation'),
            'version': ret.get('version', 'v1.0'),
            'revision': ret.get('revision', 'REV-00'),
            'uploadedBy': ret.get('uploaded_by', 'Dharmesh Joshi'),
            'uploadDate': ret.get('upload_date') or ret.get('created_date') or '',
            'accessPermission': ret.get('access_permission', 'public'),
            'fileSize': ret.get('file_size', '5.2 MB'),
            'fileUrl': ret.get('file_url', '#'),
            'createdAt': ret.get('created_at', ''),
        }


class DesignJobSerializer(serializers.ModelSerializer):
    requirement = CustomerRequirementSerializer(read_only=True)
    drawings = Drawing2DSerializer(many=True, read_only=True)
    models_3d = Design3DModelSerializer(many=True, read_only=True)
    boms = BOMHeaderSerializer(many=True, read_only=True)

    class Meta:
        model = DesignJob
        fields = [
            'id',
            'design_job_number',
            'project_id',
            'project_number',
            'job_number',
            'customer_id',
            'customer_name',
            'customer_po_number',
            'sales_order_number',
            'product_name',
            'machine_type',
            'quantity',
            'delivery_date',
            'design_manager',
            'assigned_designer',
            'priority',
            'required_date',
            'status',
            'remarks',
            'active_revision',
            'created_date',
            'requirement',
            'drawings',
            'models_3d',
            'boms',
        ]
