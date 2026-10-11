"""
Django Management Command: cleanup_testing_data
Location: apps/core/management/commands/cleanup_testing_data.py

Safe Go-Live Database Cleanup & Model Inventory Tool for UmaERP.
Provides verified inventory, dry-run reporting, dependency-aware transaction removal,
and master/system data protection for client handover.
"""

import sys
from datetime import datetime
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction, connection
from django.conf import settings


# ==============================================================================
# MODEL CLASSIFICATION REGISTRY
# ==============================================================================

# 1. Strictly Protected: System, Auth, Schema, Migrations, Security
STRICTLY_PROTECTED = [
    'authentication.User',
    'auth.Group',
    'auth.Permission',
    'contenttypes.ContentType',
    'admin.LogEntry',
    'sessions.Session',
    'core.CompanySetting',
    'core.NumberingSetting',
]

# 2. Master & Reference Data: Core operational configurations (Preserved)
MASTER_REFERENCE_DATA = [
    'organization.Department',
    'organization.Role',
    'accounting.FinancialYear',
    'accounting.ChartOfAccount',
    'accounting.TaxMaster',
    'accounting.CostCenter',
    'accounting.BankAccount',
    'store.ItemCategory',
    'store.UOMMaster',
    'store.Warehouse',
    'store.WarehouseLocation',
    'production.WorkCenter',
    'production.RoutingOperation',
    'hr.Designation',
    'hr.ShiftMaster',
    'hr.Holiday',
    'hr.SalaryComponent',
    'maintenance.InternalAsset',
    'maintenance.CustomerMachine',
]

# 3. Entity Masters (Preserved by default; require explicit confirmation to reset)
ENTITY_MASTERS = [
    'crm.Customer',
    'crm.Contact',
    'crm.Exhibition',
    'purchase.Supplier',
    'purchase.SupplierContact',
    'store.ItemMaster',
]

