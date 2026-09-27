from rest_framework import serializers
from .models import (
    DesignJob,
    CustomerRequirement,
    Drawing2D,
    Design3DModel,
    BOMHeader,
    DesignRevisionLog,
    TechnicalDocumentItem,
)


class CustomerRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerRequirement
        fields = [
            'id',
            'design_job_id',
            'project_id',
            'job_number',
            'customer_name',
            'contact_person',
            'contact_mobile',
            'machine_name',
            'machine_type',
            'model',
            'quantity',
            'capacity',
            'application',
            'production_requirement',
            'dimensions',
            'material',
            'power_requirement',
            'speed',
            'output',
            'automation_level',
            'control_system',
            'safety_requirements',
            'special_requirements',
            'customer_drawing_url',
            'customer_notes',
            'designer_notes',
        ]


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
        fields = [
            'id',
            'design_job_id',
            'doc_number',
            'title',
            'category',
            'file_url',
            'created_date',
        ]


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
