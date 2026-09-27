from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApprovalItemViewSet, ERPAlertItemViewSet, Job360APIView

router = DefaultRouter()
router.register('approvals', ApprovalItemViewSet, basename='approval')
router.register('alerts', ERPAlertItemViewSet, basename='alert')

urlpatterns = [
    path('job-360/<str:job_number>/', Job360APIView.as_view(), name='job-360-detail'),
    path('job-360/', Job360APIView.as_view(), name='job-360-query'),
    path('', include(router.urls)),
]
