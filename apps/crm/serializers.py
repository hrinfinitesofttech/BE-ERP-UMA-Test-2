from datetime import datetime
from rest_framework import serializers
from apps.core.base_serializers import UniversalModelSerializerMixin
from .models import (
    Lead,
    Customer,
    Contact,
    Enquiry,
    Opportunity,
    FollowUp,
    SiteVisit,
    Exhibition,
    Quotation,
    CustomerPO,
    SalesOrder,
    Activity,
)


class LeadSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            'id',
            'lead_no',
            'company_name',
            'industry',
            'website',
            'gstin',
            'address',
            'city',
            'state',
            'country',
            'pincode',
            'contact_person',
            'designation',
            'mobile',
            'alt_mobile',
            'email',
            'whatsapp',
            'product_name',
            'machine_type',
            'quantity',
            'capacity',
            'application',
            'requirement_description',
            'expected_delivery',
            'budget',
            'priority',
            'source',
            'assigned_sales_person_id',
            'assigned_sales_person_name',
            'status',
            'next_follow_up_date',
            'remarks',
            'created_date',
            'converted_customer_id',
            'converted_enquiry_id',
            'converted_opportunity_id',
            'attachments',
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'leadNo': 'lead_no',
            'companyName': 'company_name',
            'contactPerson': 'contact_person',
            'altMobile': 'alt_mobile',
            'productName': 'product_name',
            'machineType': 'machine_type',
            'requirementDescription': 'requirement_description',
            'expectedDelivery': 'expected_delivery',
            'assignedSalesPersonId': 'assigned_sales_person_id',
            'assignedSalesPersonName': 'assigned_sales_person_name',
            'nextFollowUpDate': 'next_follow_up_date',
            'createdDate': 'created_date',
            'convertedCustomerId': 'converted_customer_id',
            'convertedEnquiryId': 'converted_enquiry_id',
            'convertedOpportunityId': 'converted_opportunity_id',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if 'phone' in data and 'mobile' not in data:
            data['mobile'] = data.pop('phone')
        if not data.get('mobile'):
            data['mobile'] = '9999999999'
        if not data.get('product_name'):
            data['product_name'] = data.get('productName') or data.get('notes') or data.get('requirement_description') or 'Industrial Process Equipment'
        inst = getattr(self, 'instance', None)
        if inst:
            if 'id' in data:
                data.pop('id', None)
        else:
            if not data.get('lead_no'):
                data['lead_no'] = data.get('leadNumber') or data.get('id') or f"LEAD-{int(datetime.now().timestamp())}"
            if not data.get('id'):
                data['id'] = data['lead_no']
            if not data.get('created_date'):
                data['created_date'] = datetime.now().date().isoformat()
        return super().to_internal_value(data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['leadNo'] = instance.lead_no
        rep['companyName'] = instance.company_name
        rep['contactPerson'] = instance.contact_person
        rep['altMobile'] = instance.alt_mobile
        rep['productName'] = instance.product_name
        rep['machineType'] = instance.machine_type
        rep['requirementDescription'] = instance.requirement_description
        rep['expectedDelivery'] = str(instance.expected_delivery) if instance.expected_delivery else ''
        rep['assignedSalesPersonId'] = instance.assigned_sales_person_id
        rep['assignedSalesPersonName'] = instance.assigned_sales_person_name
        rep['nextFollowUpDate'] = str(instance.next_follow_up_date) if instance.next_follow_up_date else ''
        rep['createdDate'] = str(instance.created_date) if instance.created_date else ''
        rep['convertedCustomerId'] = instance.converted_customer_id
        rep['convertedEnquiryId'] = instance.converted_enquiry_id
        rep['convertedOpportunityId'] = instance.converted_opportunity_id
        return rep


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            'id',
            'customer_id',
            'customer_name',
            'name',
            'designation',
            'department',
            'email',
            'mobile',
            'whatsapp',
            'is_primary',
        ]


class CustomerSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    contacts = ContactSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id',
            'customer_code',
            'customer_type',
            'company_name',
            'industry',
            'gstin',
            'pan',
            'website',
            'contact_person',
            'designation',
            'mobile',
            'email',
            'whatsapp',
            'billing_address',
            'shipping_address',
            'city',
            'state',
            'country',
            'pincode',
            'payment_terms',
            'credit_limit',
            'currency',
            'category',
            'assigned_sales_person',
            'created_date',
            'contacts',
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'customerCode': 'customer_code',
            'customerType': 'customer_type',
            'companyName': 'company_name',
            'contactPerson': 'contact_person',
            'billingAddress': 'billing_address',
            'shippingAddress': 'shipping_address',
            'paymentTerms': 'payment_terms',
            'creditLimit': 'credit_limit',
            'assignedSalesPerson': 'assigned_sales_person',
            'createdDate': 'created_date',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if 'phone' in data and 'mobile' not in data:
            data['mobile'] = data.pop('phone')
        if not data.get('mobile'):
            data['mobile'] = '9999999999'
        if 'address' in data and not data.get('billing_address'):
            data['billing_address'] = data.get('address')
        if not data.get('company_name'):
            data['company_name'] = data.get('name', 'Customer Co')
        inst = getattr(self, 'instance', None)
        if inst:
            if 'id' in data:
                data.pop('id', None)
        else:
            if not data.get('customer_code'):
                data['customer_code'] = data.get('id') or f"CUST-{int(datetime.now().timestamp())}"
            if not data.get('id'):
                data['id'] = data['customer_code']
            if not data.get('created_date'):
                data['created_date'] = datetime.now().date().isoformat()
            if not data.get('customer_type'):
                data['customer_type'] = 'company'
            if not data.get('contact_person'):
                data['contact_person'] = data.get('company_name', 'Customer Representative')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['customerCode'] = instance.customer_code
        rep['customerType'] = instance.customer_type
        rep['companyName'] = instance.company_name
        rep['contactPerson'] = instance.contact_person
        rep['billingAddress'] = instance.billing_address
        rep['shippingAddress'] = instance.shipping_address
        rep['paymentTerms'] = instance.payment_terms
        rep['creditLimit'] = float(instance.credit_limit or 0)
        rep['assignedSalesPerson'] = instance.assigned_sales_person
        rep['createdDate'] = str(instance.created_date) if instance.created_date else ''
        return rep


class EnquirySerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = [
            'id',
            'enquiry_no',
            'lead_id',
            'customer_id',
            'customer_name',
            'customer_email',
            'contact_person',
            'contact_mobile',
            'enquiry_date',
            'requirement',
            'machine_product',
            'quantity',
            'specification',
            'expected_delivery',
            'assigned_person_id',
            'assigned_person_name',
            'status',
            'quotation_id',
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        field_map = {
            'enquiryNo': 'enquiry_no',
            'enquiryNumber': 'enquiry_no',
            'leadId': 'lead_id',
            'lead': 'lead_id',
            'customerId': 'customer_id',
            'customer': 'customer_id',
            'customerName': 'customer_name',
            'companyName': 'customer_name',
            'customerEmail': 'customer_email',
            'email': 'customer_email',
            'contactPerson': 'contact_person',
            'contactMobile': 'contact_mobile',
            'mobile': 'contact_mobile',
            'phone': 'contact_mobile',
            'enquiryDate': 'enquiry_date',
            'machineProduct': 'machine_product',
            'expectedDelivery': 'expected_delivery',
            'assignedPersonId': 'assigned_person_id',
            'assignedPersonName': 'assigned_person_name',
            'quotationId': 'quotation_id',
        }
        for camel, snake in field_map.items():
            if camel in data and snake not in data:
                data[snake] = data.pop(camel)
        if data.get('customer_id') and not data.get('customer_name'):
            try:
                from .models import Customer
                c = Customer.objects.filter(id=data['customer_id']).first() or Customer.objects.filter(customer_code=data['customer_id']).first()
                if c:
                    data['customer_name'] = c.company_name
                    if not data.get('customer_email') and c.email:
                        data['customer_email'] = c.email
                    if not data.get('contact_person') and c.contact_person:
                        data['contact_person'] = c.contact_person
                    if not data.get('contact_mobile') and c.mobile:
                        data['contact_mobile'] = c.mobile
            except Exception:
                pass
        if not data.get('customer_name'):
            data['customer_name'] = data.get('company_name') or 'Valued Customer'
        if not data.get('requirement'):
            data['requirement'] = data.get('description') or data.get('subject') or data.get('notes') or 'Customer Requirement'
        if not data.get('machine_product'):
            items = data.get('items', [])
            item_name = items[0].get('productName') or items[0].get('product_name') if items and isinstance(items, list) and isinstance(items[0], dict) else None
            data['machine_product'] = item_name or data.get('machineProduct') or data.get('productName') or data.get('subject') or 'Process Equipment'
        if not data.get('enquiry_date'):
            data['enquiry_date'] = data.get('enquiryDate') or data.get('date') or datetime.now().date().isoformat()
        inst = getattr(self, 'instance', None)
        if inst:
            if 'id' in data:
                data.pop('id', None)
        else:
            if not data.get('enquiry_no'):
                data['enquiry_no'] = data.get('enquiryNumber') or data.get('id') or f"ENQ-{int(datetime.now().timestamp())}"
            if not data.get('id'):
                data['id'] = data['enquiry_no']
        return super().to_internal_value(data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['enquiryNo'] = instance.enquiry_no
        rep['leadId'] = instance.lead_id
        rep['customerId'] = instance.customer_id
        rep['customerName'] = instance.customer_name
        rep['customerEmail'] = instance.customer_email
        rep['contactPerson'] = instance.contact_person
        rep['contactMobile'] = instance.contact_mobile
        rep['enquiryDate'] = str(instance.enquiry_date) if instance.enquiry_date else ''
        rep['machineProduct'] = instance.machine_product
        rep['expectedDelivery'] = str(instance.expected_delivery) if instance.expected_delivery else ''
        rep['assignedPersonId'] = instance.assigned_person_id
        rep['assignedPersonName'] = instance.assigned_person_name
        rep['quotationId'] = instance.quotation_id
        return rep


class OpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Opportunity
        fields = [
            'id',
            'opportunity_no',
            'lead_id',
            'customer_id',
            'customer_name',
            'machine_product',
            'estimated_value',
            'expected_closing_date',
            'sales_person_id',
            'sales_person_name',
            'probability',
            'stage',
            'remarks',
            'quotation_id',
        ]


class FollowUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowUp
        fields = [
            'id',
            'follow_up_no',
            'lead_or_customer_id',
            'lead_or_customer_name',
            'entity_type',
            'type',
            'assigned_to_id',
            'assigned_to_name',
            'date',
            'time',
            'priority',
            'purpose',
            'notes',
            'next_follow_up_date',
            'status',
            'completed_notes',
        ]


class SiteVisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteVisit
        fields = [
            'id',
            'visit_no',
            'customer_id',
            'customer_name',
            'contact_person',
            'contact_mobile',
            'visit_date',
            'location',
            'employee_id',
            'employee_name',
            'purpose',
            'discussion_notes',
            'requirement_details',
            'outcome',
            'next_action',
            'next_follow_up_date',
        ]


class ExhibitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exhibition
        fields = [
            'id',
            'expo_name',
            'organizer',
            'location',
            'start_date',
            'end_date',
            'stall_number',
            'contact_person',
            'budget',
            'assigned_team',
            'products_displayed',
            'notes',
            'total_contacts',
            'qualified_leads',
            'quotations_sent',
            'converted_customers',
        ]


class QuotationSerializer(UniversalModelSerializerMixin, serializers.ModelSerializer):
    quotationNumber = serializers.CharField(source='quotation_number', required=False)
    currentRevision = serializers.CharField(source='current_revision', required=False)
    validUntil = serializers.CharField(source='valid_until', required=False, allow_blank=True)
    customerId = serializers.CharField(source='customer_id', required=False)
    customerName = serializers.CharField(source='customer_name', required=False)
    contactPerson = serializers.CharField(source='contact_person', required=False, allow_blank=True)
    contactMobile = serializers.CharField(source='contact_mobile', required=False, allow_blank=True)
    contactEmail = serializers.CharField(source='contact_email', required=False, allow_blank=True)
    enquiryId = serializers.CharField(source='enquiry_id', required=False, allow_blank=True, allow_null=True)
    opportunityId = serializers.CharField(source='opportunity_id', required=False, allow_blank=True, allow_null=True)
    salesPersonId = serializers.CharField(source='sales_person_id', required=False, allow_blank=True)
    salesPersonName = serializers.CharField(source='sales_person_name', required=False, allow_blank=True)

    class Meta:
        model = Quotation
        fields = '__all__'

    def to_internal_value(self, data):
        inst = getattr(self, 'instance', None)
        ret = {}
        ret['id'] = data.get('id') or data.get('quotationNumber') or data.get('quotation_number') or (inst.id if inst else None)
        ret['quotation_number'] = data.get('quotation_number') or data.get('quotationNumber') or ret.get('id') or (inst.quotation_number if inst else '')
        ret['current_revision'] = data.get('current_revision') or data.get('currentRevision') or (inst.current_revision if inst else 'Rev-00')
        ret['date'] = data.get('date') or (inst.date if inst else datetime.now().strftime('%Y-%m-%d'))
        ret['valid_until'] = data.get('valid_until') or data.get('validUntil') or (inst.valid_until if inst else '')
        ret['customer_id'] = data.get('customer_id') or data.get('customerId') or data.get('customer') or (inst.customer_id if inst else '')
        ret['customer_name'] = data.get('customer_name') or data.get('customerName') or (inst.customer_name if inst else '')
        if ret.get('customer_id') and not ret.get('customer_name'):
            try:
                from .models import Customer
                c = Customer.objects.filter(id=ret['customer_id']).first() or Customer.objects.filter(customer_code=ret['customer_id']).first()
                if c:
                    ret['customer_name'] = c.company_name
            except Exception:
                pass
        if not ret.get('customer_name'):
            ret['customer_name'] = data.get('company_name') or data.get('companyName') or 'Valued Customer'
        ret['contact_person'] = data.get('contact_person') or data.get('contactPerson') or (inst.contact_person if inst else '')
        ret['contact_mobile'] = data.get('contact_mobile') or data.get('contactMobile') or (inst.contact_mobile if inst else '')
        ret['contact_email'] = data.get('contact_email') or data.get('contactEmail') or (inst.contact_email if inst else '')
        ret['enquiry_id'] = data.get('enquiry_id') or data.get('enquiryId') or data.get('enquiry') or (inst.enquiry_id if inst else None)
        ret['opportunity_id'] = data.get('opportunity_id') or data.get('opportunityId') or (inst.opportunity_id if inst else None)
        ret['sales_person_id'] = data.get('sales_person_id') or data.get('salesPersonId') or (inst.sales_person_id if inst else '')
        ret['sales_person_name'] = data.get('sales_person_name') or data.get('salesPersonName') or (inst.sales_person_name if inst else '')
        ret['status'] = data.get('status') or (inst.status if inst else 'draft')
        ret['lead_id'] = data.get('lead_id') or data.get('leadId') or (inst.lead_id if inst else None)
        ret['machine_product'] = data.get('machine_product') or data.get('machineProduct') or (inst.machine_product if inst else '')
        ret['latest_summary'] = data.get('latest_summary') or data.get('latestSummary') or (inst.latest_summary if inst else '')
        ret['subtotal'] = float(data.get('subtotal') or (inst.subtotal if inst else 0))
        ret['tax_amount'] = float(data.get('tax_amount') or data.get('taxAmount') or (inst.tax_amount if inst else 0))
        ret['total_amount'] = float(data.get('total_amount') or data.get('totalAmount') or data.get('grand_total') or data.get('grandTotal') or (inst.total_amount if inst else 0))
        ret['grand_total'] = float(data.get('grand_total') or data.get('grandTotal') or ret['total_amount'] or (inst.grand_total if inst else 0))
        ret['items'] = data.get('items') or (inst.items if inst else [])
        if 'approved_by' in data or 'approvedBy' in data:
            ret['approved_by'] = data.get('approved_by') or data.get('approvedBy')
        if 'rejection_reason' in data or 'rejectionReason' in data:
            ret['rejection_reason'] = data.get('rejection_reason') or data.get('rejectionReason')

        if 'revisions' in data:
            ret['revisions'] = data.get('revisions') or []
        elif inst and inst.revisions:
            ret['revisions'] = inst.revisions
        else:
            ret['revisions'] = [{
                'revisionNumber': 'Rev-00',
                'revisionDate': ret.get('date'),
                'items': ret.get('items'),
                'subtotal': ret.get('subtotal'),
                'taxAmount': ret.get('tax_amount'),
                'grandTotal': ret.get('total_amount'),
                'status': ret.get('status'),
            }]

        if 'notes' in data:
            ret['notes'] = data.get('notes') or ''
        elif inst:
            ret['notes'] = inst.notes or ''
        else:
            ret['notes'] = ''
        return ret

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['id'] = instance.id
        rep['quotationNumber'] = instance.quotation_number
        rep['currentRevision'] = instance.current_revision
        rep['date'] = instance.date
        rep['validUntil'] = instance.valid_until
        rep['customerId'] = instance.customer_id
        rep['customerName'] = instance.customer_name
        rep['contactPerson'] = instance.contact_person
        rep['contactMobile'] = instance.contact_mobile
        rep['contactEmail'] = instance.contact_email
        rep['leadId'] = instance.lead_id
        rep['enquiryId'] = instance.enquiry_id
        rep['opportunityId'] = instance.opportunity_id
        rep['machineProduct'] = instance.machine_product
        rep['salesPersonId'] = instance.sales_person_id
        rep['salesPersonName'] = instance.sales_person_name
        rep['revisions'] = instance.revisions or []
        rep['items'] = instance.items or []
        rep['subtotal'] = instance.subtotal
        rep['taxAmount'] = instance.tax_amount
        rep['totalAmount'] = instance.total_amount
        rep['grandTotal'] = instance.grand_total or instance.total_amount
        rep['status'] = instance.status
        rep['approvedBy'] = instance.approved_by
        rep['approvedAt'] = instance.approved_at.isoformat() if instance.approved_at else None
        rep['rejectionReason'] = instance.rejection_reason
        rep['notes'] = instance.notes
        
        # Calculate latestSummary for frontend convenience
        revs = instance.revisions or []
        last_rev = revs[-1] if revs else {}
        first_item = (instance.items or last_rev.get('items') or [{}])[0]
        rep['latestSummary'] = {
            'machineProduct': instance.machine_product or first_item.get('productName', 'Process Equipment'),
            'grandTotal': instance.grand_total or instance.total_amount or last_rev.get('grandTotal', 0),
            'status': instance.status or last_rev.get('status', 'draft')
        }
        return rep


class CustomerPOSerializer(serializers.ModelSerializer):
    poNumber = serializers.CharField(source='po_number', required=False)
    internalCpoNo = serializers.CharField(source='internal_cpo_no', required=False, allow_blank=True)
    customerId = serializers.CharField(source='customer_id', required=False)
    customerName = serializers.CharField(source='customer_name', required=False)
    quotationId = serializers.CharField(source='quotation_id', required=False, allow_blank=True, allow_null=True)
    quotationNumber = serializers.CharField(source='quotation_number', required=False, allow_blank=True)
    poDate = serializers.CharField(source='po_date', required=False)
    receivedDate = serializers.CharField(source='received_date', required=False, allow_blank=True)
    deliveryDate = serializers.CharField(source='delivery_date', required=False, allow_blank=True)
    poAmount = serializers.FloatField(source='po_value', required=False)
    poValue = serializers.FloatField(source='po_value', required=False)
    scopeOfWork = serializers.CharField(source='scope_of_work', required=False, allow_blank=True)
    paymentTerms = serializers.CharField(source='payment_terms', required=False, allow_blank=True)
    poDocumentUrl = serializers.CharField(source='po_document_url', required=False, allow_blank=True)
    attachmentUrl = serializers.CharField(source='attachment_url', required=False, allow_blank=True)
    convertedSoId = serializers.CharField(source='converted_so_id', required=False, allow_blank=True, allow_null=True)
    salesOrderId = serializers.CharField(source='converted_so_id', required=False, allow_blank=True, allow_null=True)
    specialConditions = serializers.CharField(source='special_conditions', required=False, allow_blank=True)

    class Meta:
        model = CustomerPO
        fields = '__all__'

    def to_internal_value(self, data):
        inst = getattr(self, 'instance', None)
        ret = {}
        if inst:
            ret['id'] = inst.id
            ret['po_number'] = inst.po_number
        else:
            ret['id'] = data.get('id') or data.get('internal_cpo_no') or data.get('internalCpoNo') or data.get('po_number') or data.get('poNumber') or None
            ret['po_number'] = data.get('po_number') or data.get('poNumber') or ret.get('id') or 'PO/GEN'
        ret['internal_cpo_no'] = data.get('internal_cpo_no') or data.get('internalCpoNo') or (inst.internal_cpo_no if inst else '')
        ret['customer_id'] = data.get('customer_id') or data.get('customerId') or data.get('customer') or (inst.customer_id if inst else '')
        ret['customer_name'] = data.get('customer_name') or data.get('customerName') or (inst.customer_name if inst else '')
        if ret.get('customer_id') and not ret.get('customer_name'):
            try:
                from .models import Customer
                c = Customer.objects.filter(id=ret['customer_id']).first() or Customer.objects.filter(customer_code=ret['customer_id']).first()
                if c:
                    ret['customer_name'] = c.company_name
            except Exception:
                pass
        if not ret.get('customer_name'):
            ret['customer_name'] = data.get('company_name') or data.get('companyName') or 'Valued Customer'
        ret['quotation_id'] = data.get('quotation_id') or data.get('quotationId') or data.get('quotation') or (inst.quotation_id if inst else None)
        ret['quotation_number'] = data.get('quotation_number') or data.get('quotationNumber') or (inst.quotation_number if inst else '')
        ret['po_date'] = data.get('po_date') or data.get('poDate') or (inst.po_date if inst else datetime.now().strftime('%Y-%m-%d'))
        ret['received_date'] = data.get('received_date') or data.get('receivedDate') or (inst.received_date if inst else ret['po_date'])
        ret['delivery_date'] = data.get('delivery_date') or data.get('deliveryDate') or (inst.delivery_date if inst else '')
        
        po_val = data.get('po_value') if 'po_value' in data else (data.get('poValue') if 'poValue' in data else (data.get('orderValue') if 'orderValue' in data else (data.get('order_value') if 'order_value' in data else (data.get('poAmount') if 'poAmount' in data else (data.get('po_amount') if 'po_amount' in data else None)))))
        if po_val is not None:
            ret['po_value'] = float(po_val)
        elif inst:
            ret['po_value'] = inst.po_value
        else:
            ret['po_value'] = 0.0

        ret['po_amount'] = ret['po_value']
        ret['scope_of_work'] = data.get('scope_of_work') or data.get('scopeOfWork') or data.get('remarks') or (inst.scope_of_work if inst else '')
        ret['remarks'] = data.get('remarks') or ret['scope_of_work']
        ret['payment_terms'] = data.get('payment_terms') or data.get('paymentTerms') or (inst.payment_terms if inst else '')
        ret['po_document_url'] = data.get('po_document_url') or data.get('poDocumentUrl') or (inst.po_document_url if inst else '')
        ret['attachment_url'] = data.get('attachment_url') or data.get('attachmentUrl') or ret['po_document_url']
        ret['status'] = data.get('status') or (inst.status if inst else 'received')
        ret['converted_so_id'] = data.get('converted_so_id') or data.get('convertedSoId') or data.get('salesOrderId') or data.get('sales_order_id') or (inst.converted_so_id if inst else None)
        ret['sales_order_id'] = ret['converted_so_id']
        ret['special_conditions'] = data.get('special_conditions') or data.get('specialConditions') or (inst.special_conditions if inst else '')
        return ret

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['id'] = instance.id
        rep['poNumber'] = instance.po_number
        rep['internalCpoNo'] = instance.internal_cpo_no
        rep['customerId'] = instance.customer_id
        rep['customerName'] = instance.customer_name
        rep['quotationId'] = instance.quotation_id
        rep['quotationNumber'] = instance.quotation_number
        rep['poDate'] = instance.po_date
        rep['receivedDate'] = instance.received_date
        rep['deliveryDate'] = instance.delivery_date
        rep['poAmount'] = instance.po_amount or instance.po_value
        rep['poValue'] = instance.po_value
        rep['scopeOfWork'] = instance.scope_of_work
        rep['remarks'] = instance.remarks or instance.scope_of_work
        rep['paymentTerms'] = instance.payment_terms
        rep['poDocumentUrl'] = instance.po_document_url
        rep['attachmentUrl'] = instance.attachment_url or instance.po_document_url
        rep['status'] = instance.status
        rep['convertedSoId'] = instance.converted_so_id
        rep['salesOrderId'] = instance.sales_order_id or instance.converted_so_id
        rep['specialConditions'] = instance.special_conditions
        return rep


class SalesOrderSerializer(serializers.ModelSerializer):
    salesOrderNumber = serializers.CharField(source='sales_order_number', required=False)
    customerPoId = serializers.CharField(source='customer_po_id', required=False, allow_blank=True, allow_null=True)
    customerPoNumber = serializers.CharField(source='customer_po_number', required=False, allow_blank=True)
    quotationId = serializers.CharField(source='quotation_id', required=False, allow_blank=True, allow_null=True)
    quotationNumber = serializers.CharField(source='quotation_number', required=False, allow_blank=True)
    customerId = serializers.CharField(source='customer_id', required=False)
    customerName = serializers.CharField(source='customer_name', required=False)
    orderDate = serializers.CharField(source='order_date', required=False)
    targetDeliveryDate = serializers.CharField(source='target_delivery_date', required=False, allow_blank=True)
    deliveryDate = serializers.CharField(source='delivery_date', required=False, allow_blank=True)
    totalAmount = serializers.FloatField(source='total_amount', required=False)
    taxAmount = serializers.FloatField(source='tax_amount', required=False)
    grandTotal = serializers.FloatField(source='grand_total', required=False)
    orderValue = serializers.FloatField(source='order_value', required=False)
    paymentTerms = serializers.CharField(source='payment_terms', required=False, allow_blank=True)
    billingAddress = serializers.CharField(source='billing_address', required=False, allow_blank=True)
    shippingAddress = serializers.CharField(source='shipping_address', required=False, allow_blank=True)
    projectId = serializers.CharField(source='project_id', required=False, allow_blank=True, allow_null=True)
    jobNumber = serializers.CharField(source='job_number', required=False, allow_blank=True)
    assignedProjectManager = serializers.CharField(source='assigned_project_manager', required=False, allow_blank=True)
    createdBy = serializers.CharField(source='created_by', required=False, allow_blank=True)
    approvedBy = serializers.CharField(source='approved_by', required=False, allow_blank=True)

    class Meta:
        model = SalesOrder
        fields = '__all__'

    def to_internal_value(self, data):
        inst = getattr(self, 'instance', None)
        ret = {}
        if inst:
            ret['id'] = inst.id
            ret['sales_order_number'] = inst.sales_order_number
        else:
            ret['id'] = data.get('id') or data.get('salesOrderNumber') or data.get('sales_order_number') or None
            ret['sales_order_number'] = data.get('sales_order_number') or data.get('salesOrderNumber') or ret.get('id') or 'SO-GEN'
        ret['customer_po_id'] = data.get('customer_po_id') or data.get('customerPoId') or data.get('customerPo') or data.get('customer_po') or (inst.customer_po_id if inst else None)
        ret['customer_po_number'] = data.get('customer_po_number') or data.get('customerPoNumber') or (inst.customer_po_number if inst else '')
        ret['quotation_id'] = data.get('quotation_id') or data.get('quotationId') or data.get('quotation') or (inst.quotation_id if inst else None)
        ret['quotation_number'] = data.get('quotation_number') or data.get('quotationNumber') or (inst.quotation_number if inst else '')
        ret['customer_id'] = data.get('customer_id') or data.get('customerId') or data.get('customer') or (inst.customer_id if inst else '')
        ret['customer_name'] = data.get('customer_name') or data.get('customerName') or (inst.customer_name if inst else '')
        if ret.get('customer_id') and not ret.get('customer_name'):
            try:
                from .models import Customer
                c = Customer.objects.filter(id=ret['customer_id']).first() or Customer.objects.filter(customer_code=ret['customer_id']).first()
                if c:
                    ret['customer_name'] = c.company_name
            except Exception:
                pass
        if not ret.get('customer_name'):
            ret['customer_name'] = data.get('company_name') or data.get('companyName') or 'Valued Customer'
        ret['order_date'] = data.get('order_date') or data.get('orderDate') or (inst.order_date if inst else datetime.now().strftime('%Y-%m-%d'))
        ret['target_delivery_date'] = data.get('target_delivery_date') or data.get('targetDeliveryDate') or data.get('deliveryDate') or data.get('delivery_date') or (inst.target_delivery_date if inst else '')
        ret['delivery_date'] = data.get('delivery_date') or data.get('deliveryDate') or ret['target_delivery_date']
        
        if 'items' in data:
            ret['items'] = data.get('items') or []
        elif inst:
            ret['items'] = inst.items or []
        else:
            ret['items'] = []
            
        tot_val = data.get('total_amount') if 'total_amount' in data else (data.get('totalAmount') if 'totalAmount' in data else (data.get('subtotal') if 'subtotal' in data else (data.get('orderValue') if 'orderValue' in data else None)))
        if tot_val is not None:
            ret['total_amount'] = float(tot_val)
        elif inst:
            ret['total_amount'] = inst.total_amount
        else:
            ret['total_amount'] = 0.0

        tax_val = data.get('tax_amount') if 'tax_amount' in data else (data.get('taxAmount') if 'taxAmount' in data else None)
        if tax_val is not None:
            ret['tax_amount'] = float(tax_val)
        elif inst:
            ret['tax_amount'] = inst.tax_amount
        else:
            ret['tax_amount'] = 0.0

        gt_val = data.get('grand_total') if 'grand_total' in data else (data.get('grandTotal') if 'grandTotal' in data else (data.get('orderValue') if 'orderValue' in data else (data.get('order_value') if 'order_value' in data else None)))
        if gt_val is not None:
            ret['grand_total'] = float(gt_val)
        elif inst:
            ret['grand_total'] = inst.grand_total
        else:
            ret['grand_total'] = ret['total_amount']

        ret['order_value'] = float(data.get('order_value') or data.get('orderValue') or ret['grand_total'] or 0)
        ret['payment_terms'] = data.get('payment_terms') or data.get('paymentTerms') or (inst.payment_terms if inst else '')
        ret['billing_address'] = data.get('billing_address') or data.get('billingAddress') or (inst.billing_address if inst else '')
        ret['shipping_address'] = data.get('shipping_address') or data.get('shippingAddress') or (inst.shipping_address if inst else '')
        ret['status'] = data.get('status') or (inst.status if inst else 'confirmed')
        ret['project_id'] = data.get('project_id') or data.get('projectId') or (inst.project_id if inst else None)
        ret['job_number'] = data.get('job_number') or data.get('jobNumber') or (inst.job_number if inst else '')
        ret['assigned_project_manager'] = data.get('assigned_project_manager') or data.get('assignedProjectManager') or data.get('project_manager_name') or ''
        ret['created_by'] = data.get('created_by') or data.get('createdBy') or (inst.created_by if inst else '')
        ret['approved_by'] = data.get('approved_by') or data.get('approvedBy') or (inst.approved_by if inst else '')
        return ret

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['id'] = instance.id
        rep['salesOrderNumber'] = instance.sales_order_number
        rep['customerPoId'] = instance.customer_po_id
        rep['customerPoNumber'] = instance.customer_po_number
        rep['quotationId'] = instance.quotation_id
        rep['quotationNumber'] = instance.quotation_number
        rep['customerId'] = instance.customer_id
        rep['customerName'] = instance.customer_name
        rep['orderDate'] = instance.order_date
        rep['targetDeliveryDate'] = instance.target_delivery_date
        rep['deliveryDate'] = instance.delivery_date or instance.target_delivery_date
        rep['items'] = instance.items or []
        rep['totalAmount'] = instance.total_amount
        rep['taxAmount'] = instance.tax_amount
        rep['grandTotal'] = instance.grand_total
        rep['orderValue'] = instance.order_value or instance.grand_total
        rep['paymentTerms'] = instance.payment_terms
        rep['billingAddress'] = instance.billing_address
        rep['shippingAddress'] = instance.shipping_address
        rep['status'] = instance.status
        rep['projectId'] = instance.project_id
        rep['jobNumber'] = instance.job_number
        rep['assignedProjectManager'] = instance.assigned_project_manager
        rep['createdBy'] = instance.created_by
        rep['approvedBy'] = instance.approved_by
        return rep


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = [
            'id',
            'entity_type',
            'entity_id',
            'title',
            'description',
            'performed_by',
            'performed_at',
            'type',
        ]
