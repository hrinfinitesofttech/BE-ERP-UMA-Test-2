from django.db import models


class ItemCategory(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.code} - {self.name}"


class UOMMaster(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return self.code


class ItemMaster(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    item_code = models.CharField(max_length=64, unique=True)
    item_name = models.CharField(max_length=200)
    item_type = models.CharField(max_length=100, default='Raw Material')
    category = models.CharField(max_length=100)
    sub_category = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField(blank=True, default='')
    specification = models.TextField(blank=True, default='')
    drawing_number = models.CharField(max_length=100, blank=True, default='')
    brand_make = models.CharField(max_length=100, blank=True, default='')
    hsn_sac = models.CharField(max_length=50, default='7219')
    gst_rate = models.FloatField(default=18.0)
    uom = models.CharField(max_length=30, default='Kg')
    minimum_stock = models.FloatField(default=0)
    maximum_stock = models.FloatField(default=0)
    reorder_level = models.FloatField(default=0)
    unit_cost = models.FloatField(default=0)
    status = models.CharField(max_length=30, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_code} - {self.item_name}"


class Warehouse(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    warehouse_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    warehouse_type = models.CharField(max_length=100, default='Main Store')
    location = models.CharField(max_length=200, default='Makarpura Unit 1')
    incharge = models.CharField(max_length=150, default='Hitesh Rawal')
    status = models.CharField(max_length=30, default='Active')

    def __str__(self):
        return f"{self.warehouse_code} - {self.name}"


class WarehouseLocation(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    warehouse_id = models.CharField(max_length=64)
    rack = models.CharField(max_length=50)
    bin = models.CharField(max_length=50)
    shelf = models.CharField(max_length=50, blank=True, default='')
    code = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.code


class GoodsReceiptNote(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    grn_number = models.CharField(max_length=64, unique=True)
    date = models.CharField(max_length=50)
    po_id = models.CharField(max_length=64, blank=True, default='')
    po_number = models.CharField(max_length=64, blank=True, default='')
    supplier_id = models.CharField(max_length=64)
    supplier_name = models.CharField(max_length=200)
    challan_number = models.CharField(max_length=100, blank=True, default='')
    challan_date = models.CharField(max_length=50, blank=True, default='')
    invoice_number = models.CharField(max_length=100, blank=True, default='')
    invoice_date = models.CharField(max_length=50, blank=True, default='')
    vehicle_number = models.CharField(max_length=50, blank=True, default='')
    received_by = models.CharField(max_length=150)
    warehouse_id = models.CharField(max_length=64, default='wh-main')
    items = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=50, default='Accepted') # Draft, Received, Inspection Pending, Accepted, Rejected
    qc_status = models.CharField(max_length=50, default='Pass') # Pass, Fail, Pending
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.grn_number} from {self.supplier_name}"


class QCInspection(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    grn_id = models.CharField(max_length=64)
    grn_number = models.CharField(max_length=64)
    inspection_date = models.CharField(max_length=50)
    inspector = models.CharField(max_length=150)
    items = models.JSONField(default=list, blank=True)
    overall_result = models.CharField(max_length=50, default='Pass') # Pass, Fail, Conditional Approval
    remarks = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QC for {self.grn_number}: {self.overall_result}"


class StockBalance(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    item_id = models.CharField(max_length=64)
    item_code = models.CharField(max_length=64)
    item_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, default='Raw Material')
    uom = models.CharField(max_length=30, default='Kg')
    warehouse_id = models.CharField(max_length=64, default='wh-main')
    warehouse_name = models.CharField(max_length=200, default='Main Raw Material Warehouse')
    location = models.CharField(max_length=100, blank=True, default='')
    quantity = models.FloatField(default=0)
    reserved_quantity = models.FloatField(default=0)
    available_quantity = models.FloatField(default=0)
    unit_rate = models.FloatField(default=0)
    total_value = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_code} in {self.warehouse_id}: {self.quantity} {self.uom}"


class StockReservation(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    reservation_number = models.CharField(max_length=64)
    project_id = models.CharField(max_length=64)
    job_number = models.CharField(max_length=64)
    item_id = models.CharField(max_length=64)
    item_code = models.CharField(max_length=64)
    item_name = models.CharField(max_length=200)
    reserved_quantity = models.FloatField(default=0)
    reserved_date = models.CharField(max_length=50)
    reserved_by = models.CharField(max_length=150)
    status = models.CharField(max_length=30, default='Reserved')

    def __str__(self):
        return f"Reserved {self.reserved_quantity} of {self.item_code} for {self.job_number}"


class MaterialIssue(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    issue_number = models.CharField(max_length=64, unique=True)
    project_id = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    work_order_id = models.CharField(max_length=64, blank=True, default='')
    department = models.CharField(max_length=50, default='Production')
    issued_to = models.CharField(max_length=150)
    issue_date = models.CharField(max_length=50)
    warehouse_id = models.CharField(max_length=64, default='wh-main')
    items = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=30, default='Fully Issued')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.issue_number} to {self.issued_to}"


class MaterialReturn(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    return_number = models.CharField(max_length=64, unique=True)
    project_id = models.CharField(max_length=64, blank=True, default='')
    job_number = models.CharField(max_length=64, blank=True, default='')
    returned_by = models.CharField(max_length=150)
    department = models.CharField(max_length=50, default='Production')
    return_date = models.CharField(max_length=50)
    warehouse_id = models.CharField(max_length=64, default='wh-main')
    items = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=30, default='Completed')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.return_number} from {self.returned_by}"


class StockLedgerEntry(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    date = models.CharField(max_length=50)
    transaction_type = models.CharField(max_length=50) # GRN, Material Issue, Material Return, Stock Adjustment
    reference_number = models.CharField(max_length=64)
    item_id = models.CharField(max_length=64)
    item_code = models.CharField(max_length=64)
    item_name = models.CharField(max_length=200)
    warehouse_id = models.CharField(max_length=64, default='wh-main')
    inward_quantity = models.FloatField(default=0)
    outward_quantity = models.FloatField(default=0)
    closing_quantity = models.FloatField(default=0)
    unit_rate = models.FloatField(default=0)
    total_amount = models.FloatField(default=0)
    performed_by = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} [{self.transaction_type}] {self.item_code} bal: {self.closing_quantity}"


class ScrapEntry(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    scrap_number = models.CharField(max_length=64, unique=True)
    date = models.CharField(max_length=50)
    source = models.CharField(max_length=50, default='Production')
    source_reference = models.CharField(max_length=64, blank=True, default='')
    item_id = models.CharField(max_length=64, blank=True, default='')
    item_code = models.CharField(max_length=64)
    quantity = models.FloatField(default=0)
    uom = models.CharField(max_length=30, default='Kg')
    disposal_method = models.CharField(max_length=100, default='Recycling')
    estimated_value = models.FloatField(default=0)
    status = models.CharField(max_length=30, default='Identified')

    def __str__(self):
        return f"{self.scrap_number} - {self.item_code} ({self.quantity} {self.uom})"
