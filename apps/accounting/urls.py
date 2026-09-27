from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FinancialYearViewSet, ChartOfAccountViewSet, TaxMasterViewSet,
    CostCenterViewSet, SalesInvoiceViewSet, PurchaseInvoiceViewSet,
    CustomerReceiptViewSet, SupplierPaymentViewSet, JournalEntryViewSet,
    JobCostingSummaryViewSet
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

urlpatterns = [
    path('', include(router.urls)),
]
