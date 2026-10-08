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

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'designJobId' in data and 'design_job_id' not in data:
            data['design_job_id'] = data.pop('designJobId')
        if 'drawingNumber' in data and 'drawing_number' not in data:
            data['drawing_number'] = data.pop('drawingNumber')
        if 'drawingTitle' in data and 'title' not in data:
            data['title'] = data.pop('drawingTitle')
        if 'sheetSize' in data and 'sheet_size' not in data:
            data['sheet_size'] = data.pop('sheetSize')
        if 'preparedBy' in data and 'prepared_by' not in data:
            data['prepared_by'] = data.pop('preparedBy')
        elif 'drawnBy' in data and 'prepared_by' not in data:
            data['prepared_by'] = data.pop('drawnBy')
        if 'checkedBy' in data and 'checked_by' not in data:
            data['checked_by'] = data.pop('checkedBy')
        if 'approvedBy' in data and 'approved_by' not in data:
            data['approved_by'] = data.pop('approvedBy')
        if 'releaseDate' in data and 'release_date' not in data:
            data['release_date'] = data.pop('releaseDate')
        if 'fileUrl' in data and 'file_url' not in data:
            data['file_url'] = data.pop('fileUrl')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {
            **ret,
            'designJobId': ret.get('design_job_id', ''),
            'drawingNumber': ret.get('drawing_number', ''),
            'drawingTitle': ret.get('title', ''),
            'sheetSize': ret.get('sheet_size', 'A1'),
            'preparedBy': ret.get('prepared_by', 'Dharmesh Joshi'),
            'drawnBy': ret.get('prepared_by', 'Dharmesh Joshi'),
            'checkedBy': ret.get('checked_by', ''),
            'approvedBy': ret.get('approved_by', ''),
            'releaseDate': ret.get('release_date', ''),
            'fileUrl': ret.get('file_url', ''),
        }


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

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'designJobId' in data and 'design_job_id' not in data:
            data['design_job_id'] = data.pop('designJobId')
        if 'modelNumber' in data and 'model_number' not in data:
            data['model_number'] = data.pop('modelNumber')
        elif 'designNumber' in data and 'model_number' not in data:
            data['model_number'] = data.pop('designNumber')
        if 'modelName' in data and 'model_name' not in data:
            data['model_name'] = data.pop('modelName')
        elif 'modelTitle' in data and 'model_name' not in data:
            data['model_name'] = data.pop('modelTitle')
        if 'massKg' in data and 'mass_kg' not in data:
            data['mass_kg'] = data.pop('massKg')
        elif 'totalWeightKg' in data and 'mass_kg' not in data:
            data['mass_kg'] = data.pop('totalWeightKg')
        if 'volumeM3' in data and 'volume_m3' not in data:
            data['volume_m3'] = data.pop('volumeM3')
        if 'modeledBy' in data and 'modeled_by' not in data:
            data['modeled_by'] = data.pop('modeledBy')
        elif 'designer' in data and 'modeled_by' not in data:
            data['modeled_by'] = data.pop('designer')
        if 'fileUrl' in data and 'file_url' not in data:
            data['file_url'] = data.pop('fileUrl')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {
            **ret,
            'designJobId': ret.get('design_job_id', ''),
            'modelNumber': ret.get('model_number', ''),
            'modelName': ret.get('model_name', ''),
            'massKg': ret.get('mass_kg', 0),
            'volumeM3': ret.get('volume_m3', 0),
            'modeledBy': ret.get('modeled_by', 'Dharmesh Joshi'),
            'designer': ret.get('modeled_by', 'Dharmesh Joshi'),
            'fileUrl': ret.get('file_url', ''),
        }


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

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'bomNumber' in data and 'bom_number' not in data:
            data['bom_number'] = data.pop('bomNumber')
        if 'designJobId' in data and 'design_job_id' not in data:
            data['design_job_id'] = data.pop('designJobId')
        if 'projectId' in data and 'project_id' not in data:
            data['project_id'] = data.pop('projectId')
        if 'project' in data and 'project_id' not in data:
            data['project_id'] = data.pop('project')
        if not data.get('bom_number'):
            data['bom_number'] = data.get('id') or f"BOM-{int(datetime.now().timestamp())}"
        if not data.get('id'):
            data['id'] = data['bom_number']
        if 'jobNumber' in data and 'job_number' not in data:
            data['job_number'] = data.pop('jobNumber')
        if 'activeRevision' in data and 'active_revision' not in data:
            data['active_revision'] = data.pop('activeRevision')
        if 'totalItems' in data and 'total_items' not in data:
            data['total_items'] = data.pop('totalItems')
        if 'totalWeightKg' in data and 'total_weight_kg' not in data:
            data['total_weight_kg'] = data.pop('totalWeightKg')
        if 'totalEstimatedCost' in data and 'total_estimated_cost' not in data:
            data['total_estimated_cost'] = data.pop('totalEstimatedCost')
        if 'preparedBy' in data and 'prepared_by' not in data:
            data['prepared_by'] = data.pop('preparedBy')
        if 'approvedBy' in data and 'approved_by' not in data:
            data['approved_by'] = data.pop('approvedBy')
        if 'releaseDate' in data and 'release_date' not in data:
            data['release_date'] = data.pop('releaseDate')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        items = ret.get('items') or []
        normalized_items = []
        total_cost = 0.0
        for idx, itm in enumerate(items):
            if isinstance(itm, dict):
                rate = float(
                    itm.get('estimatedRate') or itm.get('estimated_rate') or
                    itm.get('rate') or itm.get('unitPrice') or itm.get('unit_price') or
                    itm.get('unitCost') or itm.get('unit_cost') or itm.get('est_rate') or
                    itm.get('estRate') or itm.get('costPerUnit') or 0.0
                )
                qty = float(itm.get('quantity') or itm.get('qty') or 1.0)
                total_amt = float(
                    itm.get('totalEstimatedAmount') or itm.get('total_estimated_amount') or
                    itm.get('total_amount') or itm.get('totalAmount') or
                    itm.get('extendedCost') or itm.get('extended_cost') or (qty * rate)
                )
                total_cost += total_amt
                item_name = itm.get('itemName') or itm.get('item_name') or itm.get('partName') or itm.get('materialName') or itm.get('material') or f"Component {idx+1}"
                part_num = itm.get('partNumber') or itm.get('part_number') or itm.get('itemCode') or itm.get('item_code') or f"MAT-{idx+1:03d}"

                normalized_items.append({
                    **itm,
                    'itemNo': itm.get('itemNo') or idx + 1,
                    'itemNumber': itm.get('itemNumber') or f"ITM-{idx+1:03d}",
                    'partNumber': part_num,
                    'part_number': part_num,
                    'itemName': item_name,
                    'item_name': item_name,
                    'partName': item_name,
                    'description': itm.get('description') or itm.get('specification') or '',
                    'specification': itm.get('specification') or itm.get('description') or '',
                    'material': itm.get('material') or item_name,
                    'item_type': itm.get('item_type') or itm.get('itemType') or 'RAW_MATERIAL',
                    'itemType': itm.get('itemType') or itm.get('item_type') or 'RAW_MATERIAL',
                    'procurement': itm.get('procurement') or ('FABRICATE' if itm.get('procurementType') == 'In-House' else 'PURCHASE'),
                    'procurementType': itm.get('procurementType') or ('In-House' if itm.get('procurement') == 'FABRICATE' else 'Purchase'),
                    'quantity': qty,
                    'qty': qty,
                    'unit': itm.get('unit') or 'PCS',
                    'estimatedRate': rate,
                    'estimated_rate': rate,
                    'rate': rate,
                    'unitCost': rate,
                    'unit_price': rate,
                    'totalEstimatedAmount': total_amt,
                    'total_amount': total_amt,
                    'total_estimated_amount': total_amt,
                    'totalAmount': total_amt,
                    'extendedCost': total_amt,
                })
            else:
                normalized_items.append(itm)
        
        calc_total_cost = float(ret.get('total_estimated_cost') or total_cost)
        return {
            **ret,
            'items': normalized_items,
            'bomNumber': ret.get('bom_number', ''),
            'designJobId': ret.get('design_job_id', ''),
            'projectId': ret.get('project_id', ''),
            'jobNumber': ret.get('job_number', ''),
            'activeRevision': ret.get('active_revision', 'REV-00'),
            'totalItems': ret.get('total_items', len(normalized_items)),
            'totalWeightKg': ret.get('total_weight_kg', 0),
            'totalEstimatedCost': calc_total_cost,
            'estimatedTotalCost': calc_total_cost,
            'preparedBy': ret.get('prepared_by', 'Dharmesh Joshi'),
            'approvedBy': ret.get('approved_by', ''),
            'releaseDate': ret.get('release_date', ''),
        }


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

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'designJobId' in data and 'design_job_id' not in data:
            data['design_job_id'] = data.pop('designJobId')
        if 'revisionNumber' in data and 'revision_number' not in data:
            data['revision_number'] = data.pop('revisionNumber')
        if 'changesSummary' in data and 'changes_summary' not in data:
            data['changes_summary'] = data.pop('changesSummary')
        if 'requestedBy' in data and 'requested_by' not in data:
            data['requested_by'] = data.pop('requestedBy')
        if 'approvedBy' in data and 'approved_by' not in data:
            data['approved_by'] = data.pop('approvedBy')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {
            **ret,
            'designJobId': ret.get('design_job_id', ''),
            'revisionNumber': ret.get('revision_number', ''),
            'changesSummary': ret.get('changes_summary', ''),
            'requestedBy': ret.get('requested_by', ''),
            'approvedBy': ret.get('approved_by', ''),
        }


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
        if 'project' in data and 'project_id' not in data:
            data['project_id'] = data.pop('project')
        if 'jobNumber' in data and 'job_number' not in data:
            data['job_number'] = data.pop('jobNumber')
        if 'docNumber' in data and 'doc_number' not in data:
            data['doc_number'] = data.pop('docNumber')
        if 'documentNumber' in data and 'doc_number' not in data:
            data['doc_number'] = data.pop('documentNumber')
        if not data.get('doc_number'):
            data['doc_number'] = data.get('id') or f"DOC-{int(datetime.now().timestamp())}"
        if not data.get('id'):
            data['id'] = data['doc_number']
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
            'approved_by',
            'approved_date',
            'disapproved_by',
            'disapproved_date',
            'rejection_reason',
            'approval_notes',
            'created_date',
            'requirement',
            'drawings',
            'models_3d',
            'boms',
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'designJobNumber': 'design_job_number',
            'projectId': 'project_id',
            'projectNumber': 'project_number',
            'jobNumber': 'job_number',
            'customerId': 'customer_id',
            'customerName': 'customer_name',
            'customerPoNumber': 'customer_po_number',
            'salesOrderNumber': 'sales_order_number',
            'productName': 'product_name',
            'machineType': 'machine_type',
            'deliveryDate': 'delivery_date',
            'designManager': 'design_manager',
            'assignedDesigner': 'assigned_designer',
            'requiredDate': 'required_date',
            'activeRevision': 'active_revision',
            'approvedBy': 'approved_by',
            'approvedDate': 'approved_date',
            'disapprovedBy': 'disapproved_by',
            'disapprovedDate': 'disapproved_date',
            'rejectionReason': 'rejection_reason',
            'approvalNotes': 'approval_notes',
            'createdDate': 'created_date',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {
            **ret,
            'designJobNumber': ret.get('design_job_number', ret.get('id', '')),
            'projectId': ret.get('project_id', ''),
            'projectNumber': ret.get('project_number', ''),
            'jobNumber': ret.get('job_number', ''),
            'customerId': ret.get('customer_id', ''),
            'customerName': ret.get('customer_name', ''),
            'customerPoNumber': ret.get('customer_po_number', ''),
            'salesOrderNumber': ret.get('sales_order_number', ''),
            'productName': ret.get('product_name', ''),
            'machineType': ret.get('machine_type', ''),
            'deliveryDate': ret.get('delivery_date', ''),
            'designManager': ret.get('design_manager', 'Dharmesh Joshi'),
            'assignedDesigner': ret.get('assigned_designer', 'Dharmesh Joshi'),
            'requiredDate': ret.get('required_date', ''),
            'activeRevision': ret.get('active_revision', 'REV-00'),
            'approvedBy': ret.get('approved_by', ''),
            'approvedDate': ret.get('approved_date', ''),
            'disapprovedBy': ret.get('disapproved_by', ''),
            'disapprovedDate': ret.get('disapproved_date', ''),
            'rejectionReason': ret.get('rejection_reason', ''),
            'approvalNotes': ret.get('approval_notes', ''),
            'createdDate': ret.get('created_date', ''),
        }
