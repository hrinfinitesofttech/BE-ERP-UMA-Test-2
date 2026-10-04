from django.contrib import admin
from .models import (
    FinancialYear,
    ChartOfAccount,
    TaxMaster,
    CostCenter,
    SalesInvoice,
    PurchaseInvoice,
    CustomerReceipt,
    SupplierPayment,
    JournalEntry,
    JobCostingSummary,
    CreditNote,
    DebitNote,
    BankAccount,
    ContraVoucher,
    ExpenseEntry,
    FixedAsset,
)

@admin.register(FinancialYear)
class FinancialYearAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'fy_code', 'start_date', 'end_date', 'status')
    search_fields = ('id', 'name', 'fy_code')
    list_filter = ('start_date', 'end_date', 'status', 'closed_date')

@admin.register(ChartOfAccount)
class ChartOfAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'account_code', 'account_name', 'account_group', 'category', 'account_type')
    search_fields = ('id', 'account_code', 'account_name')
    list_filter = ('category', 'account_type', 'tax_applicability', 'status')

@admin.register(TaxMaster)
class TaxMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'tax_code', 'tax_name', 'tax_type', 'rate_percent', 'cgst_rate')
    search_fields = ('id', 'tax_code', 'tax_name', 'hsn_sac_code')
    list_filter = ('tax_type', 'status')

@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ('id', 'cost_center_code', 'cost_center_name', 'department', 'manager_name', 'status')
    search_fields = ('id', 'cost_center_code', 'cost_center_name', 'manager_name')
    list_filter = ('status',)

@admin.register(SalesInvoice)
class SalesInvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice_number', 'invoice_date', 'due_date', 'customer_name', 'grand_total', 'payment_status')
    search_fields = ('id', 'invoice_number', 'customer_id', 'customer_name')
    list_filter = ('invoice_date', 'due_date', 'status', 'payment_status')

@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice_number', 'vendor_invoice_number', 'invoice_date', 'supplier_name', 'grand_total', 'payment_status')
    search_fields = ('id', 'invoice_number', 'vendor_invoice_number', 'supplier_id', 'supplier_name')
    list_filter = ('invoice_date', 'due_date', 'status', 'payment_status')

@admin.register(CustomerReceipt)
class CustomerReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'receipt_number', 'receipt_date', 'customer_name', 'sales_invoice_number', 'amount', 'status')
    search_fields = ('id', 'receipt_number', 'customer_id', 'customer_name')
    list_filter = ('receipt_date', 'status')

@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment_number', 'payment_date', 'supplier_name', 'purchase_invoice_number', 'amount', 'status')
    search_fields = ('id', 'payment_number', 'supplier_id', 'supplier_name')
    list_filter = ('payment_date', 'status')

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'journal_number', 'journal_date', 'voucher_type', 'total_debit', 'total_credit', 'status')
    search_fields = ('id', 'journal_number')
    list_filter = ('journal_date', 'voucher_type', 'status')

@admin.register(JobCostingSummary)
class JobCostingSummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_number', 'product_name', 'customer_name', 'sales_order_value', 'total_actual_cost', 'profit', 'margin_percent')
    search_fields = ('id', 'job_number', 'product_name', 'customer_name')

@admin.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'credit_note_number', 'credit_note_date', 'customer_name', 'original_invoice_number', 'total_amount', 'status')
    search_fields = ('id', 'credit_note_number', 'customer_name', 'original_invoice_number')
    list_filter = ('credit_note_date', 'status')

@admin.register(DebitNote)
class DebitNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'debit_note_number', 'debit_note_date', 'supplier_name', 'original_invoice_number', 'total_amount', 'status')
    search_fields = ('id', 'debit_note_number', 'supplier_name', 'original_invoice_number')
    list_filter = ('debit_note_date', 'status')

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'bank_name', 'account_name', 'account_number', 'branch', 'account_type', 'current_balance', 'status')
    search_fields = ('id', 'bank_name', 'account_number', 'account_name', 'ifsc_code')
    list_filter = ('account_type', 'status', 'is_active')

@admin.register(ContraVoucher)
class ContraVoucherAdmin(admin.ModelAdmin):
    list_display = ('id', 'contra_number', 'contra_date', 'contra_type', 'from_account_name', 'to_account_name', 'amount', 'status')
    search_fields = ('id', 'contra_number', 'from_account_name', 'to_account_name')
    list_filter = ('contra_date', 'contra_type', 'status')

@admin.register(ExpenseEntry)
class ExpenseEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'expense_number', 'expense_date', 'category', 'vendor_name', 'claimed_by', 'grand_total', 'status')
    search_fields = ('id', 'expense_number', 'vendor_name', 'claimed_by', 'category')
    list_filter = ('expense_date', 'category', 'status', 'payment_mode')

@admin.register(FixedAsset)
class FixedAssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'asset_code', 'asset_name', 'category', 'purchase_date', 'purchase_cost', 'current_book_value', 'status')
    search_fields = ('id', 'asset_code', 'asset_name', 'supplier_name', 'location')
    list_filter = ('category', 'status', 'depreciation_method')
