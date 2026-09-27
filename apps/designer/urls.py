from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DesignJobViewSet,
    CustomerRequirementViewSet,
    Drawing2DViewSet,
    Design3DModelViewSet,
    BOMHeaderViewSet,
    DesignRevisionLogViewSet,
    TechnicalDocumentItemViewSet,
)

router = DefaultRouter()
router.register(r'jobs', DesignJobViewSet, basename='design-job')
router.register(r'requirements', CustomerRequirementViewSet, basename='requirement')
router.register(r'drawings-2d', Drawing2DViewSet, basename='drawing-2d')
router.register(r'models-3d', Design3DModelViewSet, basename='model-3d')
router.register(r'boms', BOMHeaderViewSet, basename='bom')
router.register(r'revisions', DesignRevisionLogViewSet, basename='revision')
router.register(r'technical-documents', TechnicalDocumentItemViewSet, basename='technical-document')

urlpatterns = [
    path('', include(router.urls)),
]
