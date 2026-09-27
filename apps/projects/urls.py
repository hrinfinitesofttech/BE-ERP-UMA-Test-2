from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectJobMasterViewSet,
    ProjectPlanningStageViewSet,
    ProjectMilestoneViewSet,
    ProjectTaskViewSet,
    DepartmentAssignmentViewSet,
    ProjectIssueViewSet,
    ProjectDelayViewSet,
    CustomerChangeRequestViewSet,
    ProjectCostViewSet,
)

router = DefaultRouter()
router.register(r'jobs', ProjectJobMasterViewSet, basename='project-job')
router.register(r'planning-stages', ProjectPlanningStageViewSet, basename='planning-stage')
router.register(r'milestones', ProjectMilestoneViewSet, basename='milestone')
router.register(r'tasks', ProjectTaskViewSet, basename='task')
router.register(r'assignments', DepartmentAssignmentViewSet, basename='assignment')
router.register(r'issues', ProjectIssueViewSet, basename='issue')
router.register(r'delays', ProjectDelayViewSet, basename='delay')
router.register(r'change-requests', CustomerChangeRequestViewSet, basename='change-request')
router.register(r'costs', ProjectCostViewSet, basename='cost')

urlpatterns = [
    path('', include(router.urls)),
]
