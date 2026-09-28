"""
URL configuration for erp_backend project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from apps.organization.views import DepartmentViewSet, RoleViewSet
from apps.authentication.views import EmployeeViewSet, LoginView, CurrentUserView, ChangePasswordView
from apps.core.views import (
    CompanySettingView,
    NumberingSettingViewSet,
    AuditLogViewSet,
    NotificationViewSet,
)
from apps.crm.views import (
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
from apps.projects.views import (
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
from apps.designer.views import (
    DesignJobViewSet,
    CustomerRequirementViewSet,
    Drawing2DViewSet,
    Design3DModelViewSet,
    BOMHeaderViewSet,
    DesignRevisionLogViewSet,
    TechnicalDocumentItemViewSet,
)
from apps.purchase.views import (
    SupplierViewSet,
    SupplierContactViewSet,
    PurchaseRequisitionViewSet,
    RequestForQuotationViewSet,
    SupplierQuotationViewSet,
    QuotationComparisonViewSet,
    PurchaseOrderViewSet,
    PurchaseReturnViewSet,
)
from apps.store.views import (
    ItemCategoryViewSet,
    UOMMasterViewSet,
    ItemMasterViewSet,
    WarehouseViewSet,
    WarehouseLocationViewSet,
    GoodsReceiptNoteViewSet,
    QCInspectionViewSet,
    StockBalanceViewSet,
    StockReservationViewSet,
    MaterialIssueViewSet,
    MaterialReturnViewSet,
    StockLedgerEntryViewSet,
    ScrapEntryViewSet,
)
from apps.production.views import (
    ManufacturingJobViewSet,
    ProductionPlanViewSet,
    WorkCenterViewSet,
    RoutingOperationViewSet,
    WorkOrderViewSet,
    ProductionOrderViewSet,
    ProductionScheduleItemViewSet,
    ProductionEntryViewSet,
    WIPRecordViewSet,
    ProductionHoldViewSet,
    ReworkOrderViewSet,
    ProductionScrapViewSet,
    FinishedGoodsItemViewSet,
)
from apps.maintenance.views import (
    InternalAssetViewSet,
    CustomerMachineViewSet,
    ServiceRequestViewSet,
    PreventiveMaintenancePlanViewSet,
    BreakdownRecordViewSet,
    ServiceVisitViewSet,
    AMCContractViewSet,
)
from apps.hr.views import (
    DesignationViewSet,
    EmployeeDocumentViewSet,
    ShiftMasterViewSet,
    AttendanceRecordViewSet,
    LeaveRequestViewSet,
    WFHRequestViewSet,
    MissedPunchRequestViewSet,
    AttendanceRegularizationViewSet,
    OvertimeRecordViewSet,
    EarlyCheckoutRequestViewSet,
    SalaryComponentViewSet,
    SalaryStructureViewSet,
    PayrollRecordViewSet,
    EmployeeAdvanceLoanViewSet,
    ReimbursementExpenseViewSet,
)
from apps.accounting.views import (
    FinancialYearViewSet,
    ChartOfAccountViewSet,
    TaxMasterViewSet,
    CostCenterViewSet,
    SalesInvoiceViewSet,
    PurchaseInvoiceViewSet,
    CustomerReceiptViewSet,
    SupplierPaymentViewSet,
    JournalEntryViewSet,
    JobCostingSummaryViewSet,
    CreditNoteViewSet,
    DebitNoteViewSet,
    BankAccountViewSet,
    ContraVoucherViewSet,
    ExpenseEntryViewSet,
)
from apps.integration.views import (
    ApprovalItemViewSet,
    ERPAlertItemViewSet,
    Job360APIView,
)

# Root API router exposing convenient top-level endpoints
api_router = DefaultRouter()
# Core & Org
api_router.register(r'departments', DepartmentViewSet, basename='department')
api_router.register(r'roles', RoleViewSet, basename='role')
api_router.register(r'employees', EmployeeViewSet, basename='employee')
api_router.register(r'numbering', NumberingSettingViewSet, basename='numbering')
api_router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
api_router.register(r'notifications', NotificationViewSet, basename='notification')

# CRM Endpoints
api_router.register(r'leads', LeadViewSet, basename='lead')
api_router.register(r'customers', CustomerViewSet, basename='customer')
api_router.register(r'contacts', ContactViewSet, basename='contact')
api_router.register(r'enquiries', EnquiryViewSet, basename='enquiry')
api_router.register(r'opportunities', OpportunityViewSet, basename='opportunity')
api_router.register(r'followups', FollowUpViewSet, basename='followup')
api_router.register(r'visits', SiteVisitViewSet, basename='visit')
api_router.register(r'exhibitions', ExhibitionViewSet, basename='exhibition')
api_router.register(r'quotations', QuotationViewSet, basename='quotation')
api_router.register(r'customer-pos', CustomerPOViewSet, basename='customer-po')
api_router.register(r'sales-orders', SalesOrderViewSet, basename='sales-order')
api_router.register(r'activities', ActivityViewSet, basename='activity')

# Project Management
api_router.register(r'projects', ProjectJobMasterViewSet, basename='project')
api_router.register(r'planning-stages', ProjectPlanningStageViewSet, basename='planning-stage')
api_router.register(r'project-milestones', ProjectMilestoneViewSet, basename='project-milestone')
api_router.register(r'project-tasks', ProjectTaskViewSet, basename='project-task')
api_router.register(r'project-issues', ProjectIssueViewSet, basename='project-issue')
api_router.register(r'project-delays', ProjectDelayViewSet, basename='project-delay')
api_router.register(r'change-requests', CustomerChangeRequestViewSet, basename='change-request')
api_router.register(r'department-assignments', DepartmentAssignmentViewSet, basename='department-assignment')
api_router.register(r'project-costs', ProjectCostViewSet, basename='project-cost')

# Design & Engineering
api_router.register(r'design-jobs', DesignJobViewSet, basename='design-job')
api_router.register(r'design-requirements', CustomerRequirementViewSet, basename='design-requirement')
api_router.register(r'customer-requirements', CustomerRequirementViewSet, basename='customer-requirement')
api_router.register(r'drawings-2d', Drawing2DViewSet, basename='drawing-2d')
api_router.register(r'models-3d', Design3DModelViewSet, basename='model-3d')
api_router.register(r'boms', BOMHeaderViewSet, basename='bom')
api_router.register(r'design-revisions', DesignRevisionLogViewSet, basename='design-revision')
api_router.register(r'technical-documents', TechnicalDocumentItemViewSet, basename='technical-document')

# Purchase & Procurement
api_router.register(r'suppliers', SupplierViewSet, basename='supplier')
api_router.register(r'supplier-contacts', SupplierContactViewSet, basename='supplier-contact')
api_router.register(r'purchase-requisitions', PurchaseRequisitionViewSet, basename='purchase-requisition')
api_router.register(r'rfqs', RequestForQuotationViewSet, basename='rfq')
api_router.register(r'supplier-quotations', SupplierQuotationViewSet, basename='supplier-quotation')
api_router.register(r'quotation-comparisons', QuotationComparisonViewSet, basename='quotation-comparison')
api_router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
api_router.register(r'purchase-returns', PurchaseReturnViewSet, basename='purchase-return')

# Store & Inventory
api_router.register(r'item-categories', ItemCategoryViewSet, basename='item-category')
api_router.register(r'uoms', UOMMasterViewSet, basename='uom')
api_router.register(r'items', ItemMasterViewSet, basename='item')
api_router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
api_router.register(r'warehouse-locations', WarehouseLocationViewSet, basename='warehouse-location')
api_router.register(r'grns', GoodsReceiptNoteViewSet, basename='grn')
api_router.register(r'qc-inspections', QCInspectionViewSet, basename='qc-inspection')
api_router.register(r'stock', StockBalanceViewSet, basename='stock-balance')
api_router.register(r'stock-reservations', StockReservationViewSet, basename='stock-reservation')
api_router.register(r'material-issues', MaterialIssueViewSet, basename='material-issue')
api_router.register(r'material-returns', MaterialReturnViewSet, basename='material-return')
api_router.register(r'stock-ledger', StockLedgerEntryViewSet, basename='stock-ledger')
api_router.register(r'scrap', ScrapEntryViewSet, basename='scrap')

# Production & Shopfloor
api_router.register(r'manufacturing-jobs', ManufacturingJobViewSet, basename='manufacturing-job')
api_router.register(r'production-plans', ProductionPlanViewSet, basename='production-plan')
api_router.register(r'work-centers', WorkCenterViewSet, basename='work-center')
api_router.register(r'routing-operations', RoutingOperationViewSet, basename='routing-operation')
api_router.register(r'work-orders', WorkOrderViewSet, basename='work-order')
api_router.register(r'production-orders', ProductionOrderViewSet, basename='production-order')
api_router.register(r'production-schedules', ProductionScheduleItemViewSet, basename='production-schedule')
api_router.register(r'production-entries', ProductionEntryViewSet, basename='production-entry')
api_router.register(r'wip-records', WIPRecordViewSet, basename='wip-record')
api_router.register(r'production-holds', ProductionHoldViewSet, basename='production-hold')
api_router.register(r'rework-orders', ReworkOrderViewSet, basename='rework-order')
api_router.register(r'production-scraps', ProductionScrapViewSet, basename='production-scrap')
api_router.register(r'finished-goods', FinishedGoodsItemViewSet, basename='finished-good')

# Maintenance & Plant Service
api_router.register(r'internal-assets', InternalAssetViewSet, basename='internal-asset')
api_router.register(r'customer-machines', CustomerMachineViewSet, basename='customer-machine')
api_router.register(r'service-requests', ServiceRequestViewSet, basename='service-request')
api_router.register(r'pm-plans', PreventiveMaintenancePlanViewSet, basename='pm-plan')
api_router.register(r'breakdowns', BreakdownRecordViewSet, basename='breakdown')
api_router.register(r'service-visits', ServiceVisitViewSet, basename='service-visit')
api_router.register(r'amc-contracts', AMCContractViewSet, basename='amc-contract')

# HR & Payroll
api_router.register(r'designations', DesignationViewSet, basename='designation')
api_router.register(r'employee-documents', EmployeeDocumentViewSet, basename='employee-document')
api_router.register(r'shifts', ShiftMasterViewSet, basename='shift')
api_router.register(r'attendance-records', AttendanceRecordViewSet, basename='attendance-record')
api_router.register(r'leave-requests', LeaveRequestViewSet, basename='leave-request')
api_router.register(r'wfh-requests', WFHRequestViewSet, basename='wfh-request')
api_router.register(r'missed-punches', MissedPunchRequestViewSet, basename='missed-punch')
api_router.register(r'missed-punch-requests', MissedPunchRequestViewSet, basename='missed-punch-request')
api_router.register(r'regularizations', AttendanceRegularizationViewSet, basename='regularization')
api_router.register(r'attendance-regularizations', AttendanceRegularizationViewSet, basename='attendance-regularization')
api_router.register(r'overtime-records', OvertimeRecordViewSet, basename='overtime-record')
api_router.register(r'early-checkouts', EarlyCheckoutRequestViewSet, basename='early-checkout')
api_router.register(r'early-checkout-requests', EarlyCheckoutRequestViewSet, basename='early-checkout-request')
api_router.register(r'salary-components', SalaryComponentViewSet, basename='salary-component')
api_router.register(r'salary-structures', SalaryStructureViewSet, basename='salary-structure')
api_router.register(r'payroll-records', PayrollRecordViewSet, basename='payroll-record')
api_router.register(r'advance-loans', EmployeeAdvanceLoanViewSet, basename='advance-loan')
api_router.register(r'employee-advances', EmployeeAdvanceLoanViewSet, basename='employee-advance')
api_router.register(r'reimbursements', ReimbursementExpenseViewSet, basename='reimbursement')

# Accounting & Finance
api_router.register(r'financial-years', FinancialYearViewSet, basename='financial-year')
api_router.register(r'chart-of-accounts', ChartOfAccountViewSet, basename='chart-of-account')
api_router.register(r'taxes', TaxMasterViewSet, basename='tax')
api_router.register(r'cost-centers', CostCenterViewSet, basename='cost-center')
api_router.register(r'sales-invoices', SalesInvoiceViewSet, basename='sales-invoice')
api_router.register(r'purchase-invoices', PurchaseInvoiceViewSet, basename='purchase-invoice')
api_router.register(r'customer-receipts', CustomerReceiptViewSet, basename='customer-receipt')
api_router.register(r'supplier-payments', SupplierPaymentViewSet, basename='supplier-payment')
api_router.register(r'journal-entries', JournalEntryViewSet, basename='journal-entry')
api_router.register(r'job-costings', JobCostingSummaryViewSet, basename='job-costing')
api_router.register(r'credit-notes', CreditNoteViewSet, basename='credit-note')
api_router.register(r'debit-notes', DebitNoteViewSet, basename='debit-note')
api_router.register(r'bank-accounts', BankAccountViewSet, basename='bank-account')
api_router.register(r'contra-entries', ContraVoucherViewSet, basename='contra-entry')
api_router.register(r'contra-vouchers', ContraVoucherViewSet, basename='contra-voucher')
api_router.register(r'expenses', ExpenseEntryViewSet, basename='expense')
api_router.register(r'expense-entries', ExpenseEntryViewSet, basename='expense-entry')

# Integration & Approvals
api_router.register(r'approvals', ApprovalItemViewSet, basename='approval')
api_router.register(r'alerts', ERPAlertItemViewSet, basename='alert')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Direct top-level convenience endpoints matching frontend conventions
    path('api/auth/login/', LoginView.as_view(), name='api-login'),
    path('api/auth/me/', CurrentUserView.as_view(), name='api-me'),
    path('api/auth/change-password/', ChangePasswordView.as_view(), name='api-change-password'),
    path('api/company/', CompanySettingView.as_view(), name='api-company'),
    path('api/job-360/<str:job_number>/', Job360APIView.as_view(), name='api-job-360-detail'),
    path('api/job-360/', Job360APIView.as_view(), name='api-job-360-query'),
    path('api/', include(api_router.urls)),

    # Modular Namespaced URLs
    path('api/auth/', include('apps.authentication.urls')),
    path('api/org/', include('apps.organization.urls')),
    path('api/core/', include('apps.core.urls')),
    path('api/crm/', include('apps.crm.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/designer/', include('apps.designer.urls')),
    path('api/purchase/', include('apps.purchase.urls')),
    path('api/store/', include('apps.store.urls')),
    path('api/production/', include('apps.production.urls')),
    path('api/maintenance/', include('apps.maintenance.urls')),
    path('api/hr/', include('apps.hr.urls')),
    path('api/accounting/', include('apps.accounting.urls')),
    path('api/integration/', include('apps.integration.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
