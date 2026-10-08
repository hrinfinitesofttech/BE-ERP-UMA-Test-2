from datetime import datetime
from rest_framework import serializers
from apps.core.base_serializers import UniversalModelSerializerMixin
from .models import (
    Supplier,
    SupplierContact,
    PurchaseRequisition,
    RequestForQuotation,
    SupplierQuotation,
    QuotationComparison,
    PurchaseOrder,
    PurchaseReturn,
    MaterialRequirement,
)


class MaterialRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialRequirement
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'projectId': 'project_id',
            'jobId': 'job_id',
            'jobNumber': 'job_number',
            'customerName': 'customer_name',
            'designJobId': 'design_job_id',
            'bomId': 'bom_id',
            'bomNumber': 'bom_number',
            'bomRevision': 'bom_revision',
            'partNumber': 'part_number',
            'itemCode': 'item_code',
            'itemName': 'item_name',
            'materialName': 'material_name',
            'unitOfMeasure': 'unit_of_measure',
            'requiredQuantity': 'required_quantity',
            'availableStock': 'available_stock',
            'reservedStock': 'reserved_stock',
            'onOrderQuantity': 'on_order_quantity',
            'shortageQuantity': 'shortage_quantity',
            'requiredByDate': 'required_by_date',
            'procurementType': 'procurement_type',
            'procurementStatus': 'procurement_status',
            'drawingNumber': 'drawing_number',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if not data.get('item_name'):
            data['item_name'] = data.get('itemName') or data.get('material_name') or data.get('materialName') or data.get('name') or 'Required Material'
        if not data.get('unit_of_measure'):
            data['unit_of_measure'] = data.get('unit') or 'NOS'
        if 'required_quantity' not in data:
            data['required_quantity'] = float(data.get('quantity') or data.get('qty') or 1)
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {
            'id': ret.get('id'),
            'projectId': ret.get('project_id', ''),
            'jobId': ret.get('job_id', ''),
            'jobNumber': ret.get('job_number', '') or ret.get('job_id', ''),
            'customerName': ret.get('customer_name', ''),
            'designJobId': ret.get('design_job_id', ''),
            'bomId': ret.get('bom_id', ''),
            'bomNumber': ret.get('bom_number', ''),
            'bomRevision': ret.get('bom_revision', 'REV-01'),
            'partNumber': ret.get('part_number', ''),
            'itemCode': ret.get('item_code', ''),
            'itemName': ret.get('item_name', ''),
            'materialName': ret.get('material_name', ''),
            'specification': ret.get('specification', ''),
            'category': ret.get('category', 'Raw Material'),
            'requiredQuantity': ret.get('required_quantity', 0),
            'unitOfMeasure': ret.get('unit_of_measure', 'NOS'),
            'availableStock': ret.get('available_stock', 0),
            'reservedStock': ret.get('reserved_stock', 0),
            'onOrderQuantity': ret.get('on_order_quantity', 0),
            'shortageQuantity': ret.get('shortage_quantity', 0),
            'requiredByDate': ret.get('required_by_date', ''),
            'procurementType': ret.get('procurement_type', 'Purchase'),
            'procurementStatus': ret.get('procurement_status', 'Pending'),
            'drawingNumber': ret.get('drawing_number', ''),
            'status': ret.get('status', 'shortage'),
            'createdAt': ret.get('created_at', ''),
            'updatedAt': ret.get('updated_at', ''),
        }


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequisition
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'indentNumber' in data and 'pr_number' not in data:
            data['pr_number'] = data.pop('indentNumber')
        if 'indent_number' in data and 'pr_number' not in data:
            data['pr_number'] = data.pop('indent_number')
        if 'prNumber' in data and 'pr_number' not in data:
            data['pr_number'] = data.pop('prNumber')
        if not data.get('pr_number'):
            data['pr_number'] = data.get('id') or f"IND-{int(datetime.now().timestamp())}"
        if not data.get('id'):
            data['id'] = data['pr_number']
        if 'projectId' in data and 'project_id' not in data:
            data['project_id'] = data.pop('projectId')
        if 'project' in data and 'project_id' not in data:
            data['project_id'] = data.pop('project')
        if 'jobId' in data and 'job_code' not in data:
            data['job_code'] = data.pop('jobId')
        elif 'jobNumber' in data and 'job_code' not in data:
            data['job_code'] = data.pop('jobNumber')
        if 'requestedBy' in data and 'requested_by' not in data:
            data['requested_by'] = data.pop('requestedBy')
        if 'requisitionDate' in data and 'request_date' not in data:
            data['request_date'] = data.pop('requisitionDate')
        elif 'prDate' in data and 'request_date' not in data:
            data['request_date'] = data.pop('prDate')
        if 'requiredByDate' in data and 'required_by_date' not in data:
            data['required_by_date'] = data.pop('requiredByDate')
        elif 'requiredDate' in data and 'required_by_date' not in data:
            data['required_by_date'] = data.pop('requiredDate')
        if 'estimatedCost' in data and 'total_estimated_cost' not in data:
            data['total_estimated_cost'] = data.pop('estimatedCost')
        if 'approvedBy' in data and 'approved_by' not in data:
            data['approved_by'] = data.pop('approvedBy')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        items = ret.get('items') or []
        return {
            'id': ret.get('id'),
            'prNumber': ret.get('pr_number', ''),
            'projectId': ret.get('project_id', ''),
            'jobId': ret.get('job_code', ''),
            'jobNumber': ret.get('job_code', ''),
            'bomId': f"BOM-{ret.get('job_code', '')}",
            'bomRevision': 'REV-01',
            'requestedBy': ret.get('requested_by', 'Purchase Admin'),
            'department': ret.get('department', 'Purchase / Planning'),
            'requisitionDate': ret.get('request_date', ''),
            'prDate': ret.get('request_date', ''),
            'requiredByDate': ret.get('required_by_date', ''),
            'priority': ret.get('priority', 'high'),
            'status': ret.get('status', 'Submitted'),
            'items': items,
            'totalItems': len(items) if isinstance(items, list) else 0,
            'estimatedCost': ret.get('total_estimated_cost', 0),
            'remarks': ret.get('remarks', ''),
            'approvedBy': ret.get('approved_by'),
            'createdAt': ret.get('created_at', ''),
            'updatedAt': ret.get('updated_at', ''),
        }


class RequestForQuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestForQuotation
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'rfqNumber' in data and 'rfq_number' not in data:
            data['rfq_number'] = data.pop('rfqNumber')
        if 'prId' in data and 'pr_id' not in data:
            data['pr_id'] = data.pop('prId')
        if 'rfqDate' in data and 'rfq_date' not in data:
            data['rfq_date'] = data.pop('rfqDate')
        if 'dueDate' in data and 'due_date' not in data:
            data['due_date'] = data.pop('dueDate')
        if 'invitedSuppliers' in data and 'suppliers' not in data:
            data['suppliers'] = data.pop('invitedSuppliers')
        if 'termsAndConditions' in data and 'terms_and_conditions' not in data:
            data['terms_and_conditions'] = data.pop('termsAndConditions')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        items = ret.get('items') or []
        suppliers = ret.get('suppliers') or []
        return {
            'id': ret.get('id'),
            'rfqNumber': ret.get('rfq_number', ''),
            'prId': ret.get('pr_id', ''),
            'prNumber': ret.get('pr_id', ''),
            'rfqDate': ret.get('rfq_date', ''),
            'dueDate': ret.get('due_date', ''),
            'invitedSuppliers': suppliers,
            'suppliers': suppliers,
            'items': items,
            'status': ret.get('status', 'Sent to Suppliers'),
            'termsAndConditions': ret.get('terms_and_conditions', ''),
            'issuedBy': 'Purchase Team',
            'createdAt': ret.get('created_at', ''),
        }


class SupplierQuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierQuotation
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'quotationNumber' in data and 'quotation_number' not in data:
            data['quotation_number'] = data.pop('quotationNumber')
        if 'rfqId' in data and 'rfq_id' not in data:
            data['rfq_id'] = data.pop('rfqId')
        if 'supplierId' in data and 'supplier_id' not in data:
            data['supplier_id'] = data.pop('supplierId')
        if 'supplierName' in data and 'supplier_name' not in data:
            data['supplier_name'] = data.pop('supplierName')
        if 'quotationDate' in data and 'date' not in data:
            data['date'] = data.pop('quotationDate')
        if 'validityDate' in data and 'valid_until' not in data:
            data['valid_until'] = data.pop('validityDate')
        elif 'validUntil' in data and 'valid_until' not in data:
            data['valid_until'] = data.pop('validUntil')
        if 'subTotal' in data and 'sub_total' not in data:
            data['sub_total'] = data.pop('subTotal')
        if 'taxTotal' in data and 'tax_amount' not in data:
            data['tax_amount'] = data.pop('taxTotal')
        elif 'taxAmount' in data and 'tax_amount' not in data:
            data['tax_amount'] = data.pop('taxAmount')
        if 'grandTotal' in data and 'grand_total' not in data:
            data['grand_total'] = data.pop('grandTotal')
        if 'paymentTerms' in data and 'payment_terms' not in data:
            data['payment_terms'] = data.pop('paymentTerms')
        if 'deliveryLeadTime' in data and 'delivery_lead_time' not in data:
            data['delivery_lead_time'] = data.pop('deliveryLeadTime')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {
            'id': ret.get('id'),
            'quotationNumber': ret.get('quotation_number', ''),
            'rfqId': ret.get('rfq_id', ''),
            'rfqNumber': ret.get('rfq_id', ''),
            'supplierId': ret.get('supplier_id', ''),
            'supplierName': ret.get('supplier_name', ''),
            'supplierQuotationRef': ret.get('quotation_number', ''),
            'quotationDate': ret.get('date', ''),
            'validityDate': ret.get('valid_until', ''),
            'items': ret.get('items') or [],
            'subTotal': ret.get('sub_total', 0),
            'taxTotal': ret.get('tax_amount', 0),
            'grandTotal': ret.get('grand_total', 0),
            'paymentTerms': ret.get('payment_terms', ''),
            'deliveryTerms': 'FOR Destination',
            'leadTimeDays': 7,
            'status': ret.get('status', 'Received'),
            'technicalStatus': 'Compliant',
            'recordedBy': 'Purchase Officer',
            'createdAt': ret.get('created_at', ''),
        }


class SupplierContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierContact
        fields = [
            'id',
            'supplier_id',
            'name',
            'designation',
            'department',
            'mobile',
            'email',
            'is_primary',
        ]


class SupplierSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    contacts = SupplierContactSerializer(many=True, read_only=True)

    class Meta:
        model = Supplier
        fields = [
            'id',
            'vendor_code',
            'name',
            'category',
            'supplier_type',
            'contact_person',
            'mobile',
            'phone',
            'email',
            'address',
            'city',
            'state',
            'country',
            'pincode',
            'gstin',
            'pan',
            'payment_terms',
            'rating',
            'status',
            'contacts',
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if not data.get('vendor_code'):
            data['vendor_code'] = data.get('supplierCode') or data.get('supplier_code') or data.get('vendorCode') or data.get('id') or f"SUP-{int(datetime.now().timestamp())}"
        if not data.get('name'):
            data['name'] = data.get('supplierName') or data.get('supplier_name') or data.get('companyName') or data.get('company_name') or 'Supplier Co'
        if not data.get('contact_person'):
            data['contact_person'] = data.get('contactPerson') or data.get('name') or 'Contact Person'
        if 'phone' in data and not data.get('mobile'):
            data['mobile'] = data.get('phone')
        if not data.get('mobile'):
            data['mobile'] = data.get('phone') or '9999999999'
        if not data.get('id'):
            data['id'] = data.get('vendor_code') or f"SUP-{int(datetime.now().timestamp())}"
        return super().to_internal_value(data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['supplierCode'] = instance.vendor_code
        rep['vendorCode'] = instance.vendor_code
        rep['supplierName'] = instance.name
        rep['contactPerson'] = instance.contact_person
        rep['pinCode'] = instance.pincode
        rep['panNumber'] = instance.pan
        return rep


class QuotationComparisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationComparison
        fields = [
            'id',
            'rfq_id',
            'comparison_date',
            'items',
            'supplier_quotations',
            'recommended_supplier_id',
            'recommended_supplier_name',
            'recommendation_reason',
            'prepared_by',
            'approved_by',
            'status',
        ]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = '__all__'

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'poNumber': 'po_number',
            'revisionNumber': 'revision_number',
            'poDate': 'date',
            'supplierId': 'supplier_id',
            'supplierName': 'supplier_name',
            'contactPerson': 'contact_person',
            'supplierGstin': 'supplier_gstin',
            'supplierAddress': 'supplier_address',
            'projectId': 'project_id',
            'jobId': 'job_code',
            'jobCode': 'job_code',
            'jobNumber': 'job_code',
            'deliveryDate': 'delivery_date',
            'expectedDeliveryDate': 'delivery_date',
            'paymentTerms': 'payment_terms',
            'subTotal': 'sub_total',
            'subtotal': 'sub_total',
            'discountAmount': 'discount_amount',
            'taxAmount': 'tax_amount',
            'taxTotal': 'tax_amount',
            'grandTotal': 'grand_total',
            'totalAmount': 'grand_total',
            'preparedBy': 'prepared_by',
            'createdBy': 'prepared_by',
            'approvedBy': 'approved_by',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)

        if 'supplier' in data and 'supplier_id' not in data:
            data['supplier_id'] = data.pop('supplier')
        if 'indent' in data and 'indent_id' not in data:
            data['indent_id'] = data.pop('indent')

        if data.get('supplier_id'):
            try:
                from .models import Supplier
                s = Supplier.objects.filter(id=data['supplier_id']).first() or Supplier.objects.filter(vendor_code=data['supplier_id']).first()
                if s:
                    if not data.get('supplier_name') or data.get('supplier_name') == 'Supplier':
                        data['supplier_name'] = s.name
                    if not data.get('contact_person'):
                        data['contact_person'] = s.contact_person
                    if not data.get('supplier_gstin'):
                        data['supplier_gstin'] = s.gstin
                    if not data.get('supplier_address'):
                        data['supplier_address'] = s.address
            except Exception:
                pass

        if not data.get('po_number'):
            data['po_number'] = data.get('id') or f"PO-{int(datetime.now().timestamp())}"
        if not data.get('id'):
            data['id'] = data['po_number']
        if not data.get('date'):
            data['date'] = datetime.now().strftime('%Y-%m-%d')
        if not data.get('delivery_date'):
            data['delivery_date'] = datetime.now().strftime('%Y-%m-%d')
        if not data.get('prepared_by'):
            data['prepared_by'] = 'Admin User'
        if not data.get('supplier_id'):
            data['supplier_id'] = 'SUP-001'
        if not data.get('supplier_name'):
            data['supplier_name'] = 'Supplier'
        if not data.get('revision_number'):
            data['revision_number'] = 'Rev-00'
        elif isinstance(data.get('revision_number'), int):
            data['revision_number'] = f"Rev-{data['revision_number']:02d}"

        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        items = ret.get('items') or []
        return {
            'id': ret.get('id'),
            'poNumber': ret.get('po_number', ''),
            'revisionNumber': ret.get('revision_number', 'Rev-00'),
            'date': ret.get('date', ''),
            'poDate': ret.get('date', ''),
            'supplierId': ret.get('supplier_id', ''),
            'supplierName': ret.get('supplier_name', ''),
            'contactPerson': ret.get('contact_person', ''),
            'supplierGstin': ret.get('supplier_gstin', '24AAAAA0000A1Z5'),
            'supplierAddress': ret.get('supplier_address', ''),
            'projectId': ret.get('project_id') or 'PRJ-2026-0001',
            'jobId': ret.get('job_code') or 'JOB-2026-001',
            'jobCode': ret.get('job_code') or 'JOB-2026-001',
            'jobNumber': ret.get('job_code') or 'JOB-2026-001',
            'deliveryDate': ret.get('delivery_date', ''),
            'expectedDeliveryDate': ret.get('delivery_date', ''),
            'paymentTerms': ret.get('payment_terms', '30 Days Credit after GRN'),
            'deliveryTerms': 'FOR Destination (Uma Techno Fab GIDC Works)',
            'dispatchMode': 'By Road Truck',
            'currency': 'INR',
            'items': items,
            'subTotal': ret.get('sub_total', 0),
            'discountAmount': ret.get('discount_amount', 0),
            'taxAmount': ret.get('tax_amount', 0),
            'taxTotal': ret.get('tax_amount', 0),
            'freightCharges': 0,
            'grandTotal': ret.get('grand_total', 0),
            'status': ret.get('status', 'Submitted'),
            'approvalTier': 'Tier 1 - Executive',
            'specialInstructions': 'Test certificates (MTC) required along with material delivery.',
            'preparedBy': ret.get('prepared_by', 'Admin User'),
            'createdBy': ret.get('prepared_by', 'Admin User'),
            'approvedBy': ret.get('approved_by'),
            'createdAt': ret.get('created_at', ''),
            'updatedAt': ret.get('updated_at', ''),
        }


class PurchaseReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseReturn
        fields = [
            'id',
            'return_number',
            'po_id',
            'po_number',
            'grn_id',
            'grn_number',
            'supplier_id',
            'supplier_name',
            'date',
            'reason',
            'items',
            'total_amount',
            'status',
            'debit_note_number',
        ]
