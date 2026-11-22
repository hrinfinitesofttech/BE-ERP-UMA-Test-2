from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .ledger_views import (
    AccountGroupViewSet, LedgerViewSet, VoucherViewSet, DepreciationAssetViewSet, StockItemViewSet,
    PaymentRequestViewSet, ReportView, SetupView, DayBookView,
)
from .views import (
    FinancialYearViewSet, ChartOfAccountViewSet, TaxMasterViewSet,
    CostCenterViewSet, SalesInvoiceViewSet, PurchaseInvoiceViewSet,
    CustomerReceiptViewSet, SupplierPaymentViewSet, JournalEntryViewSet,
    JobCostingSummaryViewSet, CreditNoteViewSet, DebitNoteViewSet,
    BankAccountViewSet, ContraVoucherViewSet, ExpenseEntryViewSet,
    FixedAssetViewSet, AccountingDashboardMetricsView, EWayBillViewSet
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
router.register('eway-bills', EWayBillViewSet, basename='eway-bill')
router.register('ewaybills', EWayBillViewSet, basename='ewaybill')

router.register('account-groups', AccountGroupViewSet, basename='account-group')
router.register('ledgers', LedgerViewSet, basename='ledger')
router.register('vouchers', VoucherViewSet, basename='voucher')
router.register('depreciation-assets', DepreciationAssetViewSet, basename='depreciation-asset')
router.register('stock-items', StockItemViewSet, basename='stock-item')
router.register('payment-requests', PaymentRequestViewSet, basename='payment-request')

urlpatterns = [
    path('reports/<str:kind>/', ReportView.as_view(), name='accounting-report'),
    path('setup/<str:action_name>/', SetupView.as_view(), name='accounting-setup'),
    path('day-book/', DayBookView.as_view(), name='accounting-day-book'),
    path('dashboard-metrics/', AccountingDashboardMetricsView.as_view(), name='accounting-dashboard-metrics'),
    path('', include(router.urls)),
]


