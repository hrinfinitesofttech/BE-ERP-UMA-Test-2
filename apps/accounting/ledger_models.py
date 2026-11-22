"""
Double-entry ledger engine (Tally-style) following the UMA Techno Fab account structure:
Balance Sheet, Depreciation Chart, Trial Balance, Stock, P&L and Ratio Analysis.
"""
from decimal import Decimal

from django.db import models

NATURE_CHOICES = [
    ('Capital', 'Capital Account'),
    ('Loans', 'Loans (Liability)'),
    ('CurrentLiabilities', 'Current Liabilities'),
    ('FixedAssets', 'Fixed Assets'),
    ('Investments', 'Investments'),
    ('CurrentAssets', 'Current Assets'),
    ('Sales', 'Sales Accounts'),
    ('Purchase', 'Purchase Accounts'),
    ('DirectIncome', 'Direct Incomes'),
    ('IndirectIncome', 'Indirect Incomes'),
    ('DirectExpense', 'Direct Expenses'),
    ('IndirectExpense', 'Indirect Expenses'),
]
BALANCE_SHEET_NATURES = {'Capital', 'Loans', 'CurrentLiabilities', 'FixedAssets', 'Investments', 'CurrentAssets'}
CREDIT_NATURES = {'Capital', 'Loans', 'CurrentLiabilities', 'Sales', 'DirectIncome', 'IndirectIncome'}


class AccountGroup(models.Model):
    name = models.CharField(max_length=128, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT, related_name='children')
    nature = models.CharField(max_length=32, choices=NATURE_CHOICES)
    sort_order = models.IntegerField(default=0)
    is_system = models.BooleanField(default=False)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Ledger(models.Model):
    name = models.CharField(max_length=255, unique=True)
    group = models.ForeignKey(AccountGroup, on_delete=models.PROTECT, related_name='ledgers')
    opening_balance = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    opening_type = models.CharField(max_length=2, default='Dr')  # Dr / Cr
    party_type = models.CharField(max_length=16, blank=True, default='')  # customer / supplier / bank
    party_id = models.CharField(max_length=64, blank=True, default='')
    status = models.CharField(max_length=32, default='Active')
    is_system = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['group__sort_order', 'sort_order', 'name']

    def __str__(self):
        return self.name

    @property
    def signed_opening(self):
        amt = self.opening_balance or Decimal('0')
        return amt if self.opening_type == 'Dr' else -amt


class LedgerEntry(models.Model):
    voucher_type = models.CharField(max_length=32)
    voucher_no = models.CharField(max_length=64, db_index=True)
    voucher_date = models.DateField(db_index=True)
    ledger = models.ForeignKey(Ledger, on_delete=models.PROTECT, related_name='entries')
    debit = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    narration = models.TextField(blank=True, default='')
    source_type = models.CharField(max_length=32, blank=True, default='')
    source_id = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['voucher_date', 'id']
        indexes = [models.Index(fields=['source_type', 'source_id'])]

    def __str__(self):
        return f"{self.voucher_no} {self.ledger_id} Dr{self.debit} Cr{self.credit}"


class Voucher(models.Model):
    """Manually keyed Payment / Receipt / Journal / Contra vouchers (multi-line Dr/Cr)."""
    voucher_no = models.CharField(max_length=64, unique=True)
    voucher_type = models.CharField(max_length=32, default='Journal')
    voucher_date = models.DateField()
    reference = models.CharField(max_length=128, blank=True, default='')
    narration = models.TextField(blank=True, default='')
    lines = models.JSONField(default=list)  # [{ledger_id, debit, credit, narration}]
    total_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    status = models.CharField(max_length=32, default='Posted')
    created_by = models.CharField(max_length=128, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-voucher_date', '-id']

    def __str__(self):
        return f"{self.voucher_no} ({self.voucher_type})"


class DepreciationAsset(models.Model):
    """Income-tax depreciation chart row (WDV method, block-wise)."""
    financial_year = models.CharField(max_length=16, default='2025-26')
    group_name = models.CharField(max_length=128)
    particulars = models.CharField(max_length=255)
    rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    opening = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    addition1 = models.DecimalField(max_digits=16, decimal_places=2, default=0)  # used >= 180 days
    addition2 = models.DecimalField(max_digits=16, decimal_places=2, default=0)  # used < 180 days
    sales = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['financial_year', 'sort_order', 'id']
        unique_together = [('financial_year', 'particulars')]

    def compute(self):
        D = lambda v: Decimal(str(v or 0))
        rate = D(self.rate) / Decimal('100')
        o, a1, a2, s = D(self.opening), D(self.addition1), D(self.addition2), D(self.sales)
        total = o + a1 + a2 - s
        base_full = max(o + a1 - s, Decimal('0'))
        dep = (rate * base_full + (rate / 2) * a2).quantize(Decimal('0.01'))
        return {'total': total, 'depreciation': dep, 'wdv': total - dep}


class StockItem(models.Model):
    name = models.CharField(max_length=255, unique=True)
    category = models.CharField(max_length=32, default='Raw Material')  # Finished Goods / Raw Material
    sub_group = models.CharField(max_length=128, blank=True, default='')
    uom = models.CharField(max_length=30, default='Nos')
    opening_qty = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    closing_qty = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    rate = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    closing_value = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    store_item_code = models.CharField(max_length=64, blank=True, default='')
    sort_order = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'sort_order', 'name']

    def save(self, *args, **kwargs):
        self.closing_value = (Decimal(str(self.closing_qty or 0)) * Decimal(str(self.rate or 0))).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)


class PaymentRequest(models.Model):
    """Bridge between Purchase/Store/other departments and Accounts for payments."""
    request_no = models.CharField(max_length=64, unique=True)
    source_type = models.CharField(max_length=32, default='Manual')  # GRN / Purchase Invoice / PO Advance / Expense / Manual
    source_ref = models.CharField(max_length=128, blank=True, default='', db_index=True)
    po_number = models.CharField(max_length=64, blank=True, default='')
    department = models.CharField(max_length=64, default='Purchase')
    supplier_id = models.CharField(max_length=64, blank=True, default='')
    supplier_name = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=16, default='Normal')
    status = models.CharField(max_length=24, default='Pending')  # Pending / Approved / Paid / Rejected
    requested_by = models.CharField(max_length=128, blank=True, default='')
    approved_by = models.CharField(max_length=128, blank=True, default='')
    payment_number = models.CharField(max_length=64, blank=True, default='')
    remarks = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f"{self.request_no} {self.supplier_name} {self.amount} [{self.status}]"
