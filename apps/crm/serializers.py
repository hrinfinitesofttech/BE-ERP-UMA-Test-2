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
    class Meta:
        model = Quotation
        fields = [
            'id',
            'quotation_number',
            'current_revision',
            'date',
            'valid_until',
            'customer_id',
            'customer_name',
            'contact_person',
            'contact_mobile',
            'contact_email',
            'enquiry_id',
            'opportunity_id',
            'sales_person_id',
            'sales_person_name',
            'revisions',
            'notes',
        ]


class CustomerPOSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerPO
        fields = [
            'id',
            'po_number',
            'internal_cpo_no',
            'customer_id',
            'customer_name',
            'quotation_id',
            'quotation_number',
            'po_date',
            'received_date',
            'delivery_date',
            'po_value',
            'scope_of_work',
            'payment_terms',
            'po_document_url',
            'status',
            'converted_so_id',
            'special_conditions',
        ]


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
