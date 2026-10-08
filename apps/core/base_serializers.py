import re
from datetime import datetime, date
from rest_framework import serializers

def to_snake_case(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def to_camel_case(snake_str: str) -> str:
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

class UniversalModelSerializerMixin:
    """
    Mixin for DRF ModelSerializer providing:
    1. Automatic camelCase to snake_case field conversion on input (to_internal_value).
    2. Intelligent alias mapping (e.g. phone -> mobile, address -> billing_address, etc.).
    3. Automatic snake_case to camelCase field exposure on output (to_representation).
    4. Auto-assignment of missing primary keys using business codes or UUIDs.
    """

    COMMON_ALIASES = {
        'phone': 'mobile',
        'cellPhone': 'mobile',
        'address': 'billing_address',
        'shippingAddress': 'shipping_address',
        'billingAddress': 'billing_address',
        'pinCode': 'pincode',
        'panNumber': 'pan',
        'taxNumber': 'gstin',
        'vendorCode': 'vendor_code',
        'supplierCode': 'vendor_code',
        'supplierName': 'name',
        'companyName': 'company_name',
        'contactPerson': 'contact_person',
        'customerCode': 'customer_code',
        'customerName': 'customer_name',
        'orderValue': 'order_value',
        'soNumber': 'sales_order_number',
        'salesOrderNumber': 'sales_order_number',
        'poNumber': 'po_number',
        'customerPoNumber': 'customer_po_number',
        'jobCardNumber': 'job_card_number',
        'jobNumber': 'job_number',
        'productName': 'product_name',
        'itemCode': 'item_code',
        'itemName': 'item_name',
        'inspectorName': 'inspector',
        'inspectionDate': 'inspection_date',
        'startDate': 'start_date',
        'completionDate': 'completion_date',
        'deliveryDate': 'delivery_date',
        'targetDeliveryDate': 'target_delivery_date',
        'subtotal': 'taxable_amount',
        'totalAmount': 'grand_total',
    }

    def to_internal_value(self, data):
        if not hasattr(data, 'copy'):
            data = dict(data)
        else:
            data = data.copy()

        # Step 1: Normalize all camelCase keys to snake_case
        keys_to_process = list(data.keys())
        for key in keys_to_process:
            val = data[key]
            snake_key = to_snake_case(key)
            if snake_key != key and snake_key not in data:
                data[snake_key] = val

            # Check common aliases
            if key in self.COMMON_ALIASES:
                alias = self.COMMON_ALIASES[key]
                if alias not in data:
                    data[alias] = val
            if snake_key in self.COMMON_ALIASES:
                alias = self.COMMON_ALIASES[snake_key]
                if alias not in data:
                    data[alias] = val

        # Step 2: Handle specific model requirements
        model_cls = getattr(self.Meta, 'model', None)
        if model_cls:
            model_fields = {f.name for f in model_cls._meta.fields}

            # If model has mobile and phone is provided
            if 'mobile' in model_fields and 'mobile' not in data:
                data['mobile'] = data.get('phone') or '9999999999'

            # If model has vendor_code and supplierCode or id is provided
            if 'vendor_code' in model_fields and 'vendor_code' not in data:
                data['vendor_code'] = data.get('supplier_code') or data.get('vendorCode') or data.get('supplierCode') or data.get('id') or f"SUP-{int(datetime.now().timestamp())}"

            # If model has name and supplier_name/company_name is provided
            if 'name' in model_fields and 'name' not in data:
                data['name'] = data.get('supplier_name') or data.get('company_name') or data.get('supplierName') or data.get('companyName') or 'Supplier'

            # If model has contact_person
            if 'contact_person' in model_fields and 'contact_person' not in data:
                data['contact_person'] = data.get('contactPerson') or data.get('name') or data.get('company_name') or 'Contact Person'

            # If model has product_name
            if 'product_name' in model_fields and 'product_name' not in data:
                data['product_name'] = data.get('productName') or data.get('machine_product') or data.get('machineProduct') or data.get('title') or data.get('requirement_description') or 'Process Equipment'

            # If model has machine_product (e.g. Enquiry, Opportunity)
            if 'machine_product' in model_fields and 'machine_product' not in data:
                items = data.get('items', [])
                item_name = items[0].get('productName') or items[0].get('product_name') if items and isinstance(items, list) and isinstance(items[0], dict) else None
                data['machine_product'] = data.get('product_name') or data.get('productName') or item_name or 'Process Equipment'

            # If model has requirement (e.g. Enquiry)
            if 'requirement' in model_fields and 'requirement' not in data:
                data['requirement'] = data.get('subject') or data.get('notes') or data.get('description') or 'Customer Requirement'

            # If model has enquiry_date
            if 'enquiry_date' in model_fields and 'enquiry_date' not in data:
                data['enquiry_date'] = data.get('date') or datetime.now().date().isoformat()

            # If model has grn_id and grn_number is provided
            if 'grn_id' in model_fields and not data.get('grn_id'):
                data['grn_id'] = data.get('grn_number') or data.get('grnNumber') or data.get('id') or 'GRN-001'

            if 'grn_number' in model_fields and not data.get('grn_number'):
                data['grn_number'] = data.get('grn_id') or data.get('grnId') or 'GRN-001'

            if 'inspector' in model_fields and not data.get('inspector'):
                data['inspector'] = data.get('inspector_name') or data.get('inspectorName') or 'Quality Inspector'

            if 'inspection_date' in model_fields and not data.get('inspection_date'):
                data['inspection_date'] = data.get('inspectionDate') or datetime.now().date().isoformat()

            # Common FK shorthand mappings
            fk_mappings = {
                'customer': 'customer_id',
                'customerId': 'customer_id',
                'lead': 'lead_id',
                'leadId': 'lead_id',
                'enquiry': 'enquiry_id',
                'enquiryId': 'enquiry_id',
                'quotation': 'quotation_id',
                'quotationId': 'quotation_id',
                'project': 'project_id',
                'projectId': 'project_id',
                'salesOrder': 'sales_order_id',
                'salesOrderId': 'sales_order_id',
                'sales_order': 'sales_order_id',
                'purchaseOrder': 'purchase_order_id',
                'purchaseOrderId': 'purchase_order_id',
                'purchase_order': 'purchase_order_id',
                'supplier': 'supplier_id',
                'supplierId': 'supplier_id',
                'vendor': 'vendor_id',
                'vendorId': 'vendor_id',
                'indent': 'indent_id',
                'indentId': 'indent_id',
                'grn': 'grn_id',
                'grnId': 'grn_id',
                'invoice': 'invoice_id',
                'invoiceId': 'invoice_id',
            }
            for src_key, target_key in fk_mappings.items():
                if src_key in data and target_key in model_fields and target_key not in data:
                    data[target_key] = data[src_key]
                # Also support vice versa if model has FK relation without _id
                rel_key = target_key.replace('_id', '')
                if target_key in data and rel_key in model_fields and rel_key not in data:
                    data[rel_key] = data[target_key]

            # If model has customer_name and customer_id is provided, auto-lookup
            if 'customer_name' in model_fields and not data.get('customer_name'):
                cid = data.get('customer_id') or data.get('customerId') or data.get('customer')
                if cid:
                    try:
                        from apps.crm.models import Customer
                        c = Customer.objects.filter(id=cid).first() or Customer.objects.filter(customer_code=cid).first()
                        if c:
                            data['customer_name'] = c.company_name
                    except Exception:
                        pass
                if not data.get('customer_name'):
                    data['customer_name'] = data.get('companyName') or data.get('company_name') or 'Valued Customer'

            # For QCInspection items
            if 'items' in model_fields and not data.get('items'):
                if data.get('item_code') or data.get('itemCode'):
                    data['items'] = [{
                        'itemCode': data.get('item_code') or data.get('itemCode'),
                        'inspectedQuantity': data.get('inspected_quantity') or data.get('inspectedQuantity') or 1,
                        'acceptedQuantity': data.get('accepted_quantity') or data.get('acceptedQuantity') or 1,
                        'rejectedQuantity': data.get('rejected_quantity') or data.get('rejectedQuantity') or 0,
                    }]

            # If model has job_number
            if 'job_number' in model_fields and 'job_number' not in data:
                data['job_number'] = data.get('jobNumber') or data.get('job_card_number') or data.get('jobCardNumber') or data.get('id') or 'JOB-001'

            # Handle ID generation if missing
            inst = getattr(self, 'instance', None)
            if not inst:
                if 'id' not in data or not data['id']:
                    code_field = next((f for f in ['code', 'lead_no', 'customer_code', 'enquiry_no', 'opportunity_no',
                                                   'quotation_number', 'po_number', 'sales_order_number', 'project_number',
                                                   'job_number', 'design_job_number', 'bom_number', 'vendor_code',
                                                   'pr_number', 'grn_number', 'inspection_number', 'issue_number',
                                                   'dispatch_number', 'invoice_number', 'receipt_number', 'payment_number']
                                       if f in model_fields and data.get(f)), None)
                    if code_field:
                        data['id'] = str(data[code_field])
                    else:
                        data['id'] = f"REC-{int(datetime.now().timestamp()*1000)}"

        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Add camelCase aliases for all snake_case keys
        aliases = {}
        for k, v in ret.items():
            camel_k = to_camel_case(k)
            if camel_k != k:
                aliases[camel_k] = v
        ret.update(aliases)
        return ret
