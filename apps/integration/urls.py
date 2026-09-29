from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ApprovalItemViewSet,
    ERPAlertItemViewSet,
    Job360OverviewViewSet,
    ExecutiveDashboardKPIViewSet,
    Customer360SummaryViewSet,
    Supplier360SummaryViewSet,
    ItemMaterial360SummaryViewSet,
    Employee360SummaryViewSet,
    GlobalActivityLogViewSet,
    ERPReportCenterItemViewSet,
    JobProfitabilityRecordViewSet,
    Job360APIView,
)

router = DefaultRouter()
router.register('approvals', ApprovalItemViewSet, basename='approval')
router.register('alerts', ERPAlertItemViewSet, basename='alert')
router.register('job-360-records', Job360OverviewViewSet, basename='job-360-record')
router.register('executive-kpis', ExecutiveDashboardKPIViewSet, basename='executive-kpi')
router.register('customer-360-summaries', Customer360SummaryViewSet, basename='customer-360-summary')
router.register('supplier-360-summaries', Supplier360SummaryViewSet, basename='supplier-360-summary')
router.register('item-360-summaries', ItemMaterial360SummaryViewSet, basename='item-360-summary')
router.register('employee-360-summaries', Employee360SummaryViewSet, basename='employee-360-summary')
router.register('activity-logs', GlobalActivityLogViewSet, basename='activity-log')
router.register('report-center-items', ERPReportCenterItemViewSet, basename='report-center-item')
router.register('job-profitability-records', JobProfitabilityRecordViewSet, basename='job-profitability-record')

urlpatterns = [
    path('job-360/<str:job_number>/', Job360APIView.as_view(), name='job-360-detail'),
    path('job-360/', Job360APIView.as_view(), name='job-360-query'),
    path('', include(router.urls)),
]