# 4. Target Testing Business Transactions (Ordered topologically: dependent child first)
TRANSACTION_DELETION_ORDER = [
    # --- Integration, 360 & System Logs ---
    'integration.ApprovalItem',
    'integration.ERPAlertItem',
    'integration.Job360Overview',
    'integration.Customer360Summary',
    'integration.Supplier360Summary',
    'integration.ItemMaterial360Summary',
    'integration.Employee360Summary',
    'integration.JobProfitabilityRecord',
    'integration.GlobalActivityLog',
    'integration.ExecutiveDashboardKPI',
    'integration.ERPReportCenterItem',
    'core.Notification',

    # --- Accounting & Finance Transactions ---
    'accounting.ContraVoucher',
    'accounting.ExpenseEntry',
    'accounting.DebitNote',
    'accounting.CreditNote',
    'accounting.JobCostingSummary',
    'accounting.JournalEntry',
    'accounting.SupplierPayment',
    'accounting.CustomerReceipt',
    'accounting.PurchaseInvoice',
    'accounting.SalesInvoice',
    'accounting.FixedAsset',

    # --- Maintenance & Plant Service Transactions ---
    'maintenance.DowntimeRecord',
    'maintenance.WarrantyRecord',
    'maintenance.ServiceReport',
    'maintenance.ServicePartReturn',
    'maintenance.ServicePartIssue',
    'maintenance.ServiceWorkOrder',
    'maintenance.ServiceVisit',
    'maintenance.BreakdownRecord',
    'maintenance.ServiceRequest',
    'maintenance.PreventiveMaintenancePlan',
    'maintenance.AMCContract',
    'maintenance.ServiceContract',

    # --- HR & Payroll Operational Transactions ---
    'hr.EarlyCheckoutRequest',
    'hr.OvertimeRecord',
    'hr.MissedPunchRequest',
    'hr.AttendanceRegularization',
    'hr.WFHRequest',
    'hr.LeaveRequest',
    'hr.AttendanceRecord',
    'hr.PayrollRecord',
    'hr.EmployeeAdvanceLoan',
    'hr.ReimbursementExpense',
    'hr.EmployeeAppraisal',
    'hr.EmployeeExit',
    'hr.EmployeePromotion',
    'hr.EmployeeTransfer',
    'hr.EmployeeOnboarding',
    'hr.EmployeeDocument',
    'hr.SalaryStructure',

    # --- Production & Shop Floor Execution ---
    'production.ProductionCompletion',
    'production.PackingOrder',
    'production.DispatchOrder',
    'production.FinishedGoodsItem',
    'production.ProductionScrap',
    'production.ReworkOrder',
    'production.ProductionHold',
    'production.WIPRecord',
    'production.ProductionEntry',
    'production.ProductionScheduleItem',
    'production.ProductionOrder',
    'production.WorkOrder',
    'production.ProductionPlan',
    'production.ProductionMaterialRequest',
    'production.ManufacturingJob',

    # --- Store & Inventory Transactions ---
    'store.ScrapEntry',
    'store.StockAdjustment',
    'store.StockTransfer',
    'store.MaterialReturn',
    'store.MaterialIssue',
    'store.StockReservation',
    'store.StockLedgerEntry',
    'store.StockBalance',  # Stock balance reset
    'store.QCInspection',
    'store.GoodsReceiptNote',

    # --- Purchase & Procurement Transactions ---
    'purchase.QuotationComparison',
    'purchase.SupplierQuotation',
    'purchase.RequestForQuotation',
    'purchase.PurchaseReturn',
    'purchase.PurchaseOrder',
    'purchase.PurchaseRequisition',
    'purchase.MaterialRequirement',

    # --- Design & Engineering Records ---
    'designer.DesignRevisionLog',
    'designer.TechnicalDocumentItem',
    'designer.DesignTask',
    'designer.AssemblyDrawing',
    'designer.Drawing2D',
    'designer.Design3DModel',
    'designer.CustomerRequirement',
    'designer.BOMHeader',
    'designer.DesignJob',

    # --- Project Management Records ---
    'projects.CustomerChangeRequest',
    'projects.ProjectIssue',
    'projects.ProjectDelay',
    'projects.ProjectCost',
    'projects.ProjectDocument',
    'projects.DepartmentAssignment',
    'projects.ProjectTask',
    'projects.ProjectMilestone',
    'projects.ProjectPlanningStage',
    'projects.ProjectJobMaster',

    # --- CRM & Sales Transactions ---
    'crm.Activity',
    'crm.FollowUp',
    'crm.SiteVisit',
    'crm.SalesOrder',
    'crm.CustomerPO',
    'crm.Quotation',
    'crm.Opportunity',
    'crm.Enquiry',
    'crm.Lead',
]

AMBIGUOUS_TEST_KEYWORDS = [
    'test', 'demo', 'sample', 'audit', 'qa-', 'mock', 'temp', 'dummy', 'fake', 'trial', 'testing'
]


