from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InternalAssetViewSet, CustomerMachineViewSet, ServiceRequestViewSet,
    PreventiveMaintenancePlanViewSet, BreakdownRecordViewSet, ServiceVisitViewSet,
    AMCContractViewSet
)

router = DefaultRouter()
router.register('internal-assets', InternalAssetViewSet, basename='internal-asset')
router.register('customer-machines', CustomerMachineViewSet, basename='customer-machine')
router.register('service-requests', ServiceRequestViewSet, basename='service-request')
router.register('pm-plans', PreventiveMaintenancePlanViewSet, basename='pm-plan')
router.register('breakdowns', BreakdownRecordViewSet, basename='breakdown')
router.register('service-visits', ServiceVisitViewSet, basename='service-visit')
router.register('amc-contracts', AMCContractViewSet, basename='amc-contract')

urlpatterns = [
    path('', include(router.urls)),
]
