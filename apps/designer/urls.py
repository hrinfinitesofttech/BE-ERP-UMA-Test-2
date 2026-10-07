from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DesignJobViewSet,
    BOMHeaderViewSet,
)

router = DefaultRouter()
router.register(r'jobs', DesignJobViewSet, basename='design-job')
router.register(r'boms', BOMHeaderViewSet, basename='bom')

urlpatterns = [
    path('', include(router.urls)),
]
