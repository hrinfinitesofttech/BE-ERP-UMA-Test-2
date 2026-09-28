from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DesignationViewSet, EmployeeDocumentViewSet, ShiftMasterViewSet,
    AttendanceRecordViewSet, LeaveRequestViewSet, WFHRequestViewSet,
    MissedPunchRequestViewSet, AttendanceRegularizationViewSet,
    OvertimeRecordViewSet, EarlyCheckoutRequestViewSet,
    SalaryComponentViewSet, SalaryStructureViewSet, PayrollRecordViewSet,
    EmployeeAdvanceLoanViewSet, ReimbursementExpenseViewSet,
    EmployeeOnboardingViewSet, EmployeeTransferViewSet,
    EmployeePromotionViewSet, EmployeeExitViewSet
)

router = DefaultRouter()
router.register('designations', DesignationViewSet, basename='designation')
router.register('employee-documents', EmployeeDocumentViewSet, basename='employee-document')
router.register('shifts', ShiftMasterViewSet, basename='shift')
router.register('attendance-records', AttendanceRecordViewSet, basename='attendance-record')
router.register('leave-requests', LeaveRequestViewSet, basename='leave-request')
router.register('wfh-requests', WFHRequestViewSet, basename='wfh-request')
router.register('missed-punches', MissedPunchRequestViewSet, basename='missed-punch')
router.register('regularizations', AttendanceRegularizationViewSet, basename='regularization')
router.register('overtime-records', OvertimeRecordViewSet, basename='overtime-record')
router.register('early-checkouts', EarlyCheckoutRequestViewSet, basename='early-checkout')
router.register('salary-components', SalaryComponentViewSet, basename='salary-component')
router.register('salary-structures', SalaryStructureViewSet, basename='salary-structure')
router.register('payroll-records', PayrollRecordViewSet, basename='payroll-record')
router.register('advance-loans', EmployeeAdvanceLoanViewSet, basename='advance-loan')
router.register('reimbursements', ReimbursementExpenseViewSet, basename='reimbursement')
router.register('employee-onboardings', EmployeeOnboardingViewSet, basename='employee-onboarding')
router.register('employee-transfers', EmployeeTransferViewSet, basename='employee-transfer')
router.register('employee-promotions', EmployeePromotionViewSet, basename='employee-promotion')
router.register('employee-exits', EmployeeExitViewSet, basename='employee-exit')

urlpatterns = [
    path('', include(router.urls)),
]

