from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LeadViewSet,
    CustomerViewSet,
    ContactViewSet,
    EnquiryViewSet,
    OpportunityViewSet,
    FollowUpViewSet,
    SiteVisitViewSet,
    ExhibitionViewSet,
    QuotationViewSet,
    CustomerPOViewSet,
    SalesOrderViewSet,
    ActivityViewSet,
)

router = DefaultRouter()
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'enquiries', EnquiryViewSet, basename='enquiry')
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')
router.register(r'followups', FollowUpViewSet, basename='followup')
router.register(r'visits', SiteVisitViewSet, basename='visit')
router.register(r'exhibitions', ExhibitionViewSet, basename='exhibition')
router.register(r'quotations', QuotationViewSet, basename='quotation')
router.register(r'customer-pos', CustomerPOViewSet, basename='customer-po')
router.register(r'sales-orders', SalesOrderViewSet, basename='sales-order')
router.register(r'activities', ActivityViewSet, basename='activity')

urlpatterns = [
    path('', include(router.urls)),
]
