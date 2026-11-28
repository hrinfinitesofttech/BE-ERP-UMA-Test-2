from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NestingHandoverViewSet, NestingJobViewSet, NestingTaskViewSet, SheetUsageViewSet

router = DefaultRouter()
router.register('jobs', NestingJobViewSet, basename='nesting-job')
router.register('tasks', NestingTaskViewSet, basename='nesting-task')
router.register('handovers', NestingHandoverViewSet, basename='nesting-handover')
router.register('sheet-usage', SheetUsageViewSet, basename='nesting-sheet-usage')

urlpatterns = [
    path('', include(router.urls)),
]
