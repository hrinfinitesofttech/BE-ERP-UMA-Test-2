from datetime import datetime, date
from rest_framework import serializers
from apps.core.base_serializers import UniversalModelSerializerMixin
from .models import (
    ManufacturingJob, ProductionPlan, WorkCenter, RoutingOperation,
    WorkOrder, ProductionOrder, ProductionScheduleItem, ProductionEntry,
    WIPRecord, ProductionHold, ReworkOrder, ProductionScrap, FinishedGoodsItem,
    ProductionMaterialRequest, DispatchOrder, PackingOrder
)


class ManufacturingJobSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ManufacturingJob
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'salesOrder' in data and not data.get('sales_order_id'):
            data['sales_order_id'] = data.pop('salesOrder')
        if 'salesOrderId' in data and not data.get('sales_order_id'):
            data['sales_order_id'] = data.pop('salesOrderId')
        if 'project' in data and not data.get('project_id'):
            data['project_id'] = data.pop('project')
        if 'projectId' in data and not data.get('project_id'):
            data['project_id'] = data.pop('projectId')
        if not data.get('job_number'):
            data['job_number'] = data.get('jobNumber') or data.get('jobCardNumber') or data.get('id') or f"JOB-{int(datetime.now().timestamp())}"
        if not data.get('product_name'):
            data['product_name'] = data.get('productName') or 'Industrial Process Equipment'
        if not data.get('quantity'):
            data['quantity'] = data.get('targetQuantity') or data.get('completedQuantity') or 1
        if not data.get('planned_start_date') and not data.get('plannedStartDate'):
            data['planned_start_date'] = data.get('startDate') or datetime.now().date().isoformat()
        if not data.get('planned_completion_date') and not data.get('plannedCompletionDate'):
            data['planned_completion_date'] = data.get('plannedEndDate') or data.get('completionDate')
        if not data.get('id'):
            data['id'] = data.get('job_number')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['jobNumber'] = instance.job_number
        data['projectId'] = instance.project_id
        data['projectNumber'] = instance.project_number
        data['customerId'] = instance.customer_id
        data['customerName'] = instance.customer_name
        data['salesOrderId'] = instance.sales_order_id
        data['salesOrderNumber'] = instance.sales_order_number
        data['customerPoNumber'] = instance.customer_po_number
        data['productName'] = instance.product_name
        data['designId'] = instance.design_id
        data['designRevision'] = instance.design_revision
        data['bomId'] = instance.bom_id
        data['bomRevision'] = instance.bom_revision
        data['projectManager'] = instance.project_manager
        data['productionManager'] = instance.production_manager
        data['plannedStartDate'] = str(instance.planned_start_date) if instance.planned_start_date else ''
        data['plannedCompletionDate'] = str(instance.planned_completion_date) if instance.planned_completion_date else ''
        data['actualStartDate'] = str(instance.actual_start_date) if instance.actual_start_date else ''
        data['actualCompletionDate'] = str(instance.actual_completion_date) if instance.actual_completion_date else ''
        data['productionProgress'] = instance.production_progress
        return data


class ProductionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionPlan
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['planNumber'] = instance.plan_number
        data['jobId'] = instance.job_id
        data['jobNumber'] = instance.job_number
        data['projectId'] = instance.project_id
        data['productName'] = instance.product_name
        data['requiredQuantity'] = float(instance.required_quantity or 0)
        data['bomId'] = instance.bom_id
        data['bomRevision'] = instance.bom_revision
        data['materialAvailabilityStatus'] = instance.material_availability_status
        data['plannedStartDate'] = str(instance.planned_start_date) if instance.planned_start_date else ''
        data['plannedCompletionDate'] = str(instance.planned_completion_date) if instance.planned_completion_date else ''
        data['assignedWorkCenters'] = instance.assigned_work_centers
        data['plannedManpowerCount'] = instance.planned_manpower_count
        data['productionManager'] = instance.production_manager
        return data


class WorkCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkCenter
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['workCenterCode'] = instance.work_center_code
        data['workCenterName'] = instance.work_center_name
        data['machineName'] = instance.machine_name
        data['machineNumber'] = instance.machine_number
        data['capacityPerDayHours'] = float(instance.capacity_per_day_hours or 8)
        data['availableHours'] = float(instance.available_hours or 8)
        data['efficiencyPercent'] = float(instance.efficiency_percent or 100)
        data['supervisorName'] = instance.supervisor_name
        return data


class RoutingOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingOperation
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['operationNumber'] = instance.operation_number
        data['operationName'] = instance.operation_name
        data['workCenterCode'] = instance.work_center_code
        data['workCenterName'] = instance.work_center_name
        data['machineName'] = instance.machine_name
        data['plannedSetupMinutes'] = instance.planned_setup_minutes
        data['plannedProcessingMinutes'] = instance.planned_processing_minutes
        data['totalPlannedMinutes'] = instance.total_planned_minutes
        data['assignedOperator'] = instance.assigned_operator
        data['qcRequired'] = instance.qc_required
        return data


class WorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'workOrderNumber': 'work_order_number',
            'jobId': 'job_id',
            'jobNumber': 'job_number',
            'projectId': 'project_id',
            'customerId': 'customer_id',
            'customerName': 'customer_name',
            'salesOrderNumber': 'sales_order_number',
            'designRevision': 'design_revision',
            'bomRevision': 'bom_revision',
            'productName': 'product_name',
            'productionQuantity': 'production_quantity',
            'plannedStartDate': 'planned_start_date',
            'plannedEndDate': 'planned_end_date',
            'actualStartDate': 'actual_start_date',
            'actualEndDate': 'actual_end_date',
            'productionManager': 'production_manager',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if not data.get('work_order_number'):
            data['work_order_number'] = data.get('id') or f"WO-{int(datetime.now().timestamp())}"
        if not data.get('id'):
            data['id'] = data['work_order_number']
        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['workOrderNumber'] = instance.work_order_number
        data['jobId'] = instance.job_id
        data['jobNumber'] = instance.job_number
        data['projectId'] = instance.project_id
        data['customerId'] = instance.customer_id
        data['customerName'] = instance.customer_name
        data['salesOrderNumber'] = instance.sales_order_number
        data['designRevision'] = instance.design_revision
        data['bomRevision'] = instance.bom_revision
        data['productName'] = instance.product_name
        data['productionQuantity'] = float(instance.production_quantity or 1)
        data['plannedStartDate'] = str(instance.planned_start_date) if instance.planned_start_date else ''
        data['plannedEndDate'] = str(instance.planned_end_date) if instance.planned_end_date else ''
        data['actualStartDate'] = str(instance.actual_start_date) if instance.actual_start_date else ''
        data['actualEndDate'] = str(instance.actual_end_date) if instance.actual_end_date else ''
        data['productionManager'] = instance.production_manager
        return data


class ProductionOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrder
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['productionOrderNumber'] = instance.production_order_number
        data['workOrderId'] = instance.work_order_id
        data['workOrderNumber'] = instance.work_order_number
        data['jobId'] = instance.job_id
        data['jobNumber'] = instance.job_number
        data['productName'] = instance.product_name
        data['bomRevision'] = instance.bom_revision
        data['designRevision'] = instance.design_revision
        data['plannedStartDate'] = str(instance.planned_start_date) if instance.planned_start_date else ''
        data['plannedEndDate'] = str(instance.planned_end_date) if instance.planned_end_date else ''
        data['actualStartDate'] = str(instance.actual_start_date) if instance.actual_start_date else ''
        data['actualEndDate'] = str(instance.actual_end_date) if instance.actual_end_date else ''
        data['productionManager'] = instance.production_manager
        return data


class ProductionScheduleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionScheduleItem
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['scheduleNumber'] = instance.schedule_number
        data['jobId'] = instance.job_id
        data['jobNumber'] = instance.job_number
        data['workOrderNumber'] = instance.work_order_number
        data['operationName'] = instance.operation_name
        data['workCenterCode'] = instance.work_center_code
        data['workCenterName'] = instance.work_center_name
        data['machineName'] = instance.machine_name
        data['assignedOperator'] = instance.assigned_operator
        data['plannedStart'] = str(instance.planned_start) if instance.planned_start else ''
        data['plannedEnd'] = str(instance.planned_end) if instance.planned_end else ''
        data['actualStart'] = str(instance.actual_start) if instance.actual_start else ''
        data['actualEnd'] = str(instance.actual_end) if instance.actual_end else ''
        data['delayHours'] = float(instance.delay_hours or 0)
        return data


class ProductionEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionEntry
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'productionEntryNumber': 'production_entry_number',
            'entryDate': 'entry_date',
            'jobId': 'job_id',
            'jobNumber': 'job_number',
            'workOrderNumber': 'work_order_number',
            'productionOrderNumber': 'production_order_number',
            'operationName': 'operation_name',
            'workCenterName': 'work_center_name',
            'machineName': 'machine_name',
            'operatorName': 'operator_name',
            'startTime': 'start_time',
            'endTime': 'end_time',
            'plannedQuantity': 'planned_quantity',
            'producedQuantity': 'produced_quantity',
            'rejectedQuantity': 'rejected_quantity',
            'reworkQuantity': 'rework_quantity',
            'scrapQuantity': 'scrap_quantity',
            'goodQuantity': 'good_quantity',
            'downtimeMinutes': 'downtime_minutes',
            'downtimeReason': 'downtime_reason',
            'createdBy': 'created_by',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if not data.get('production_entry_number'):
            data['production_entry_number'] = data.get('id') or f"PENTRY-{int(datetime.now().timestamp())}"
        if not data.get('id'):
            data['id'] = data['production_entry_number']
        if not data.get('entry_date'):
            data['entry_date'] = datetime.now().date().isoformat()
        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['productionEntryNumber'] = instance.production_entry_number
        data['entryDate'] = str(instance.entry_date)
        data['jobId'] = instance.job_id
        data['jobNumber'] = instance.job_number
        data['workOrderNumber'] = instance.work_order_number
        data['productionOrderNumber'] = instance.production_order_number
        data['operationName'] = instance.operation_name
        data['workCenterName'] = instance.work_center_name
        data['machineName'] = instance.machine_name
        data['operatorName'] = instance.operator_name
        data['startTime'] = instance.start_time
        data['endTime'] = instance.end_time
        data['plannedQuantity'] = float(instance.planned_quantity or 0)
        data['producedQuantity'] = float(instance.produced_quantity or 0)
        data['rejectedQuantity'] = float(instance.rejected_quantity or 0)
        data['reworkQuantity'] = float(instance.rework_quantity or 0)
        data['scrapQuantity'] = float(instance.scrap_quantity or 0)
        data['goodQuantity'] = float(instance.good_quantity or 0)
        data['downtimeMinutes'] = instance.downtime_minutes
        data['downtimeReason'] = instance.downtime_reason
        data['createdBy'] = instance.created_by
        return data


class WIPRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = WIPRecord
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['jobId'] = instance.job_id
        data['jobNumber'] = instance.job_number
        data['workOrderNumber'] = instance.work_order_number
        data['productionOrderNumber'] = instance.production_order_number
        data['currentOperationName'] = instance.current_operation_name
        data['completedOperationsCount'] = instance.completed_operations_count
        data['totalOperationsCount'] = instance.total_operations_count
        data['wipQuantity'] = float(instance.wip_quantity or 0)
        data['responsibleDepartment'] = instance.responsible_department
        data['startDate'] = str(instance.start_date) if instance.start_date else ''
        data['expectedCompletionDate'] = str(instance.expected_completion_date) if instance.expected_completion_date else ''
        data['delayDays'] = instance.delay_days
        return data


class ProductionHoldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionHold
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['holdNumber'] = instance.hold_number
        data['jobId'] = instance.job_id
        data['jobNumber'] = instance.job_number
        data['workOrderNumber'] = instance.work_order_number
        data['operationName'] = instance.operation_name
        data['startDate'] = str(instance.start_date) if instance.start_date else ''
        data['expectedResumeDate'] = str(instance.expected_resume_date) if instance.expected_resume_date else ''
        data['approvedBy'] = instance.approved_by
        data['resumeDate'] = str(instance.resume_date) if instance.resume_date else ''
        return data


class ReworkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReworkOrder
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['reworkNumber'] = instance.rework_number
        data['jobId'] = instance.job_id
        data['jobNumber'] = instance.job_number
        data['workOrderNumber'] = instance.work_order_number
        data['productionEntryNumber'] = instance.production_entry_number
        data['operationName'] = instance.operation_name
        data['itemCode'] = instance.item_code
        data['itemName'] = instance.item_name
        data['quantity'] = float(instance.quantity or 0)
        data['responsibleDepartment'] = instance.responsible_department
        data['reworkInstructions'] = instance.rework_instructions
        data['assignedOperator'] = instance.assigned_operator
        data['startDate'] = str(instance.start_date) if instance.start_date else ''
        data['completionDate'] = str(instance.completion_date) if instance.completion_date else ''
        return data


class ProductionScrapSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionScrap
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['scrapNumber'] = instance.scrap_number
        data['entryDate'] = str(instance.entry_date)
        data['jobId'] = instance.job_id
        data['jobNumber'] = instance.job_number
        data['workOrderNumber'] = instance.work_order_number
        data['productionOrderNumber'] = instance.production_order_number
        data['operationName'] = instance.operation_name
        data['materialCode'] = instance.material_code
        data['materialName'] = instance.material_name
        data['quantity'] = float(instance.quantity or 0)
        data['scrapType'] = instance.scrap_type
        data['operatorName'] = instance.operator_name
        data['estimatedValue'] = float(instance.estimated_value or 0)
        return data


class FinishedGoodsItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinishedGoodsItem
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'finishedGoodsNumber': 'finished_goods_number',
            'jobId': 'job_id',
            'jobNumber': 'job_number',
            'workOrderNumber': 'work_order_number',
            'productionOrderNumber': 'production_order_number',
            'productName': 'product_name',
            'serialNumber': 'serial_number',
            'batchNumber': 'batch_number',
            'warehouseId': 'warehouse_id',
            'warehouseName': 'warehouse_name',
            'locationBin': 'location_bin',
            'completionDate': 'completion_date',
            'qcStatus': 'qc_status',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if not data.get('finished_goods_number'):
            data['finished_goods_number'] = data.get('id') or f"FG-{int(datetime.now().timestamp())}"
        if not data.get('id'):
            data['id'] = data['finished_goods_number']
        if not data.get('completion_date'):
            data['completion_date'] = datetime.now().date().isoformat()
        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['finishedGoodsNumber'] = instance.finished_goods_number
        data['jobId'] = instance.job_id
        data['jobNumber'] = instance.job_number
        data['workOrderNumber'] = instance.work_order_number
        data['productionOrderNumber'] = instance.production_order_number
        data['productName'] = instance.product_name
        data['serialNumber'] = instance.serial_number
        data['batchNumber'] = instance.batch_number
        data['warehouseId'] = instance.warehouse_id
        data['warehouseName'] = instance.warehouse_name
        data['locationBin'] = instance.location_bin
        data['completionDate'] = str(instance.completion_date) if instance.completion_date else ''
        data['qcStatus'] = instance.qc_status
        return data


class ProductionMaterialRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionMaterialRequest
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['requestNumber'] = instance.request_number
        data['issueNumber'] = instance.request_number
        data['projectId'] = instance.project_id
        data['jobId'] = instance.job_id
        data['jobNumber'] = instance.job_number
        data['workOrderNumber'] = instance.work_order_number
        data['bomNumber'] = instance.bom_number
        data['bomRevision'] = instance.bom_revision
        data['productionStage'] = instance.production_stage
        data['requestedBy'] = instance.requested_by
        data['issuedTo'] = instance.issued_to
        data['issuedBy'] = instance.issued_by
        data['requestDate'] = str(instance.request_date) if instance.request_date else ''
        data['issueDate'] = str(instance.request_date) if instance.request_date else ''
        data['warehouseId'] = instance.warehouse_id
        data['warehouseName'] = instance.warehouse_name
        data['totalValue'] = float(instance.total_value or 0)
        data['totalIssueValue'] = float(instance.total_value or 0)
        data['items'] = instance.items or []
        data['status'] = instance.status
        data['remarks'] = instance.remarks
        return data


class DispatchOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispatchOrder
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'dispatchNumber': 'dispatch_number',
            'dispatchDate': 'dispatch_date',
            'jobId': 'job_id',
            'jobNumber': 'job_number',
            'salesOrderNumber': 'sales_order_number',
            'workOrderNumber': 'work_order_number',
            'finishedGoodsNumber': 'finished_goods_number',
            'customerId': 'customer_id',
            'customerName': 'customer_name',
            'customerAddress': 'customer_address',
            'destinationCity': 'destination_city',
            'productName': 'product_name',
            'serialNumber': 'serial_number',
            'batchNumber': 'batch_number',
            'weightMT': 'weight_mt',
            'transporterName': 'transporter_name',
            'vehicleNumber': 'vehicle_number',
            'lrNumber': 'lr_number',
            'driverName': 'driver_name',
            'driverMobile': 'driver_mobile',
            'eWayBillNumber': 'e_way_bill_number',
            'invoiceNumber': 'invoice_number',
            'packagingType': 'packaging_type',
            'dispatchType': 'dispatch_type',
            'qcClearanceBy': 'qc_clearance_by',
            'dispatchedBy': 'dispatched_by',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if not data.get('dispatch_number'):
            data['dispatch_number'] = data.get('id') or f"DISP-{int(datetime.now().timestamp())}"
        if not data.get('dispatch_date'):
            data['dispatch_date'] = datetime.now().date().isoformat()
        if not data.get('customer_name'):
            data['customer_name'] = data.get('customerName') or data.get('company_name') or 'Valued Customer'
        if not data.get('product_name'):
            data['product_name'] = data.get('productName') or 'Industrial Process Equipment'
        if not data.get('id'):
            data['id'] = data['dispatch_number']
        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['dispatchNumber'] = instance.dispatch_number
        data['dispatchDate'] = str(instance.dispatch_date) if instance.dispatch_date else ''
        data['jobId'] = instance.job_id
        data['jobNumber'] = instance.job_number
        data['salesOrderNumber'] = instance.sales_order_number
        data['workOrderNumber'] = instance.work_order_number
        data['finishedGoodsNumber'] = instance.finished_goods_number
        data['customerId'] = instance.customer_id
        data['customerName'] = instance.customer_name
        data['customerAddress'] = instance.customer_address
        data['destinationCity'] = instance.destination_city
        data['productName'] = instance.product_name
        data['specification'] = instance.specification
        data['quantity'] = float(instance.quantity or 1)
        data['uom'] = instance.uom
        data['serialNumber'] = instance.serial_number
        data['batchNumber'] = instance.batch_number
        data['weightMT'] = float(instance.weight_mt or 0)
        data['transporterName'] = instance.transporter_name
        data['vehicleNumber'] = instance.vehicle_number
        data['lrNumber'] = instance.lr_number
        data['driverName'] = instance.driver_name
        data['driverMobile'] = instance.driver_mobile
        data['eWayBillNumber'] = instance.e_way_bill_number
        data['invoiceNumber'] = instance.invoice_number
        data['packagingType'] = instance.packaging_type
        data['dispatchType'] = instance.dispatch_type
        data['qcClearanceBy'] = instance.qc_clearance_by
        data['dispatchedBy'] = instance.dispatched_by
        data['status'] = instance.status
        data['remarks'] = instance.remarks
        return data


class PackingOrderSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = PackingOrder
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'packingNumber': 'packing_number',
            'packingDate': 'packing_date',
            'customerId': 'customer_id',
            'customerName': 'customer_name',
            'salesOrderId': 'sales_order_id',
            'salesOrderNumber': 'sales_order_number',
            'jobId': 'job_id',
            'jobNumber': 'job_number',
            'projectId': 'project_id',
            'projectNumber': 'project_number',
            'qcInspectionNumber': 'qc_inspection_number',
            'finishedGoodsNumber': 'finished_goods_number',
            'productName': 'product_name',
            'totalQuantity': 'total_quantity',
            'packedQuantity': 'packed_quantity',
            'remainingQuantity': 'remaining_quantity',
            'packageType': 'package_type',
            'packageDimensions': 'package_dimensions',
            'grossWeightKg': 'gross_weight_kg',
            'netWeightKg': 'net_weight_kg',
            'packedBy': 'packed_by',
            'verifiedBy': 'verified_by',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if not data.get('packing_number'):
            data['packing_number'] = data.get('id') or f"PACK-{int(datetime.now().timestamp())}"
        if not data.get('packing_date'):
            data['packing_date'] = datetime.now().date().isoformat()
        if not data.get('customer_name'):
            data['customer_name'] = data.get('customerName') or 'Valued Customer'
        if not data.get('product_name'):
            data['product_name'] = data.get('productName') or 'Industrial Process Equipment'
        if not data.get('id'):
            data['id'] = data['packing_number']
        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['packingNumber'] = instance.packing_number
        data['packingDate'] = str(instance.packing_date) if instance.packing_date else ''
        data['customerId'] = instance.customer_id
        data['customerName'] = instance.customer_name
        data['salesOrderId'] = instance.sales_order_id
        data['salesOrderNumber'] = instance.sales_order_number
        data['jobId'] = instance.job_id
        data['jobNumber'] = instance.job_number
        data['projectId'] = instance.project_id
        data['projectNumber'] = instance.project_number
        data['qcInspectionNumber'] = instance.qc_inspection_number
        data['finishedGoodsNumber'] = instance.finished_goods_number
        data['productName'] = instance.product_name
        data['specification'] = instance.specification
        data['totalQuantity'] = float(instance.total_quantity or 1)
        data['packedQuantity'] = float(instance.packed_quantity or 1)
        data['remainingQuantity'] = float(instance.remaining_quantity or 0)
        data['uom'] = instance.uom
        data['packageType'] = instance.package_type
        data['packageDimensions'] = instance.package_dimensions
        data['grossWeightKg'] = float(instance.gross_weight_kg or 0)
        data['netWeightKg'] = float(instance.net_weight_kg or 0)
        data['packedBy'] = instance.packed_by
        data['verifiedBy'] = instance.verified_by
        data['status'] = instance.status
        data['items'] = instance.items
        data['remarks'] = instance.remarks
        return data


