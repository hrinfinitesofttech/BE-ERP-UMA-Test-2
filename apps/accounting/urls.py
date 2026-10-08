from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FinancialYearViewSet, ChartOfAccountViewSet, TaxMasterViewSet,
    CostCenterViewSet, SalesInvoiceViewSet, PurchaseInvoiceViewSet,
    CustomerReceiptViewSet, SupplierPaymentViewSet, JournalEntryViewSet,
    JobCostingSummaryViewSet, CreditNoteViewSet, DebitNoteViewSet,
    BankAccountViewSet, ContraVoucherViewSet, ExpenseEntryViewSet,
    FixedAssetViewSet, AccountingDashboardMetricsView
)

router = DefaultRouter()
router.register('financial-years', FinancialYearViewSet, basename='financial-year')
router.register('chart-of-accounts', ChartOfAccountViewSet, basename='chart-of-account')
router.register('taxes', TaxMasterViewSet, basename='tax')
router.register('cost-centers', CostCenterViewSet, basename='cost-center')
router.register('sales-invoices', SalesInvoiceViewSet, basename='sales-invoice')
router.register('purchase-invoices', PurchaseInvoiceViewSet, basename='purchase-invoice')
router.register('customer-receipts', CustomerReceiptViewSet, basename='customer-receipt')
router.register('supplier-payments', SupplierPaymentViewSet, basename='supplier-payment')
router.register('journal-entries', JournalEntryViewSet, basename='journal-entry')
router.register('job-costings', JobCostingSummaryViewSet, basename='job-costing')
router.register('credit-notes', CreditNoteViewSet, basename='credit-note')
router.register('debit-notes', DebitNoteViewSet, basename='debit-note')
router.register('bank-accounts', BankAccountViewSet, basename='bank-account')
router.register('contra-vouchers', ContraVoucherViewSet, basename='contra-voucher')
router.register('contra-entries', ContraVoucherViewSet, basename='contra-entry')
router.register('expenses', ExpenseEntryViewSet, basename='expense')
router.register('expense-entries', ExpenseEntryViewSet, basename='expense-entry')
router.register('fixed-assets', FixedAssetViewSet, basename='fixed-asset')

urlpatterns = [
    path('dashboard-metrics/', AccountingDashboardMetricsView.as_view(), name='accounting-dashboard-metrics'),
    path('', include(router.urls)),
]


