from django.db import models
import uuid


class Lead(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    lead_no = models.CharField(max_length=64, unique=True)
    company_name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100, blank=True, default='')
    website = models.CharField(max_length=200, blank=True, default='')
    gstin = models.CharField(max_length=30, blank=True, default='')
    address = models.TextField(blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=20, blank=True, default='')
    contact_person = models.CharField(max_length=150)
    designation = models.CharField(max_length=100, blank=True, default='')
    mobile = models.CharField(max_length=30)
    alt_mobile = models.CharField(max_length=30, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    whatsapp = models.CharField(max_length=30, blank=True, default='')
    product_name = models.CharField(max_length=200)
    machine_type = models.CharField(max_length=100, blank=True, default='')
    quantity = models.IntegerField(default=1)
    capacity = models.CharField(max_length=100, blank=True, default='')
    application = models.CharField(max_length=150, blank=True, default='')
    requirement_description = models.TextField(blank=True, default='')
    expected_delivery = models.CharField(max_length=50, blank=True, default='')
    budget = models.FloatField(default=0)
    priority = models.CharField(max_length=20, default='medium')
    source = models.CharField(max_length=50, default='website')
    assigned_sales_person_id = models.CharField(max_length=64, blank=True, default='')
    assigned_sales_person_name = models.CharField(max_length=150, blank=True, default='')
    status = models.CharField(max_length=50, default='new')
    next_follow_up_date = models.CharField(max_length=50, blank=True, default='')
    remarks = models.TextField(blank=True, default='')
    created_date = models.CharField(max_length=50, blank=True, default='')
    converted_customer_id = models.CharField(max_length=64, blank=True, null=True)
    converted_enquiry_id = models.CharField(max_length=64, blank=True, null=True)
    converted_opportunity_id = models.CharField(max_length=64, blank=True, null=True)
    attachments = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.lead_no} - {self.company_name}"


class Customer(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    customer_code = models.CharField(max_length=50, unique=True)
    customer_type = models.CharField(max_length=30, default='company')
    company_name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100, blank=True, default='')
    gstin = models.CharField(max_length=30, blank=True, default='')
    pan = models.CharField(max_length=30, blank=True, default='')
    website = models.CharField(max_length=200, blank=True, default='')
    contact_person = models.CharField(max_length=150)
    designation = models.CharField(max_length=100, blank=True, default='')
    mobile = models.CharField(max_length=30)
    email = models.EmailField(blank=True, default='')
    whatsapp = models.CharField(max_length=30, blank=True, default='')
    billing_address = models.TextField(blank=True, default='')
    shipping_address = models.TextField(blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=20, blank=True, default='')
    payment_terms = models.CharField(max_length=255, default='30% advance, balance against PI')
    credit_limit = models.FloatField(default=0)
    currency = models.CharField(max_length=30, default='INR (₹)')
    category = models.CharField(max_length=30, default='standard')
    assigned_sales_person = models.CharField(max_length=150, blank=True, default='')
    created_date = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer_code} - {self.company_name}"


class Contact(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    customer_ref = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='contacts', null=True, blank=True)
    customer_id = models.CharField(max_length=64)
    customer_name = models.CharField(max_length=200)
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=100, blank=True, default='')
    department = models.CharField(max_length=100, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    mobile = models.CharField(max_length=30)
    whatsapp = models.CharField(max_length=30, blank=True, default='')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.customer_name})"


