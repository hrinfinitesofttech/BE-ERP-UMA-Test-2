from django.db import models


class FinancialYear(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=64)
    fy_code = models.CharField(max_length=32, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=32, default='Active')
    closed_date = models.DateField(null=True, blank=True)
    closed_by = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f"{self.name} ({self.fy_code})"


class ChartOfAccount(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    account_code = models.CharField(max_length=64, unique=True)
    account_name = models.CharField(max_length=255)
    account_group = models.CharField(max_length=128, blank=True)
    category = models.CharField(max_length=64, default='Assets')
    account_type = models.CharField(max_length=64, default='Asset')
    opening_balance = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    current_balance = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    tax_applicability = models.BooleanField(default=False)
    status = models.CharField(max_length=32, default='Active')

    def __str__(self):
        return f"{self.account_code} - {self.account_name}"


class TaxMaster(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    tax_code = models.CharField(max_length=64, unique=True)
    tax_name = models.CharField(max_length=128)
    tax_type = models.CharField(max_length=64, default='GST Combination')
    rate_percent = models.DecimalField(max_digits=6, decimal_places=2, default=18.0)
    cgst_rate = models.DecimalField(max_digits=6, decimal_places=2, default=9.0)
    sgst_rate = models.DecimalField(max_digits=6, decimal_places=2, default=9.0)
    igst_rate = models.DecimalField(max_digits=6, decimal_places=2, default=18.0)
    hsn_sac_code = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=32, default='Active')

    def __str__(self):
        return f"{self.tax_name} ({self.rate_percent}%)"


class CostCenter(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    cost_center_code = models.CharField(max_length=64, unique=True)
    cost_center_name = models.CharField(max_length=128)
    department = models.CharField(max_length=128, blank=True)
    manager_name = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=32, default='Active')

    def __str__(self):
        return f"{self.cost_center_code} - {self.cost_center_name}"


class SalesInvoice(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    invoice_number = models.CharField(max_length=64, unique=True)
    invoice_date = models.DateField()
    due_date = models.DateField()
    customer_id = models.CharField(max_length=64)
    customer_name = models.CharField(max_length=255)
    customer_gstin = models.CharField(max_length=32, blank=True)
    place_of_supply = models.CharField(max_length=128, default='Gujarat (24)')
    sales_order_id = models.CharField(max_length=64, blank=True)
    sales_order_number = models.CharField(max_length=64, blank=True)
    customer_po_number = models.CharField(max_length=64, blank=True)
    project_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    payment_terms = models.CharField(max_length=128, blank=True)
    items = models.JSONField(default=list)
    taxable_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    cgst_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    sgst_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    igst_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    round_off = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    grand_total = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    paid_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    outstanding_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    status = models.CharField(max_length=64, default='Draft')
    payment_status = models.CharField(max_length=64, default='Unpaid')
    created_by = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-invoice_date']

    def __str__(self):
        return f"{self.invoice_number} - {self.customer_name} (₹{self.grand_total})"


class PurchaseInvoice(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    invoice_number = models.CharField(max_length=64, unique=True)
    vendor_invoice_number = models.CharField(max_length=128, blank=True)
    invoice_date = models.DateField()
    due_date = models.DateField()
    supplier_id = models.CharField(max_length=64)
    supplier_name = models.CharField(max_length=255)
    supplier_gstin = models.CharField(max_length=32, blank=True)
    po_number = models.CharField(max_length=64, blank=True)
    grn_number = models.CharField(max_length=64, blank=True)
    project_id = models.CharField(max_length=64, blank=True)
    job_number = models.CharField(max_length=64, blank=True)
    payment_terms = models.CharField(max_length=128, blank=True)
    items = models.JSONField(default=list)
    taxable_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    cgst_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    sgst_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    igst_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    grand_total = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    paid_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    outstanding_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    status = models.CharField(max_length=64, default='Draft')
    payment_status = models.CharField(max_length=64, default='Unpaid')
    created_by = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-invoice_date']

    def __str__(self):
        return f"{self.invoice_number} - {self.supplier_name}"


class CustomerReceipt(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    receipt_number = models.CharField(max_length=64, unique=True)
    receipt_date = models.DateField()
    customer_id = models.CharField(max_length=64)
    customer_name = models.CharField(max_length=255)
    sales_invoice_number = models.CharField(max_length=64, blank=True)
    payment_mode = models.CharField(max_length=64, default='Bank Transfer')
    bank_name = models.CharField(max_length=128, blank=True)
    amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    reference_number = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=64, default='Received')
    remarks = models.TextField(blank=True)
    created_by = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f"{self.receipt_number} - {self.customer_name} (₹{self.amount})"


class SupplierPayment(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    payment_number = models.CharField(max_length=64, unique=True)
    payment_date = models.DateField()
    supplier_id = models.CharField(max_length=64)
    supplier_name = models.CharField(max_length=255)
    purchase_invoice_number = models.CharField(max_length=64, blank=True)
    payment_mode = models.CharField(max_length=64, default='Bank Transfer')
    bank_name = models.CharField(max_length=128, blank=True)
    amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    reference_number = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=64, default='Paid')
    remarks = models.TextField(blank=True)
    created_by = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f"{self.payment_number} - {self.supplier_name} (₹{self.amount})"


class JournalEntry(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    journal_number = models.CharField(max_length=64, unique=True)
    journal_date = models.DateField()
    voucher_type = models.CharField(max_length=64, default='Journal')
    narration = models.TextField()
    lines = models.JSONField(default=list)
    total_debit = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    total_credit = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    status = models.CharField(max_length=64, default='Posted')
    created_by = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f"{self.journal_number} ({self.voucher_type})"


class JobCostingSummary(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    job_number = models.CharField(max_length=64, unique=True)
    product_name = models.CharField(max_length=255, blank=True)
    customer_name = models.CharField(max_length=255, blank=True)
    sales_order_value = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    invoiced_value = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    received_value = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    material_cost = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    labour_cost = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    machine_cost = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    subcontract_cost = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    overhead_cost = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    total_actual_cost = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    profit = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    margin_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Costing: {self.job_number} - Margin: {self.margin_percent}%"
