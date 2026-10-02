from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ManufacturingJobViewSet, ProductionPlanViewSet, WorkCenterViewSet,
    RoutingOperationViewSet, WorkOrderViewSet, ProductionOrderViewSet,
    ProductionScheduleItemViewSet, ProductionEntryViewSet, WIPRecordViewSet,
    ProductionHoldViewSet, ReworkOrderViewSet, ProductionScrapViewSet,
    FinishedGoodsItemViewSet, ProductionMaterialRequestViewSet
)

router = DefaultRouter()
router.register('material-requests', ProductionMaterialRequestViewSet, basename='material-request')
router.register('material-issues', ProductionMaterialRequestViewSet, basename='material-issue')
router.register('manufacturing-jobs', ManufacturingJobViewSet, basename='manufacturing-job')
router.register('production-plans', ProductionPlanViewSet, basename='production-plan')
router.register('work-centers', WorkCenterViewSet, basename='work-center')
router.register('routing-operations', RoutingOperationViewSet, basename='routing-operation')
router.register('work-orders', WorkOrderViewSet, basename='work-order')
router.register('production-orders', ProductionOrderViewSet, basename='production-order')
router.register('production-schedules', ProductionScheduleItemViewSet, basename='production-schedule')
router.register('production-entries', ProductionEntryViewSet, basename='production-entry')
router.register('wip-records', WIPRecordViewSet, basename='wip-record')
router.register('production-holds', ProductionHoldViewSet, basename='production-hold')
router.register('rework-orders', ReworkOrderViewSet, basename='rework-order')
router.register('production-scraps', ProductionScrapViewSet, basename='production-scrap')
router.register('finished-goods', FinishedGoodsItemViewSet, basename='finished-good')

urlpatterns = [
    path('', include(router.urls)),
]
