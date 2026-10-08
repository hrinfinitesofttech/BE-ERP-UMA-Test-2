from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InternalAssetViewSet, CustomerMachineViewSet, ServiceRequestViewSet,
    PreventiveMaintenancePlanViewSet, BreakdownRecordViewSet, ServiceVisitViewSet,
    AMCContractViewSet, ServiceWorkOrderViewSet, ServicePartIssueViewSet,
    ServicePartReturnViewSet, ServiceReportViewSet, WarrantyRecordViewSet,
    ServiceContractViewSet, DowntimeRecordViewSet
)

router = DefaultRouter()
router.register('internal-assets', InternalAssetViewSet, basename='internal-asset')
router.register('customer-machines', CustomerMachineViewSet, basename='customer-machine')
router.register('installations', CustomerMachineViewSet, basename='installation')
router.register('service-requests', ServiceRequestViewSet, basename='service-request')
router.register('pm-plans', PreventiveMaintenancePlanViewSet, basename='pm-plan')
router.register('breakdowns', BreakdownRecordViewSet, basename='breakdown')
router.register('service-visits', ServiceVisitViewSet, basename='service-visit')
router.register('amc-contracts', AMCContractViewSet, basename='amc-contract')
router.register('service-work-orders', ServiceWorkOrderViewSet, basename='service-work-order')
router.register('service-part-issues', ServicePartIssueViewSet, basename='service-part-issue')
router.register('service-part-returns', ServicePartReturnViewSet, basename='service-part-return')
router.register('service-reports', ServiceReportViewSet, basename='service-report')
router.register('warranty-records', WarrantyRecordViewSet, basename='warranty-record')
router.register('service-contracts', ServiceContractViewSet, basename='service-contract')
router.register('downtime-records', DowntimeRecordViewSet, basename='downtime-record')

urlpatterns = [
    path('', include(router.urls)),
]

