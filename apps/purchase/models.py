from django.db import models


class Supplier(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    vendor_code = models.CharField(max_length=64, unique=True)
    supplier_code = models.CharField(max_length=64, blank=True, default='')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, default='Raw Material')
    supplier_type = models.CharField(max_length=100, default='Manufacturer')
    contact_person = models.CharField(max_length=150)
    mobile = models.CharField(max_length=30, blank=True, default='')
    phone = models.CharField(max_length=30, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    address = models.TextField(blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=20, blank=True, default='')
    gstin = models.CharField(max_length=30, blank=True, default='')
    pan = models.CharField(max_length=30, blank=True, default='')
    bank_name = models.CharField(max_length=150, blank=True, default='')
    bank_account_number = models.CharField(max_length=64, blank=True, default='')
    ifsc_code = models.CharField(max_length=32, blank=True, default='')
    credit_period_days = models.IntegerField(default=30)
    msme_number = models.CharField(max_length=64, blank=True, default='')
    msme_registered = models.BooleanField(default=False)
    payment_terms = models.CharField(max_length=200, default='30 Days Credit')
    rating = models.FloatField(default=4.5)
    notes = models.TextField(blank=True, default='')
    status = models.CharField(max_length=30, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vendor_code} - {self.name}"


class SupplierContact(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    supplier_id = models.CharField(max_length=64)
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=100, blank=True, default='')
    department = models.CharField(max_length=100, blank=True, default='')
    mobile = models.CharField(max_length=30, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.supplier_id})"


class PurchaseRequisition(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    pr_number = models.CharField(max_length=64, unique=True)
    project_id = models.CharField(max_length=64, blank=True, default='')
    job_code = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    bom_number = models.CharField(max_length=64, blank=True, default='')
    requested_by = models.CharField(max_length=150)
    department = models.CharField(max_length=50, default='Production')
    request_date = models.CharField(max_length=50)
    required_by_date = models.CharField(max_length=50)
    priority = models.CharField(max_length=30, default='high')
    status = models.CharField(max_length=50, default='pending_approval') # draft, submitted, pending_approval, approved, rejected, converted_to_rfq
    items = models.JSONField(default=list, blank=True)
    total_estimated_cost = models.FloatField(default=0)
    remarks = models.TextField(blank=True, default='')
    approved_by = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.pr_number} ({self.status})"


class RequestForQuotation(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    rfq_number = models.CharField(max_length=64, unique=True)
    pr_id = models.CharField(max_length=64, blank=True, default='')
    rfq_date = models.CharField(max_length=50)
    due_date = models.CharField(max_length=50)
    suppliers = models.JSONField(default=list, blank=True)
    items = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=50, default='sent') # draft, sent, closed
    terms_and_conditions = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.rfq_number


class SupplierQuotation(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    quotation_number = models.CharField(max_length=64)
    rfq_id = models.CharField(max_length=64, blank=True, default='')
    supplier_id = models.CharField(max_length=64)
    supplier_name = models.CharField(max_length=200)
    date = models.CharField(max_length=50)
    valid_until = models.CharField(max_length=50)
    items = models.JSONField(default=list, blank=True)
    sub_total = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    delivery_lead_time = models.CharField(max_length=100, blank=True, default='')
    payment_terms = models.CharField(max_length=200, blank=True, default='')
    status = models.CharField(max_length=50, default='received')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quotation_number} - {self.supplier_name}"


class QuotationComparison(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    rfq_id = models.CharField(max_length=64)
    comparison_date = models.CharField(max_length=50)
    items = models.JSONField(default=list, blank=True)
    supplier_quotations = models.JSONField(default=list, blank=True)
    recommended_supplier_id = models.CharField(max_length=64, blank=True, default='')
    recommended_supplier_name = models.CharField(max_length=200, blank=True, default='')
    recommendation_reason = models.TextField(blank=True, default='')
    prepared_by = models.CharField(max_length=150)
    approved_by = models.CharField(max_length=150, blank=True, null=True)
    status = models.CharField(max_length=50, default='approved')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CS for RFQ: {self.rfq_id}"


class PurchaseOrder(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    po_number = models.CharField(max_length=64, unique=True)
    revision_number = models.CharField(max_length=30, default='Rev-00')
    date = models.CharField(max_length=50)
    supplier_id = models.CharField(max_length=64)
    supplier_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150, blank=True, default='')
    supplier_gstin = models.CharField(max_length=30, blank=True, default='')
    supplier_address = models.TextField(blank=True, default='')
    billing_address = models.TextField(blank=True, default='')
    shipping_address = models.TextField(blank=True, default='')
    project_id = models.CharField(max_length=64, blank=True, default='')
    job_code = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    delivery_date = models.CharField(max_length=50)
    payment_terms = models.CharField(max_length=200, default='30 Days Credit')
    currency = models.CharField(max_length=10, default='INR')
    items = models.JSONField(default=list, blank=True)
    sub_total = models.FloatField(default=0)
    discount_amount = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    freight_charges = models.FloatField(default=0)
    other_charges = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    status = models.CharField(max_length=50, default='approved') # draft, pending_approval, approved, sent_to_supplier, partially_received, fully_received, closed, cancelled
    terms_and_conditions = models.TextField(blank=True, default='')
    remarks = models.TextField(blank=True, default='')
    prepared_by = models.CharField(max_length=150)
    approved_by = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.po_number} - {self.supplier_name}"


class PurchaseReturn(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    return_number = models.CharField(max_length=64, unique=True)
    po_id = models.CharField(max_length=64, blank=True, default='')
    po_number = models.CharField(max_length=64, blank=True, default='')
    grn_id = models.CharField(max_length=64, blank=True, default='')
    grn_number = models.CharField(max_length=64, blank=True, default='')
    supplier_id = models.CharField(max_length=64)
    supplier_name = models.CharField(max_length=200)
    date = models.CharField(max_length=50)
    reason = models.TextField()
    items = models.JSONField(default=list, blank=True)
    total_amount = models.FloatField(default=0)
    status = models.CharField(max_length=50, default='completed')
    debit_note_number = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.return_number} to {self.supplier_name}"


class MaterialRequirement(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    project_id = models.CharField(max_length=64, blank=True, default='')
    job_id = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    customer_name = models.CharField(max_length=200, blank=True, default='')
    design_job_id = models.CharField(max_length=64, blank=True, default='')
    bom_id = models.CharField(max_length=64, blank=True, default='')
    bom_number = models.CharField(max_length=64, blank=True, default='')
    bom_revision = models.CharField(max_length=30, default='REV-01')
    part_number = models.CharField(max_length=100, blank=True, default='')
    item_code = models.CharField(max_length=100, blank=True, default='')
    item_name = models.CharField(max_length=200)
    material_name = models.CharField(max_length=200, blank=True, default='')
    specification = models.TextField(blank=True, default='')
    category = models.CharField(max_length=100, default='Raw Material')
    required_quantity = models.FloatField(default=0)
    unit_of_measure = models.CharField(max_length=30, default='NOS')
    available_stock = models.FloatField(default=0)
    reserved_stock = models.FloatField(default=0)
    on_order_quantity = models.FloatField(default=0)
    shortage_quantity = models.FloatField(default=0)
    required_by_date = models.CharField(max_length=50, blank=True, default='')
    procurement_type = models.CharField(max_length=50, default='Purchase')
    procurement_status = models.CharField(max_length=50, default='Pending')
    drawing_number = models.CharField(max_length=100, blank=True, default='')
    status = models.CharField(max_length=50, default='shortage')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name} ({self.job_id}) - Shortage: {self.shortage_quantity}"

