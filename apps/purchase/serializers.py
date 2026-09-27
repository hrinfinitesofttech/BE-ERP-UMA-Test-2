from rest_framework import serializers
from .models import (
    Supplier,
    SupplierContact,
    PurchaseRequisition,
    RequestForQuotation,
    SupplierQuotation,
    QuotationComparison,
    PurchaseOrder,
    PurchaseReturn,
)


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


class SupplierSerializer(serializers.ModelSerializer):
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


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequisition
        fields = [
            'id',
            'pr_number',
            'project_id',
            'job_code',
            'requested_by',
            'department',
            'request_date',
            'required_by_date',
            'priority',
            'status',
            'items',
            'total_estimated_cost',
            'remarks',
            'approved_by',
        ]


class RequestForQuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestForQuotation
        fields = [
            'id',
            'rfq_number',
            'pr_id',
            'rfq_date',
            'due_date',
            'suppliers',
            'items',
            'status',
            'terms_and_conditions',
        ]


class SupplierQuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierQuotation
        fields = [
            'id',
            'quotation_number',
            'rfq_id',
            'supplier_id',
            'supplier_name',
            'date',
            'valid_until',
            'items',
            'sub_total',
            'tax_amount',
            'grand_total',
            'delivery_lead_time',
            'payment_terms',
            'status',
        ]


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
        fields = [
            'id',
            'po_number',
            'revision_number',
            'date',
            'supplier_id',
            'supplier_name',
            'contact_person',
            'supplier_gstin',
            'supplier_address',
            'project_id',
            'job_code',
            'delivery_date',
            'payment_terms',
            'items',
            'sub_total',
            'discount_amount',
            'tax_amount',
            'grand_total',
            'status',
            'prepared_by',
            'approved_by',
        ]


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
