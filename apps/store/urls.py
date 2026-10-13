from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ItemCategoryViewSet,
    UOMMasterViewSet,
    ItemMasterViewSet,
    GoodsReceiptNoteViewSet,
    MaterialIssueViewSet,
    MaterialReturnViewSet,
    ScrapEntryViewSet,
)

router = DefaultRouter()
router.register(r'categories', ItemCategoryViewSet, basename='item-category')
router.register(r'uoms', UOMMasterViewSet, basename='uom')
router.register(r'items', ItemMasterViewSet, basename='item')
router.register(r'grns', GoodsReceiptNoteViewSet, basename='grn')
router.register(r'issues', MaterialIssueViewSet, basename='material-issue')
router.register(r'returns', MaterialReturnViewSet, basename='material-return')
router.register(r'scrap', ScrapEntryViewSet, basename='scrap')

urlpatterns = [
    path('', include(router.urls)),
]
