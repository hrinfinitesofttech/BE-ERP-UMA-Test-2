from django.core.management.base import BaseCommand
from datetime import date, timedelta
from apps.accounting.models import (
    FinancialYear, ChartOfAccount, TaxMaster, CostCenter,
    SalesInvoice, PurchaseInvoice, CustomerReceipt, SupplierPayment,
    JournalEntry, JobCostingSummary
)
from apps.integration.models import ApprovalItem, ERPAlertItem


class Command(BaseCommand):
    help = 'Seeds Phase 6 data (Accounting, GST, Job Costing, 360 Traceability & Central Approvals)'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Phase 6: Accounting, Finance, 360 Job Traceability & Approvals...')

        today = date.today()

        # -------------------------------------------------------------
        # 1. ACCOUNTING & FINANCIAL SETUP
        # -------------------------------------------------------------
        self.stdout.write('  Seeding Financial Years & Taxes...')
        FinancialYear.objects.update_or_create(
            id='FY-2026-27',
            defaults={
                'name': 'FY 2026-2027',
                'fy_code': '2026-2027',
                'start_date': date(2026, 4, 1),
                'end_date': date(2027, 3, 31),
                'status': 'Active'
            }
        )
        FinancialYear.objects.update_or_create(
            id='FY-2025-26',
            defaults={
                'name': 'FY 2025-2026',
                'fy_code': '2025-2026',
                'start_date': date(2025, 4, 1),
                'end_date': date(2026, 3, 31),
                'status': 'Closed',
                'closed_date': date(2026, 4, 15),
                'closed_by': 'Audit Team'
            }
        )

        taxes_data = [
            {'id': 'TAX-GST-18', 'tax_code': 'GST-18', 'tax_name': 'GST 18% (CGST 9% + SGST 9%)', 'tax_type': 'GST Combination', 'rate_percent': 18.0, 'cgst_rate': 9.0, 'sgst_rate': 9.0, 'igst_rate': 18.0, 'hsn_sac_code': '8419', 'status': 'Active'},
            {'id': 'TAX-GST-12', 'tax_code': 'GST-12', 'tax_name': 'GST 12% (CGST 6% + SGST 6%)', 'tax_type': 'GST Combination', 'rate_percent': 12.0, 'cgst_rate': 6.0, 'sgst_rate': 6.0, 'igst_rate': 12.0, 'hsn_sac_code': '7308', 'status': 'Active'},
            {'id': 'TAX-GST-28', 'tax_code': 'GST-28', 'tax_name': 'GST 28% (CGST 14% + SGST 14%)', 'tax_type': 'GST Combination', 'rate_percent': 28.0, 'cgst_rate': 14.0, 'sgst_rate': 14.0, 'igst_rate': 28.0, 'hsn_sac_code': '8413', 'status': 'Active'},
        ]
        for t in taxes_data:
            TaxMaster.objects.update_or_create(id=t['id'], defaults=t)

        cost_centers = [
            {'id': 'CC-01', 'cost_center_code': 'CC-PRD-FAB', 'cost_center_name': 'Heavy Fabrication & Welding Bay', 'department': 'Production', 'manager_name': 'Vikram Rathore', 'status': 'Active'},
            {'id': 'CC-02', 'cost_center_code': 'CC-ENG-DES', 'cost_center_name': 'Design Engineering & CAD', 'department': 'Engineering', 'manager_name': 'Rajesh Patel', 'status': 'Active'},
            {'id': 'CC-03', 'cost_center_code': 'CC-SRV-SITE', 'cost_center_name': 'Field Site Commissioning & Service', 'department': 'Maintenance', 'manager_name': 'Sanjay Mehta', 'status': 'Active'},
        ]
        for cc in cost_centers:
            CostCenter.objects.update_or_create(id=cc['id'], defaults=cc)

        self.stdout.write('  Seeding Chart of Accounts...')
        coas = [
            {'id': 'COA-1001', 'account_code': '1001', 'account_name': 'Cash on Hand - Factory Safe', 'account_group': 'Cash & Bank', 'category': 'Assets', 'account_type': 'Cash', 'opening_balance': 150000.0, 'current_balance': 185000.0, 'status': 'Active'},
            {'id': 'COA-1002', 'account_code': '1002', 'account_name': 'HDFC Bank Corporate Current A/c - 50200012345', 'account_group': 'Cash & Bank', 'category': 'Assets', 'account_type': 'Bank', 'opening_balance': 24500000.0, 'current_balance': 38200000.0, 'status': 'Active'},
            {'id': 'COA-1003', 'account_code': '1003', 'account_name': 'State Bank of India (Hazira Branch) - 308912445', 'account_group': 'Cash & Bank', 'category': 'Assets', 'account_type': 'Bank', 'opening_balance': 12000000.0, 'current_balance': 14800000.0, 'status': 'Active'},
            {'id': 'COA-1101', 'account_code': '1101', 'account_name': 'Trade Debtors / Accounts Receivable', 'account_group': 'Current Assets', 'category': 'Assets', 'account_type': 'Accounts Receivable', 'opening_balance': 18500000.0, 'current_balance': 22400000.0, 'status': 'Active'},
            {'id': 'COA-1201', 'account_code': '1201', 'account_name': 'Raw Material & Steel Stock Inventory', 'account_group': 'Inventory', 'category': 'Assets', 'account_type': 'Inventory', 'opening_balance': 34000000.0, 'current_balance': 42500000.0, 'status': 'Active'},
            {'id': 'COA-1202', 'account_code': '1202', 'account_name': 'Work in Progress (WIP) Fabrication Stock', 'account_group': 'Inventory', 'category': 'Assets', 'account_type': 'Inventory', 'opening_balance': 18000000.0, 'current_balance': 26000000.0, 'status': 'Active'},
            {'id': 'COA-2001', 'account_code': '2001', 'account_name': 'Sundry Creditors / Trade Payables', 'account_group': 'Current Liabilities', 'category': 'Liabilities', 'account_type': 'Accounts Payable', 'opening_balance': 14200000.0, 'current_balance': 19500000.0, 'status': 'Active'},
            {'id': 'COA-2002', 'account_code': '2002', 'account_name': 'Output GST Payable (CGST + SGST + IGST)', 'account_group': 'Duties & Taxes', 'category': 'Liabilities', 'account_type': 'GST Payable', 'opening_balance': 2800000.0, 'current_balance': 3450000.0, 'status': 'Active'},
            {'id': 'COA-4001', 'account_code': '4001', 'account_name': 'Sales Revenue - Heavy Fabrication & Pressure Vessels', 'account_group': 'Operating Income', 'category': 'Income', 'account_type': 'Sales Income', 'opening_balance': 0.0, 'current_balance': 125000000.0, 'status': 'Active'},
            {'id': 'COA-5001', 'account_code': '5001', 'account_name': 'Direct Raw Material Consumption Cost', 'account_group': 'Direct Expenses', 'category': 'Expenses', 'account_type': 'Direct Expense', 'opening_balance': 0.0, 'current_balance': 68500000.0, 'status': 'Active'},
            {'id': 'COA-5002', 'account_code': '5002', 'account_name': 'Direct Shopfloor Labour & Welder Wages', 'account_group': 'Direct Expenses', 'category': 'Expenses', 'account_type': 'Direct Expense', 'opening_balance': 0.0, 'current_balance': 14200000.0, 'status': 'Active'},
        ]
        for c in coas:
            ChartOfAccount.objects.update_or_create(id=c['id'], defaults=c)

        # -------------------------------------------------------------
        # 2. INVOICES, RECEIPTS & PAYMENTS
        # -------------------------------------------------------------
        self.stdout.write('  Seeding Sales Invoices & Customer Receipts...')
        sales_inv = {
            'id': 'INV-2026-001',
            'invoice_number': 'INV-2026-001',
            'invoice_date': today - timedelta(days=12),
            'due_date': today + timedelta(days=18),
            'customer_id': 'CUST-001',
            'customer_name': 'Reliance Industries Limited (Jamnagar)',
            'customer_gstin': '24AAACR1234F1Z8',
            'place_of_supply': 'Gujarat (24)',
            'sales_order_id': 'SO-2026-001',
            'sales_order_number': 'SO-2026-001',
            'customer_po_number': 'RIL/PO/450098231',
            'project_id': 'PRJ-2026-001',
            'job_number': 'JOB-2026-001',
            'payment_terms': '30 Days Net from Delivery',
            'items': [
                {
                    'id': 'ITEM-01',
                    'description': 'High Pressure Hydrogen De-Sulphurization Reactor (50 KL) - Milestone 2 Mobilization & Material Inwarding (40%)',
                    'hsnSac': '8419',
                    'quantity': 1.0,
                    'uom': 'Unit',
                    'rate': 3800000.0,
                    'taxableValue': 3800000.0,
                    'cgstAmount': 342000.0,
                    'sgstAmount': 342000.0,
                    'igstAmount': 0.0,
                    'totalAmount': 4484000.0
                }
            ],
            'taxable_amount': 3800000.0,
            'cgst_amount': 342000.0,
            'sgst_amount': 342000.0,
            'igst_amount': 0.0,
            'round_off': 0.0,
            'grand_total': 4484000.0,
            'paid_amount': 4484000.0,
            'outstanding_amount': 0.0,
            'status': 'Paid',
            'payment_status': 'Paid',
            'created_by': 'Pooja Shah'
        }
        SalesInvoice.objects.update_or_create(id=sales_inv['id'], defaults=sales_inv)

        CustomerReceipt.objects.update_or_create(
            id='REC-2026-001',
            defaults={
                'receipt_number': 'REC-2026-001',
                'receipt_date': today - timedelta(days=5),
                'customer_id': 'CUST-001',
                'customer_name': 'Reliance Industries Limited (Jamnagar)',
                'sales_invoice_number': 'INV-2026-001',
                'payment_mode': 'RTGS',
                'bank_name': 'HDFC Bank Corporate A/c',
                'amount': 4484000.0,
                'reference_number': 'HDFCR52026092000189',
                'status': 'Received',
                'remarks': 'Milestone 2 payment received in full against INV-2026-001.',
                'created_by': 'Pooja Shah'
            }
        )

        self.stdout.write('  Seeding Purchase Invoices & Supplier Payments...')
        purch_inv = {
            'id': 'PINV-2026-001',
            'invoice_number': 'PINV-2026-001',
            'vendor_invoice_number': 'SAIL-BOK-INV-45129',
            'invoice_date': today - timedelta(days=20),
            'due_date': today + timedelta(days=10),
            'supplier_id': 'SUP-001',
            'supplier_name': 'Steel Authority of India Ltd (SAIL)',
            'supplier_gstin': '20AAACS0123M1Z2',
            'po_number': 'PO-2026-0042',
            'grn_number': 'GRN-2026-0018',
            'project_id': 'PRJ-2026-001',
            'job_number': 'JOB-2026-001',
            'payment_terms': '30 Days from MRN/GRN',
            'items': [
                {
                    'id': 'PITEM-01',
                    'itemCode': 'RM-PLT-01',
                    'itemName': 'SA 387 Gr 11 Cl 2 45mm Pressure Vessel Alloy Steel Plate',
                    'hsnSac': '7225',
                    'quantity': 14.5,
                    'uom': 'MT',
                    'rate': 95000.0,
                    'taxableAmount': 1377500.0,
                    'cgstAmount': 0.0,
                    'sgstAmount': 0.0,
                    'igstAmount': 247950.0,
                    'totalAmount': 1625450.0
                }
            ],
            'taxable_amount': 1377500.0,
            'cgst_amount': 0.0,
            'sgst_amount': 0.0,
            'igst_amount': 247950.0,
            'grand_total': 1625450.0,
            'paid_amount': 1625450.0,
            'outstanding_amount': 0.0,
            'status': 'Paid',
            'payment_status': 'Paid',
            'created_by': 'Pooja Shah'
        }
        PurchaseInvoice.objects.update_or_create(id=purch_inv['id'], defaults=purch_inv)

        SupplierPayment.objects.update_or_create(
            id='PAY-SUP-2026-001',
            defaults={
                'payment_number': 'PAY-SUP-2026-001',
                'payment_date': today - timedelta(days=3),
                'supplier_id': 'SUP-001',
                'supplier_name': 'Steel Authority of India Ltd (SAIL)',
                'purchase_invoice_number': 'PINV-2026-001',
                'payment_mode': 'RTGS',
                'bank_name': 'State Bank of India',
                'amount': 1625450.0,
                'reference_number': 'SBIR52026092400918',
                'status': 'Paid',
                'remarks': 'Full settlement against invoice SAIL-BOK-INV-45129 for JOB-2026-001 plates.',
                'created_by': 'Pooja Shah'
            }
        )

        JournalEntry.objects.update_or_create(
            id='JV-2026-001',
            defaults={
                'journal_number': 'JV-2026-001',
                'journal_date': today - timedelta(days=1),
                'voucher_type': 'Depreciation',
                'narration': 'Monthly depreciation booked on CNC Plasma & Plate Rolling Machines for September 2026.',
                'lines': [
                    {'accountCode': '5003', 'accountName': 'Depreciation Expense - Machinery', 'debitAmount': 185000.0, 'creditAmount': 0.0},
                    {'accountCode': '1301', 'accountName': 'Accumulated Depreciation - Plant & Machinery', 'debitAmount': 0.0, 'creditAmount': 185000.0},
                ],
                'total_debit': 185000.0,
                'total_credit': 185000.0,
                'status': 'Posted',
                'created_by': 'Finance Team'
            }
        )

        self.stdout.write('  Seeding Job Costing Summaries...')
        job_costings = [
            {
                'id': 'JC-JOB-2026-001',
                'job_number': 'JOB-2026-001',
                'product_name': 'High Pressure Hydrogen De-Sulphurization Reactor (50 KL)',
                'customer_name': 'Reliance Industries Limited (Jamnagar)',
                'sales_order_value': 9500000.0,
                'invoiced_value': 4484000.0,
                'received_value': 4484000.0,
                'material_cost': 3850000.0,
                'labour_cost': 1200000.0,
                'machine_cost': 950000.0,
                'subcontract_cost': 420000.0,
                'overhead_cost': 420000.0,
                'total_actual_cost': 6840000.0,
                'profit': 2660000.0,
                'margin_percent': 28.0
            },
            {
                'id': 'JC-JOB-2026-002',
                'job_number': 'JOB-2026-002',
                'product_name': 'Cryogenic Liquid Nitrogen Storage Tank 100 KL (Double Walled)',
                'customer_name': 'Larsen & Toubro Heavy Engineering (Hazira)',
                'sales_order_value': 14500000.0,
                'invoiced_value': 0.0,
                'received_value': 0.0,
                'material_cost': 6200000.0,
                'labour_cost': 1800000.0,
                'machine_cost': 1400000.0,
                'subcontract_cost': 650000.0,
                'overhead_cost': 550000.0,
                'total_actual_cost': 10600000.0,
                'profit': 3900000.0,
                'margin_percent': 26.9
            }
        ]
        for jc in job_costings:
            JobCostingSummary.objects.update_or_create(id=jc['id'], defaults=jc)

        # -------------------------------------------------------------
        # 3. CENTRAL APPROVAL CENTER & ALERT CENTER SEEDING
        # -------------------------------------------------------------
        self.stdout.write('  Seeding Approvals Queue & ERP Alerts...')
        approvals = [
            {
                'id': 'APPR-2026-001',
                'category': 'Purchase Order',
                'title': 'High Value Purchase Order Approval: SA 387 Gr 11 Plates',
                'record_number': 'PO-2026-0042',
                'requester_name': 'Pooja Shah',
                'requester_role': 'Procurement Manager',
                'request_date': today - timedelta(days=22),
                'amount': 1625450.0,
                'related_job_number': 'JOB-2026-001',
                'remarks': 'Approved by Managing Director under CAPEX/Raw Material threshold.',
                'urgency': 'High',
                'status': 'Approved'
            },
            {
                'id': 'APPR-2026-002',
                'category': 'BOM',
                'title': 'Release of Multi-Level Engineering BOM-2026-001 (Rev 2)',
                'record_number': 'BOM-2026-001',
                'requester_name': 'Rajesh Patel',
                'requester_role': 'Design Head',
                'request_date': today - timedelta(days=20),
                'amount': 3850000.0,
                'related_job_number': 'JOB-2026-001',
                'remarks': 'Approved for shop floor procurement and plate nesting.',
                'urgency': 'Critical',
                'status': 'Approved'
            },
            {
                'id': 'APPR-2026-003',
                'category': 'Leave',
                'title': 'Casual Leave Request for Rajesh Patel',
                'record_number': 'LV-2026-101',
                'requester_name': 'Rajesh Patel',
                'requester_role': 'Senior Design Engineer',
                'request_date': today - timedelta(days=2),
                'amount': None,
                'related_job_number': 'JOB-2026-001',
                'remarks': 'Approved for 2 days leave.',
                'urgency': 'Normal',
                'status': 'Approved'
            },
            {
                'id': 'APPR-2026-004',
                'category': 'Production Hold',
                'title': 'Production Hold Request: Ultrasonic Testing Clearance on Seam 3',
                'record_number': 'HLD-2026-001',
                'requester_name': 'Kavita Iyer',
                'requester_role': 'QA Lead',
                'request_date': today - timedelta(days=4),
                'amount': None,
                'related_job_number': 'JOB-2026-001',
                'remarks': 'Review completed, hold resumed after radiograph verification.',
                'urgency': 'Critical',
                'status': 'Approved'
            }
        ]
        for a in approvals:
            ApprovalItem.objects.update_or_create(id=a['id'], defaults=a)

        alerts = [
            {
                'id': 'ALT-2026-001',
                'module': 'Maintenance',
                'severity': 'Critical',
                'title': 'Hydraulic Bending Machine Breakdown Reported',
                'description': 'Davi 4-Roll bending machine experienced seal failure on drop-end cylinder. Repaired and tested.',
                'target_url': '/maintenance/breakdowns',
                'action_required': 'Verify hydraulic oil filtration and maintenance checklist',
                'is_read': True
            },
            {
                'id': 'ALT-2026-002',
                'module': 'Production',
                'severity': 'Warning',
                'title': 'Job JOB-2026-001 Longitudinal SAW Seam at 65% Progress',
                'description': 'Shopfloor Bay 2 operator completed root pass and 4 filler runs. NDT Level II inspection due.',
                'target_url': '/production/jobs',
                'action_required': 'Assign QA inspector for visual & UT check',
                'is_read': False
            },
            {
                'id': 'ALT-2026-003',
                'module': 'Accounts',
                'severity': 'Info',
                'title': 'Customer Payment of Rs 44,84,000 Received from Reliance',
                'description': 'RTGS payment cleared in HDFC Corporate account against invoice INV-2026-001.',
                'target_url': '/accounting/receipts',
                'action_required': 'Reconciliation verified in bank ledger',
                'is_read': False
            },
            {
                'id': 'ALT-2026-004',
                'module': 'Store',
                'severity': 'Info',
                'title': 'Low Stock Alert: Bohler SAW Flux UV 420 TT Below Minimum Reorder Level',
                'description': 'Current stock is 250 Kg; minimum buffer is 500 Kg.',
                'target_url': '/store/stock',
                'action_required': 'Generate Purchase Requisition',
                'is_read': False
            }
        ]
        for alt in alerts:
            ERPAlertItem.objects.update_or_create(id=alt['id'], defaults=alt)

        self.stdout.write(self.style.SUCCESS('[OK] Phase 6 seed completed successfully!'))
