from rest_framework import serializers
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


class LeadSerializer(serializers.ModelSerializer):
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


class CustomerSerializer(serializers.ModelSerializer):
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


class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = [
            'id',
            'enquiry_no',
            'lead_id',
            'customer_id',
            'customer_name',
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


class QuotationSerializer(serializers.ModelSerializer):
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
        ret = {}
        ret['id'] = data.get('id') or data.get('quotationNumber') or data.get('quotation_number')
        ret['quotation_number'] = data.get('quotation_number') or data.get('quotationNumber') or ret.get('id')
        ret['current_revision'] = data.get('current_revision') or data.get('currentRevision') or 'Rev-00'
        ret['date'] = data.get('date') or datetime.now().strftime('%Y-%m-%d')
        ret['valid_until'] = data.get('valid_until') or data.get('validUntil') or ''
        ret['customer_id'] = data.get('customer_id') or data.get('customerId') or ''
        ret['customer_name'] = data.get('customer_name') or data.get('customerName') or ''
        ret['contact_person'] = data.get('contact_person') or data.get('contactPerson') or ''
        ret['contact_mobile'] = data.get('contact_mobile') or data.get('contactMobile') or ''
        ret['contact_email'] = data.get('contact_email') or data.get('contactEmail') or ''
        ret['enquiry_id'] = data.get('enquiry_id') or data.get('enquiryId') or None
        ret['opportunity_id'] = data.get('opportunity_id') or data.get('opportunityId') or None
        ret['sales_person_id'] = data.get('sales_person_id') or data.get('salesPersonId') or ''
        ret['sales_person_name'] = data.get('sales_person_name') or data.get('salesPersonName') or ''
        ret['revisions'] = data.get('revisions') or []
        ret['notes'] = data.get('notes') or ''
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
        rep['enquiryId'] = instance.enquiry_id
        rep['opportunityId'] = instance.opportunity_id
        rep['salesPersonId'] = instance.sales_person_id
        rep['salesPersonName'] = instance.sales_person_name
        rep['revisions'] = instance.revisions or []
        rep['notes'] = instance.notes
        
        # Calculate latestSummary for frontend convenience
        revs = instance.revisions or []
        last_rev = revs[-1] if revs else {}
        first_item = (last_rev.get('items') or [{}])[0]
        rep['latestSummary'] = {
            'machineProduct': first_item.get('productName', 'Process Equipment'),
            'grandTotal': last_rev.get('grandTotal', 0),
            'status': last_rev.get('status', 'draft')
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
    convertedSoId = serializers.CharField(source='converted_so_id', required=False, allow_blank=True, allow_null=True)
    salesOrderId = serializers.CharField(source='converted_so_id', required=False, allow_blank=True, allow_null=True)
    specialConditions = serializers.CharField(source='special_conditions', required=False, allow_blank=True)

    class Meta:
        model = CustomerPO
        fields = '__all__'

    def to_internal_value(self, data):
        ret = {}
        ret['id'] = data.get('id') or data.get('internal_cpo_no') or data.get('internalCpoNo') or data.get('po_number') or data.get('poNumber')
        ret['po_number'] = data.get('po_number') or data.get('poNumber') or ret.get('id') or 'PO/GEN'
        ret['internal_cpo_no'] = data.get('internal_cpo_no') or data.get('internalCpoNo') or ''
        ret['customer_id'] = data.get('customer_id') or data.get('customerId') or ''
        ret['customer_name'] = data.get('customer_name') or data.get('customerName') or ''
        ret['quotation_id'] = data.get('quotation_id') or data.get('quotationId') or None
        ret['quotation_number'] = data.get('quotation_number') or data.get('quotationNumber') or ''
        ret['po_date'] = data.get('po_date') or data.get('poDate') or datetime.now().strftime('%Y-%m-%d')
        ret['received_date'] = data.get('received_date') or data.get('receivedDate') or ret['po_date']
        ret['delivery_date'] = data.get('delivery_date') or data.get('deliveryDate') or ''
        ret['po_value'] = float(data.get('po_value') or data.get('poValue') or data.get('poAmount') or data.get('po_amount') or 0)
        ret['scope_of_work'] = data.get('scope_of_work') or data.get('scopeOfWork') or data.get('remarks') or ''
        ret['payment_terms'] = data.get('payment_terms') or data.get('paymentTerms') or ''
        ret['po_document_url'] = data.get('po_document_url') or data.get('poDocumentUrl') or ''
        ret['status'] = data.get('status') or 'received'
        ret['converted_so_id'] = data.get('converted_so_id') or data.get('convertedSoId') or data.get('salesOrderId') or None
        ret['special_conditions'] = data.get('special_conditions') or data.get('specialConditions') or ''
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
        rep['poAmount'] = instance.po_value
        rep['poValue'] = instance.po_value
        rep['scopeOfWork'] = instance.scope_of_work
        rep['paymentTerms'] = instance.payment_terms
        rep['poDocumentUrl'] = instance.po_document_url
        rep['status'] = instance.status
        rep['convertedSoId'] = instance.converted_so_id
        rep['salesOrderId'] = instance.converted_so_id
        rep['specialConditions'] = instance.special_conditions
        return rep


class SalesOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = [
            'id',
            'sales_order_number',
            'customer_po_id',
            'customer_po_number',
            'quotation_id',
            'quotation_number',
            'customer_id',
            'customer_name',
            'order_date',
            'target_delivery_date',
            'items',
            'total_amount',
            'tax_amount',
            'grand_total',
            'payment_terms',
            'billing_address',
            'shipping_address',
            'status',
            'project_id',
            'created_by',
            'approved_by',
        ]


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
