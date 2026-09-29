from django.db import models
import uuid


class CompanySetting(models.Model):
    company_name = models.CharField(max_length=200, default='Uma Techno Fab Private Limited')
    tagline = models.CharField(
        max_length=255,
        default='Custom Heavy Fabrication & Make-to-Order Equipment Manufacturer'
    )
    logo_url = models.CharField(max_length=255, default='/logo.png')
    address = models.TextField(default='Plot No. 48/B, GIDC Industrial Estate, Makarpura')
    city = models.CharField(max_length=100, default='Vadodara')
    state = models.CharField(max_length=100, default='Gujarat')
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=20, default='390010')
    phone = models.CharField(max_length=100, default='+91 265 2645800 / +91 98250 11223')
    email = models.EmailField(default='info@umatechnofab.com')
    website = models.CharField(max_length=200, default='https://www.umatechnofab.com')
    gstin = models.CharField(max_length=30, default='24AABCU9821R1ZX')
    pan = models.CharField(max_length=20, default='AABCU9821R')
    cin = models.CharField(max_length=50, default='U28112GJ2012PTC071234')
    financial_year = models.CharField(max_length=20, default='2026-2027')
    currency = models.CharField(max_length=30, default='INR (₹)')
    timezone = models.CharField(max_length=50, default='Asia/Kolkata (IST)')
    bank_name = models.CharField(max_length=150, default='State Bank of India')
    bank_account_no = models.CharField(max_length=50, default='30491827461')
    bank_ifsc = models.CharField(max_length=30, default='SBIN0001234')
    bank_branch = models.CharField(max_length=150, default='Industrial Estate Branch, Vadodara')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name


class NumberingSetting(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    module = models.CharField(max_length=50) # e.g. CRM, Project
    doc_type = models.CharField(max_length=50, unique=True) # e.g. lead, quotation, customer_po, sales_order, project, job, enquiry, opportunity, visit, invoice
    prefix = models.CharField(max_length=50)
    suffix = models.CharField(max_length=50, blank=True, default='')
    current_number = models.IntegerField(default=1)
    digit_count = models.IntegerField(default=4)
    sample_preview = models.CharField(max_length=100, blank=True, default='')

    def __str__(self):
        return f"{self.doc_type} ({self.prefix})"

    def generate_next_number(self, increment=True):
        next_num = self.current_number + (1 if increment else 0)
        formatted_num = str(next_num).zfill(self.digit_count)
        result = f"{self.prefix}{formatted_num}{self.suffix}"
        if increment:
            self.current_number = next_num
            self.sample_preview = result
            self.save(update_fields=['current_number', 'sample_preview'])
        return result


class AuditLog(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user_id = models.CharField(max_length=64)
    user_name = models.CharField(max_length=150)
    role = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    action = models.CharField(max_length=50) # CREATE, UPDATE, DELETE, APPROVE, REJECT, LOGIN, LOGOUT
    module = models.CharField(max_length=100)
    page = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100)
    old_value = models.TextField(blank=True, default='')
    new_value = models.TextField(blank=True, default='')
    ip_address = models.CharField(max_length=60, blank=True, default='')
    notes = models.TextField(blank=True, default='')

    def __str__(self):
        return f"[{self.action}] {self.module}/{self.page} by {self.user_name} on {self.record_id}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"aud-{uuid.uuid4().hex[:10]}"
        super().save(*args, **kwargs)


class Notification(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=50, default='info') # info, warning, success, alert, approval_request
    department = models.CharField(max_length=50, default='all')
    link_url = models.CharField(max_length=255, blank=True, default='')
    is_read = models.BooleanField(default=False)
    priority = models.CharField(max_length=20, default='normal')

    def __str__(self):
        return f"{self.title} ({self.priority})"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"notif-{uuid.uuid4().hex[:10]}"
        super().save(*args, **kwargs)


class BugTicket(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    bug_no = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    module_page = models.CharField(max_length=100, blank=True, default='')
    severity = models.CharField(max_length=30, default='Medium')
    priority = models.CharField(max_length=30, default='Normal')
    status = models.CharField(max_length=30, default='Open')
    assignee = models.CharField(max_length=150, blank=True, default='')
    steps_to_reproduce = models.TextField(blank=True, default='')
    actual_result = models.TextField(blank=True, default='')
    expected_result = models.TextField(blank=True, default='')
    fixed_notes = models.TextField(blank=True, default='')
    created_date = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bug_no} - {self.title}"


class BackupRecord(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    backup_name = models.CharField(max_length=200)
    backup_type = models.CharField(max_length=50, default='Full Database & Media')
    file_size = models.CharField(max_length=50, default='24.5 MB')
    status = models.CharField(max_length=30, default='Completed')
    backup_date = models.CharField(max_length=50)
    file_url = models.CharField(max_length=255, blank=True, default='')
    created_by = models.CharField(max_length=150, default='Super Admin')
    is_automatic = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.backup_name} ({self.status})"


class DataImportLog(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    entity_type = models.CharField(max_length=100) # Customers, Items, Suppliers, Leads, BOMs, Invoices, Employees
    file_name = models.CharField(max_length=200)
    records_count = models.IntegerField(default=0)
    status = models.CharField(max_length=30, default='Completed') # Completed, In Progress, Failed
    imported_by = models.CharField(max_length=150, default='Super Admin')
    imported_at = models.CharField(max_length=50)
    error_summary = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.entity_type} ({self.records_count} records) - {self.status}"


class SecurityCheckRecord(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    check_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, default='Authentication & Access')
    status = models.CharField(max_length=30, default='Pass') # Pass, Warning, Fail
    severity = models.CharField(max_length=30, default='High')
    description = models.TextField(blank=True, default='')
    remediation_notes = models.TextField(blank=True, default='')
    last_evaluated_at = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.check_name} [{self.status}]"


class GoLiveChecklistItem(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    module_name = models.CharField(max_length=100)
    item_title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    owner = models.CharField(max_length=150, default='Super Admin')
    status = models.CharField(max_length=30, default='Pass') # Pass, Pending, Blocked
    signoff_date = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.module_name}: {self.item_title} ({self.status})"


