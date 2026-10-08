from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DesignJobViewSet,
    CustomerRequirementViewSet,
    Drawing2DViewSet,
    Design3DModelViewSet,
    AssemblyDrawingViewSet,
    BOMHeaderViewSet,
    DesignRevisionLogViewSet,
    TechnicalDocumentItemViewSet,
    DesignTaskViewSet,
)

router = DefaultRouter()
router.register(r'jobs', DesignJobViewSet, basename='design-job')
router.register(r'boms', BOMHeaderViewSet, basename='bom')
router.register(r'requirements', CustomerRequirementViewSet, basename='designer-requirement')
router.register(r'tasks', DesignTaskViewSet, basename='designer-task')
router.register(r'design-tasks', DesignTaskViewSet, basename='designer-design-task')
router.register(r'drawings-2d', Drawing2DViewSet, basename='designer-drawing-2d')
router.register(r'models-3d', Design3DModelViewSet, basename='designer-model-3d')
router.register(r'assembly-drawings', AssemblyDrawingViewSet, basename='designer-assembly-drawing')
router.register(r'technical-documents', TechnicalDocumentItemViewSet, basename='designer-technical-doc')
router.register(r'revisions', DesignRevisionLogViewSet, basename='designer-revision')

urlpatterns = [
    path('', include(router.urls)),
]