class Enquiry(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    enquiry_no = models.CharField(max_length=64, unique=True)
    lead_id = models.CharField(max_length=64, blank=True, null=True)
    customer_id = models.CharField(max_length=64)
    customer_name = models.CharField(max_length=200)
    enquiry_date = models.CharField(max_length=50)
    requirement = models.TextField()
    machine_product = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    specification = models.TextField(blank=True, default='')
    expected_delivery = models.CharField(max_length=50, blank=True, default='')
    assigned_person_id = models.CharField(max_length=64, blank=True, default='')
    assigned_person_name = models.CharField(max_length=150, blank=True, default='')
    status = models.CharField(max_length=50, default='new')
    quotation_id = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Enquiry'
        verbose_name_plural = 'Enquiries'

    def __str__(self):
        return f"{self.enquiry_no} - {self.customer_name}"


class Opportunity(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    opportunity_no = models.CharField(max_length=64, unique=True)
    lead_id = models.CharField(max_length=64, blank=True, null=True)
    customer_id = models.CharField(max_length=64)
    customer_name = models.CharField(max_length=200)
    machine_product = models.CharField(max_length=200)
    estimated_value = models.FloatField(default=0)
    expected_closing_date = models.CharField(max_length=50, blank=True, default='')
    sales_person_id = models.CharField(max_length=64, blank=True, default='')
    sales_person_name = models.CharField(max_length=150, blank=True, default='')
    probability = models.IntegerField(default=50)
    stage = models.CharField(max_length=50, default='qualification')
    remarks = models.TextField(blank=True, default='')
    quotation_id = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Opportunity'
        verbose_name_plural = 'Opportunities'

    def __str__(self):
        return f"{self.opportunity_no} - {self.customer_name}"


class FollowUp(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    follow_up_no = models.CharField(max_length=64, unique=True)
    lead_or_customer_id = models.CharField(max_length=64)
    lead_or_customer_name = models.CharField(max_length=200)
    entity_type = models.CharField(max_length=30, default='lead')
    type = models.CharField(max_length=30, default='call')
    assigned_to_id = models.CharField(max_length=64, blank=True, default='')
    assigned_to_name = models.CharField(max_length=150, blank=True, default='')
    date = models.CharField(max_length=30)
    time = models.CharField(max_length=30, blank=True, default='')
    priority = models.CharField(max_length=30, default='medium')
    purpose = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')
    next_follow_up_date = models.CharField(max_length=30, blank=True, default='')
    status = models.CharField(max_length=30, default='pending')
    completed_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.follow_up_no} - {self.lead_or_customer_name}"


class SiteVisit(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    visit_no = models.CharField(max_length=64, unique=True)
    customer_id = models.CharField(max_length=64)
    customer_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150)
    contact_mobile = models.CharField(max_length=30)
    visit_date = models.CharField(max_length=50)
    location = models.CharField(max_length=200)
    employee_id = models.CharField(max_length=64, blank=True, default='')
    employee_name = models.CharField(max_length=150, blank=True, default='')
    purpose = models.TextField(blank=True, default='')
    discussion_notes = models.TextField(blank=True, default='')
    requirement_details = models.TextField(blank=True, default='')
    outcome = models.CharField(max_length=50, default='positive')
    next_action = models.CharField(max_length=200, blank=True, default='')
    next_follow_up_date = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.visit_no} - {self.customer_name}"


class Exhibition(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    expo_name = models.CharField(max_length=200)
    organizer = models.CharField(max_length=200, blank=True, default='')
    location = models.CharField(max_length=200)
    start_date = models.CharField(max_length=30)
    end_date = models.CharField(max_length=30)
    stall_number = models.CharField(max_length=50, blank=True, default='')
    contact_person = models.CharField(max_length=150, blank=True, default='')
    budget = models.FloatField(default=0)
    assigned_team = models.JSONField(default=list, blank=True)
    products_displayed = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')
    total_contacts = models.IntegerField(default=0)
    qualified_leads = models.IntegerField(default=0)
    quotations_sent = models.IntegerField(default=0)
    converted_customers = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.expo_name


class Quotation(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    quotation_number = models.CharField(max_length=64, unique=True)
    current_revision = models.CharField(max_length=30, default='Rev-00')
    date = models.CharField(max_length=50)
    valid_until = models.CharField(max_length=50)
    customer_id = models.CharField(max_length=64)
    customer_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150)
    contact_mobile = models.CharField(max_length=30, blank=True, default='')
    contact_email = models.EmailField(blank=True, default='')
    enquiry_id = models.CharField(max_length=64, blank=True, null=True)
    opportunity_id = models.CharField(max_length=64, blank=True, null=True)
    sales_person_id = models.CharField(max_length=64, blank=True, default='')
    sales_person_name = models.CharField(max_length=150, blank=True, default='')
    revisions = models.JSONField(default=list, blank=True)
    items = models.JSONField(default=list, blank=True)
    subtotal = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    total_amount = models.FloatField(default=0)
    status = models.CharField(max_length=50, default='draft')
    approved_by = models.CharField(max_length=150, blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quotation_number} - {self.customer_name}"


class CustomerPO(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    po_number = models.CharField(max_length=100)
    internal_cpo_no = models.CharField(max_length=64, blank=True, default='')
    customer_id = models.CharField(max_length=64)
    customer_name = models.CharField(max_length=200)
    quotation_id = models.CharField(max_length=64, blank=True, null=True)
    quotation_number = models.CharField(max_length=64, blank=True, default='')
    po_date = models.CharField(max_length=50)
    received_date = models.CharField(max_length=50)
    delivery_date = models.CharField(max_length=50)
    po_value = models.FloatField(default=0)
    scope_of_work = models.TextField(blank=True, default='')
    payment_terms = models.TextField(blank=True, default='')
    po_document_url = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(max_length=50, default='received')
    converted_so_id = models.CharField(max_length=64, blank=True, null=True)
    special_conditions = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Customer PO'
        verbose_name_plural = 'Customer POs'

    def __str__(self):
        return f"{self.po_number} ({self.customer_name})"


class SalesOrder(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    sales_order_number = models.CharField(max_length=64, unique=True)
    customer_po_id = models.CharField(max_length=64, blank=True, null=True)
    customer_po_number = models.CharField(max_length=100, blank=True, default='')
    quotation_id = models.CharField(max_length=64, blank=True, null=True)
    quotation_number = models.CharField(max_length=64, blank=True, default='')
    customer_id = models.CharField(max_length=64)
    customer_name = models.CharField(max_length=200)
    order_date = models.CharField(max_length=50)
    target_delivery_date = models.CharField(max_length=50)
    items = models.JSONField(default=list, blank=True)
    total_amount = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    payment_terms = models.CharField(max_length=255, blank=True, default='')
    billing_address = models.TextField(blank=True, default='')
    shipping_address = models.TextField(blank=True, default='')
    status = models.CharField(max_length=50, default='confirmed')
    project_id = models.CharField(max_length=64, blank=True, null=True)
    job_number = models.CharField(max_length=64, blank=True, default='')
    created_by = models.CharField(max_length=150, blank=True, default='')
    approved_by = models.CharField(max_length=150, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sales_order_number} - {self.customer_name}"


class Activity(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    entity_type = models.CharField(max_length=30) # lead, customer, opportunity, quotation, sales_order
    entity_id = models.CharField(max_length=64)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    performed_by = models.CharField(max_length=150)
    performed_at = models.CharField(max_length=60)
    type = models.CharField(max_length=30, default='note')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'

    def __str__(self):
        return f"{self.title} on {self.entity_type}:{self.entity_id}"
