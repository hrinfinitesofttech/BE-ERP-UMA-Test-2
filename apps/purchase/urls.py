from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SupplierViewSet,
    SupplierContactViewSet,
    PurchaseRequisitionViewSet,
    RequestForQuotationViewSet,
    SupplierQuotationViewSet,
    QuotationComparisonViewSet,
    PurchaseOrderViewSet,
    PurchaseReturnViewSet,
)

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'contacts', SupplierContactViewSet, basename='supplier-contact')
router.register(r'requisitions', PurchaseRequisitionViewSet, basename='purchase-requisition')
router.register(r'rfqs', RequestForQuotationViewSet, basename='rfq')
router.register(r'quotations', SupplierQuotationViewSet, basename='supplier-quotation')
router.register(r'comparisons', QuotationComparisonViewSet, basename='quotation-comparison')
router.register(r'orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'returns', PurchaseReturnViewSet, basename='purchase-return')

urlpatterns = [
    path('', include(router.urls)),
]
