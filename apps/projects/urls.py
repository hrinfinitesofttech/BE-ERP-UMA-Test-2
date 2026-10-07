from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectJobMasterViewSet,
    ProjectPlanningStageViewSet,
    ProjectTaskViewSet,
    DepartmentAssignmentViewSet,
    ProjectCostViewSet,
    ProjectDocumentViewSet,
)

router = DefaultRouter()
router.register(r'jobs', ProjectJobMasterViewSet, basename='project-job')
router.register(r'planning-stages', ProjectPlanningStageViewSet, basename='planning-stage')
router.register(r'tasks', ProjectTaskViewSet, basename='task')
router.register(r'assignments', DepartmentAssignmentViewSet, basename='assignment')
router.register(r'costs', ProjectCostViewSet, basename='cost')
router.register(r'documents', ProjectDocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
]
