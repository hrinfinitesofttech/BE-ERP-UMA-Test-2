from django.contrib import admin
from .models import Lead, Customer, Contact, Enquiry, Opportunity, FollowUp, SiteVisit, Exhibition, Quotation, CustomerPO, SalesOrder, Activity

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('id', 'lead_no', 'company_name', 'industry', 'website', 'gstin')
    search_fields = ('id', 'lead_no', 'company_name', 'pincode')
    list_filter = ('machine_type', 'status', 'created_at', 'updated_at')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_code', 'customer_type', 'company_name', 'industry', 'gstin')
    search_fields = ('id', 'customer_code', 'company_name', 'email')
    list_filter = ('customer_type', 'category', 'created_at', 'updated_at')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_ref', 'customer_id', 'customer_name', 'name', 'designation')
    search_fields = ('id', 'customer_id', 'customer_name', 'name')
    list_filter = ('is_primary',)

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ('id', 'enquiry_no', 'lead_id', 'customer_id', 'customer_name', 'enquiry_date')
    search_fields = ('id', 'enquiry_no', 'lead_id', 'customer_id')
    list_filter = ('status', 'created_at', 'updated_at')

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('id', 'opportunity_no', 'lead_id', 'customer_id', 'customer_name', 'machine_product')
    search_fields = ('id', 'opportunity_no', 'lead_id', 'customer_id')
    list_filter = ('created_at', 'updated_at')

@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ('id', 'follow_up_no', 'lead_or_customer_id', 'lead_or_customer_name', 'entity_type', 'type')
    search_fields = ('id', 'follow_up_no', 'lead_or_customer_id', 'lead_or_customer_name')
    list_filter = ('entity_type', 'type', 'status', 'created_at')

@admin.register(SiteVisit)
class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ('id', 'visit_no', 'customer_id', 'customer_name', 'contact_person', 'contact_mobile')
    search_fields = ('id', 'visit_no', 'customer_id', 'customer_name')
    list_filter = ('created_at', 'updated_at')

@admin.register(Exhibition)
class ExhibitionAdmin(admin.ModelAdmin):
    list_display = ('id', 'expo_name', 'organizer', 'location', 'start_date', 'end_date')
    search_fields = ('id', 'expo_name', 'stall_number')
    list_filter = ('created_at', 'updated_at')

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('id', 'quotation_number', 'current_revision', 'date', 'valid_until', 'customer_id')
    search_fields = ('id', 'quotation_number', 'valid_until', 'customer_id')
    list_filter = ('created_at', 'updated_at')

@admin.register(CustomerPO)
class CustomerPOAdmin(admin.ModelAdmin):
    list_display = ('id', 'po_number', 'internal_cpo_no', 'customer_id', 'customer_name', 'quotation_id')
    search_fields = ('id', 'po_number', 'internal_cpo_no', 'customer_id')
    list_filter = ('status', 'created_at', 'updated_at')

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'sales_order_number', 'customer_po_id', 'customer_po_number', 'quotation_id', 'quotation_number')
    search_fields = ('id', 'sales_order_number', 'customer_po_id', 'customer_po_number')
    list_filter = ('status', 'created_at', 'updated_at')

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'entity_type', 'entity_id', 'title', 'performed_by', 'performed_at')
    search_fields = ('id', 'entity_id', 'title')
    list_filter = ('entity_type', 'type', 'created_at')
