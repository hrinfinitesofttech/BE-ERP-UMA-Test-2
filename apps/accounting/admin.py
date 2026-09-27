from django.contrib import admin
from .models import FinancialYear, ChartOfAccount, TaxMaster, CostCenter, SalesInvoice, PurchaseInvoice, CustomerReceipt, SupplierPayment, JournalEntry, JobCostingSummary

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
    list_display = ('id', 'invoice_number', 'invoice_date', 'due_date', 'customer_id', 'customer_name')
    search_fields = ('id', 'invoice_number', 'customer_id', 'customer_name')
    list_filter = ('invoice_date', 'due_date', 'status', 'payment_status')

@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice_number', 'vendor_invoice_number', 'invoice_date', 'due_date', 'supplier_id')
    search_fields = ('id', 'invoice_number', 'vendor_invoice_number', 'supplier_id')
    list_filter = ('invoice_date', 'due_date', 'status', 'payment_status')

@admin.register(CustomerReceipt)
class CustomerReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'receipt_number', 'receipt_date', 'customer_id', 'customer_name', 'sales_invoice_number')
    search_fields = ('id', 'receipt_number', 'customer_id', 'customer_name')
    list_filter = ('receipt_date', 'status')

@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment_number', 'payment_date', 'supplier_id', 'supplier_name', 'purchase_invoice_number')
    search_fields = ('id', 'payment_number', 'supplier_id', 'supplier_name')
    list_filter = ('payment_date', 'status')

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'journal_number', 'journal_date', 'voucher_type', 'total_debit', 'total_credit')
    search_fields = ('id', 'journal_number')
    list_filter = ('journal_date', 'voucher_type', 'status')

@admin.register(JobCostingSummary)
class JobCostingSummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_number', 'product_name', 'customer_name', 'sales_order_value', 'invoiced_value')
    search_fields = ('id', 'job_number', 'product_name', 'customer_name')
