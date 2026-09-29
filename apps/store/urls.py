from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ItemCategoryViewSet,
    UOMMasterViewSet,
    ItemMasterViewSet,
    WarehouseViewSet,
    WarehouseLocationViewSet,
    GoodsReceiptNoteViewSet,
    QCInspectionViewSet,
    StockBalanceViewSet,
    StockReservationViewSet,
    MaterialIssueViewSet,
    MaterialReturnViewSet,
    StockLedgerEntryViewSet,
    ScrapEntryViewSet,
    StockTransferViewSet,
    StockAdjustmentViewSet,
)

router = DefaultRouter()
router.register(r'categories', ItemCategoryViewSet, basename='item-category')
router.register(r'uoms', UOMMasterViewSet, basename='uom')
router.register(r'items', ItemMasterViewSet, basename='item')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'locations', WarehouseLocationViewSet, basename='warehouse-location')
router.register(r'grns', GoodsReceiptNoteViewSet, basename='grn')
router.register(r'qc-inspections', QCInspectionViewSet, basename='qc-inspection')
router.register(r'stock', StockBalanceViewSet, basename='stock-balance')
router.register(r'reservations', StockReservationViewSet, basename='stock-reservation')
router.register(r'issues', MaterialIssueViewSet, basename='material-issue')
router.register(r'returns', MaterialReturnViewSet, basename='material-return')
router.register(r'transfers', StockTransferViewSet, basename='stock-transfer')
router.register(r'adjustments', StockAdjustmentViewSet, basename='stock-adjustment')
router.register(r'ledger', StockLedgerEntryViewSet, basename='stock-ledger')
router.register(r'scrap', ScrapEntryViewSet, basename='scrap')

urlpatterns = [
    path('', include(router.urls)),
]