class Command(BaseCommand):
    help = 'Safe Go-Live Database Cleanup and Dry-Run Tool for UmaERP'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Execute in read-only dry-run mode (default behavior).'
        )
        parser.add_argument(
            '--execute',
            action='store_true',
            default=False,
            help='Execute permanent removal of approved testing transactions.'
        )
        parser.add_argument(
            '--confirm-go-live',
            type=str,
            default='',
            help='Explicit confirmation passphrase required when executing live cleanup.'
        )
        parser.add_argument(
            '--include-demo-masters',
            action='store_true',
            default=False,
            help='Optional: Also reset demo customer, supplier and item masters (requires explicit approval).'
        )
        parser.add_argument(
            '--database-file',
            type=str,
            default='',
            help='Optional path to specific SQLite database file (e.g. production backup replica).'
        )
        parser.add_argument(
            '--reset-numbering',
            action='store_true',
            default=False,
            help='Reset numbering counters in core.NumberingSetting back to starting value 1.'
        )

    def handle(self, *args, **options):
        db_file = options.get('database_file')
        if db_file:
            from pathlib import Path
            connection.close()
            settings.DATABASES['default']['NAME'] = Path(db_file).resolve()

        is_execute = options.get('execute')
        is_dry_run = options.get('dry_run') or not is_execute
        confirm_token = options.get('confirm_go_live')
        include_demo_masters = options.get('include_demo_masters')
        reset_numbering = options.get('reset_numbering')

        self.print_banner(is_dry_run)

        # 1. Database Identification Check
        self.verify_database_identity()

        # 2. Build Inventory of all Django models
        model_dict = self.get_all_django_models()

        # 3. Collect row counts
        row_counts = self.collect_row_counts(model_dict)

        # 4. Scan for ambiguous test master records
        ambiguous_records = self.scan_ambiguous_records()

        # 5. Output Model Inventory & Cleanup Classification Table
        self.output_classification_report(row_counts, include_demo_masters)

        # 6. Report Ambiguous Master Records
        self.output_ambiguous_report(ambiguous_records)

        # 7. Execution or Dry-run Completion
        if is_dry_run:
            self.stdout.write(self.style.WARNING(
                "\n[DRY-RUN MODE COMPLETE] No database rows were modified or deleted.\n"
                "Review the proposed cleanup scope above. To execute, explicit approval\n"
                "and verified backup confirmation are required.\n"
            ))
            return

        # LIVE EXECUTION SAFETY CHECKS
        REQUIRED_CONFIRMATION = "CONFIRM-CLEANUP-UMAERP-2026"
        if confirm_token != REQUIRED_CONFIRMATION:
            self.stdout.write(self.style.ERROR(
                f"\n[EXECUTION ABORTED] Missing or invalid confirmation passphrase!\n"
                f"To execute live cleanup, specify: --confirm-go-live {REQUIRED_CONFIRMATION}\n"
            ))
            sys.exit(1)

        self.stdout.write(self.style.NOTICE(
            "\n[CONFIRMED] Commencing atomic transaction deletion...\n"
        ))

        self.execute_cleanup(model_dict, row_counts, include_demo_masters, reset_numbering)

    def print_banner(self, is_dry_run):
        mode_str = "DRY-RUN (SIMULATION ONLY - ZERO CHANGES)" if is_dry_run else "*** LIVE EXECUTION ***"
        self.stdout.write(self.style.SUCCESS(
            "=" * 80 + "\n"
            "         UMA TECHNO FAB ERP — SAFE GO-LIVE DATABASE CLEANUP\n"
            f"         Mode: {mode_str}\n"
            f"         Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "=" * 80
        ))

    def verify_database_identity(self):
        db_conf = settings.DATABASES['default']
        db_engine = db_conf.get('ENGINE', 'unknown')
        db_name = db_conf.get('NAME', 'unknown')
        
        self.stdout.write(self.style.NOTICE("\n[1] CONFIGURED TARGET DATABASE IDENTITY:"))
        self.stdout.write(f"    - Engine: {db_engine}")
        self.stdout.write(f"    - Database Path: {db_name}")
        self.stdout.write(f"    - Host: {db_conf.get('HOST', 'localhost')}")
        self.stdout.write(f"    - Connection Vendor: {connection.vendor}")

    def get_all_django_models(self):
        models = apps.get_models()
        model_dict = {}
        for m in models:
            label = f"{m._meta.app_label}.{m.__name__}"
            model_dict[label] = m
        return model_dict

    def collect_row_counts(self, model_dict):
        counts = {}
        with connection.cursor() as cursor:
            for label, model in model_dict.items():
                table_name = model._meta.db_table
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                    cnt = cursor.fetchone()[0]
                    counts[label] = {
                        'count': cnt,
                        'table': table_name,
                        'model': model
                    }
                except Exception as e:
                    counts[label] = {
                        'count': -1,
                        'table': table_name,
                        'error': str(e),
                        'model': model
                    }
        return counts

    def scan_ambiguous_records(self):
        ambiguous = []
        try:
            from apps.crm.models import Customer
            for c in Customer.objects.all():
                text = f"{c.company_name} {c.contact_person} {c.email} {c.customer_code}".lower()
                if any(k in text for k in AMBIGUOUS_TEST_KEYWORDS):
                    ambiguous.append(('crm.Customer', c.id, c.company_name, 'Matches test keyword in company/name'))
        except Exception:
            pass

        try:
            from apps.purchase.models import Supplier
            for s in Supplier.objects.all():
                text = f"{s.name} {s.contact_person} {s.email} {s.vendor_code}".lower()
                if any(k in text for k in AMBIGUOUS_TEST_KEYWORDS):
                    ambiguous.append(('purchase.Supplier', s.id, s.name, 'Matches test keyword in supplier'))
        except Exception:
            pass

        try:
            from apps.store.models import ItemMaster
            for i in ItemMaster.objects.all():
                text = f"{i.item_code} {i.item_name} {i.item_type}".lower()
                if any(k in text for k in AMBIGUOUS_TEST_KEYWORDS):
                    ambiguous.append(('store.ItemMaster', i.id, f"{i.item_code}: {i.item_name}", 'Matches test keyword in item master'))
        except Exception:
            pass

        return ambiguous

    def output_classification_report(self, row_counts, include_demo_masters):
        self.stdout.write(self.style.NOTICE("\n[2] COMPLETE MODEL INVENTORY & PROPOSED CLEANUP SCOPE:\n"))
        self.stdout.write(
            f"{'Category':<24} | {'Model Identifier':<38} | {'Table Name':<34} | {'Count':<7} | {'Proposed Action'}"
        )
        self.stdout.write("-" * 125)

        # 1. Strictly Protected
        self.stdout.write(self.style.SUCCESS("\n--- CATEGORY A: STRICTLY PRESERVED (SYSTEM / AUTH / SECURITY / SCHEMA) ---"))
        total_protected = 0
        for label in STRICTLY_PROTECTED:
            if label in row_counts:
                info = row_counts[label]
                cnt = info['count']
                total_protected += max(0, cnt)
                self.stdout.write(
                    f"{'System Protected':<24} | {label:<38} | {info['table']:<34} | {cnt:<7} | PRESERVE (Untouched)"
                )

        # 2. Master Reference Data
        self.stdout.write(self.style.SUCCESS("\n--- CATEGORY B: OPERATIONAL MASTERS & REFERENCE DATA (PRESERVED) ---"))
        total_master_ref = 0
        for label in MASTER_REFERENCE_DATA:
            if label in row_counts:
                info = row_counts[label]
                cnt = info['count']
                total_master_ref += max(0, cnt)
                self.stdout.write(
                    f"{'Master Reference':<24} | {label:<38} | {info['table']:<34} | {cnt:<7} | PRESERVE (Untouched)"
                )

        # 3. Entity Masters
        action_entity = "RESET TO ZERO (Approved)" if include_demo_masters else "PRESERVE (Unless approved)"
        self.stdout.write(self.style.WARNING(
            "\n--- CATEGORY C: ENTITY MASTERS (PRESERVED BY DEFAULT; REQUIRES EXPLICIT APPROVAL) ---"
        ))
        total_entity = 0
        for label in ENTITY_MASTERS:
            if label in row_counts:
                info = row_counts[label]
                cnt = info['count']
                total_entity += max(0, cnt)
                self.stdout.write(
                    f"{'Entity Master':<24} | {label:<38} | {info['table']:<34} | {cnt:<7} | {action_entity}"
                )

        # 4. Target Testing Business Transactions
        self.stdout.write(self.style.ERROR(
            "\n--- CATEGORY D: TARGET TESTING BUSINESS TRANSACTIONS (CLEANUP CANDIDATES) ---"
        ))
        total_trans_rows = 0
        for label in TRANSACTION_DELETION_ORDER:
            if label in row_counts:
                info = row_counts[label]
                cnt = info['count']
                total_trans_rows += max(0, cnt)
                action_str = f"DELETE {cnt} rows" if cnt > 0 else "ZERO (Clean)"
                self.stdout.write(
                    f"{'Test Transaction':<24} | {label:<38} | {info['table']:<34} | {cnt:<7} | {action_str}"
                )

        self.stdout.write("=" * 125)
        self.stdout.write(self.style.NOTICE(
            f"SUMMARY TOTALS:\n"
            f"  - Strictly Protected Records:     {total_protected}\n"
            f"  - Operational Master Records:     {total_master_ref}\n"
            f"  - Entity Masters (Preserved):     {total_entity}\n"
            f"  - Testing Transactions to Remove: {total_trans_rows}\n"
        ))

    def output_ambiguous_report(self, ambiguous_records):
        self.stdout.write(self.style.NOTICE("\n[3] AMBIGUOUS / DEMO RECORD DETECTION (FOR CLIENT REVIEW):"))
        if not ambiguous_records:
            self.stdout.write("    No ambiguous test records detected in preserved master tables.")
            return

        self.stdout.write(self.style.WARNING(
            f"    Detected {len(ambiguous_records)} potential test/seed records inside master entities:\n"
        ))
        self.stdout.write(
            f"    {'Model':<22} | {'ID / Code':<20} | {'Name / Description':<36} | {'Reason'}"
        )
        self.stdout.write("    " + "-" * 115)
        for model_name, rec_id, desc, reason in ambiguous_records:
            self.stdout.write(
                f"    {model_name:<22} | {str(rec_id):<20} | {str(desc)[:35]:<36} | {reason}"
            )
        self.stdout.write(self.style.NOTICE(
            "\n    NOTE: These master records are PRESERVED by default. If the client requests\n"
            "    starting with blank customer/supplier lists, pass --include-demo-masters after confirmation.\n"
        ))

    def execute_cleanup(self, model_dict, before_counts, include_demo_masters, reset_numbering):
        deleted_summary = {}

        try:
            with transaction.atomic():
                self.stdout.write(self.style.NOTICE("\nExecuting transaction deletions in dependency order..."))

                # 1. Delete Business Transactions
                for label in TRANSACTION_DELETION_ORDER:
                    if label in model_dict:
                        model = model_dict[label]
                        cnt_before = before_counts.get(label, {}).get('count', 0)
                        if cnt_before > 0:
                            num_deleted, _ = model.objects.all().delete()
                            deleted_summary[label] = num_deleted
                            self.stdout.write(f"  [OK] Cleaned {label}: {num_deleted} records deleted.")
                        else:
                            deleted_summary[label] = 0

                # 2. Reset Stock Balances
                # Stock balances must be zeroed or emptied when all transaction ledgers are removed
                if 'store.StockBalance' in model_dict:
                    sb_model = model_dict['store.StockBalance']
                    sb_cnt = sb_model.objects.count()
                    if sb_cnt > 0:
                        sb_model.objects.all().delete()
                        self.stdout.write(f"  [OK] Reset store.StockBalance: {sb_cnt} balance records cleared.")

                # 3. Optional Entity Masters Deletion
                if include_demo_masters:
                    self.stdout.write(self.style.WARNING("\nExecuting approved entity masters reset..."))
                    for label in reversed(ENTITY_MASTERS):
                        if label in model_dict:
                            model = model_dict[label]
                            cnt_before = before_counts.get(label, {}).get('count', 0)
                            if cnt_before > 0:
                                num_deleted, _ = model.objects.all().delete()
                                deleted_summary[label] = num_deleted
                                self.stdout.write(f"  [OK] Cleaned {label}: {num_deleted} records deleted.")

                # 4. Optional Reset Document Numbering Counters
                if reset_numbering:
                    try:
                        from apps.core.models import NumberingSetting
                        for ns in NumberingSetting.objects.all():
                            ns.current_number = 0
                            ns.save()
                        self.stdout.write(self.style.SUCCESS("  [OK] Reset NumberingSetting counters to 0."))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  [WARN] Numbering reset: {e}"))

                self.stdout.write(self.style.SUCCESS(
                    "\n[TRANSACTION COMMITTED] All targeted testing transactions removed successfully!\n"
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"\n[EXECUTION FAILED - AUTOMATIC ROLLBACK]: An error occurred: {e}\n"
            ))
            raise e

        # Post-execution verification
        after_counts = self.collect_row_counts(model_dict)
        self.stdout.write(self.style.NOTICE("\n[POST-CLEANUP VERIFICATION] Checking transaction counts:"))
        zero_failures = []
        for label in TRANSACTION_DELETION_ORDER:
            cnt = after_counts.get(label, {}).get('count', 0)
            if cnt > 0:
                zero_failures.append((label, cnt))

        if not zero_failures:
            self.stdout.write(self.style.SUCCESS("  [PASS] All transaction models verified at 0 rows."))
        else:
            self.stdout.write(self.style.ERROR(f"  [FAIL] Non-zero models remaining: {zero_failures}"))
