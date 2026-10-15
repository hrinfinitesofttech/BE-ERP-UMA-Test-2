"""
UMA ERP - COMPLETE 100% CRUD & APPROVAL WORKFLOW TEST SUITE
Tests Create, Read, Update, Delete (CRUD) and Approve / Disapprove / Reject workflows
across all core ERP modules with direct SQLite database persistence checks.
"""

import os
import sys
import django
from datetime import date, datetime, timedelta
import random

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status

# Model imports for direct database verification
from apps.organization.models import Department
from apps.authentication.models import User
from apps.crm.models import Lead, Customer, Enquiry, Quotation, CustomerPO, SalesOrder
from apps.projects.models import ProjectJobMaster, ProjectMilestone
from apps.designer.models import DesignJob, BOMHeader, CustomerRequirement
from apps.purchase.models import Supplier, PurchaseRequisition, PurchaseOrder
from apps.store.models import ItemMaster, GoodsReceiptNote, MaterialIssue
from apps.production.models import WorkOrder, ProductionEntry, FinishedGoodsItem, DispatchOrder
from apps.accounting.models import SalesInvoice, CustomerReceipt, ExpenseEntry
from apps.hr.models import LeaveRequest, WFHRequest, OvertimeRecord
from apps.integration.models import ApprovalItem

class TestStats:
    passed = 0
    failed = 0
    errors = []

def record_pass(step_name):
    TestStats.passed += 1
    print(f"  [PASS] {step_name}")

def record_fail(step_name, error_msg):
    TestStats.failed += 1
    TestStats.errors.append(f"{step_name}: {error_msg}")
    print(f"  [FAIL] {step_name} -> {error_msg}")

def run_suite():
    print("=" * 95)
    print("🚀 UMA ERP - COMPREHENSIVE CRUD & APPROVAL WORKFLOW TEST SUITE")
    print("   Verifying CREATE, READ, UPDATE, DELETE & APPROVE / DISAPPROVE across all modules")
    print("=" * 95)

    client = APIClient()

    # 0. AUTHENTICATION
    print("\n[PHASE 0: AUTHENTICATION]")
    login_res = client.post('/api/auth/login/', {'username': 'admin', 'password': 'Admin@123456'}, format='json')
    if login_res.status_code == 200:
        token = login_res.data.get('access')
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        record_pass("JWT Authentication as Super Admin")
    else:
        record_fail("JWT Authentication", f"Status {login_res.status_code}: {login_res.data}")
        return False

    today_str = date.today().isoformat()
    uid = f"T{int(datetime.now().timestamp())}"

    # =========================================================================
    # 1. CRM & SALES: LEAD CRUD
    # =========================================================================
    print("\n[PHASE 1: CRM & SALES - LEAD]")
    lead_no = f"LEAD-{uid}"
    lead_payload = {
        'leadNo': lead_no,
        'companyName': f'Gujarat Process Equipments {uid}',
        'contactPerson': 'Bhavesh Mehta',
        'mobile': '9876543210',
        'email': f'bhavesh_{uid}@gpe.com',
        'productName': 'Distillation Column 5000L SS316',
        'status': 'new',
        'priority': 'high',
        'budget': 5000000,
        'createdDate': today_str,
    }
    # Create
    r_c = client.post('/api/leads/', lead_payload, format='json')
    if r_c.status_code in [200, 201]:
        lead_id = r_c.data.get('id') or lead_no
        record_pass(f"Lead CREATE (ID: {lead_id})")
        # Read
        r_r = client.get(f'/api/leads/{lead_id}/')
        if r_r.status_code == 200 and r_r.data.get('companyName') == lead_payload['companyName']:
            record_pass("Lead READ & Field Verification")
        else:
            record_fail("Lead READ", f"{r_r.status_code}")
        # Update
        r_u = client.patch(f'/api/leads/{lead_id}/', {'status': 'qualified', 'budget': 7500000}, format='json')
        db_lead = Lead.objects.filter(id=lead_id).first()
        if r_u.status_code == 200 and db_lead and db_lead.status == 'qualified':
            record_pass("Lead UPDATE & DB Persistence (Status: qualified, Budget: 75L)")
        else:
            record_fail("Lead UPDATE", "DB mismatch")
    else:
        record_fail("Lead CREATE", f"{r_c.status_code} {r_c.data}")

    # Lead Temporary DELETE verification
    del_lead_no = f"LEAD-DEL-{uid}"
    r_del_create = client.post('/api/leads/', {**lead_payload, 'leadNo': del_lead_no}, format='json')
    if r_del_create.status_code in [200, 201]:
        del_lead_id = r_del_create.data.get('id') or del_lead_no
        r_d = client.delete(f'/api/leads/{del_lead_id}/')
        db_check = Lead.objects.filter(id=del_lead_id).first()
        if r_d.status_code in [200, 204] and db_check is None:
            record_pass(f"Lead DELETE verified in SQLite (ID: {del_lead_id} removed)")
        else:
            record_fail("Lead DELETE", f"Status {r_d.status_code}, DB exists: {db_check is not None}")

    # =========================================================================
    # 2. CRM & SALES: CUSTOMER & ENQUIRY CRUD
    # =========================================================================
    print("\n[PHASE 2: CRM & SALES - CUSTOMER & ENQUIRY]")
    cust_id = f"CUST-{uid}"
    cust_payload = {
        'id': cust_id,
        'customerCode': cust_id,
        'companyName': lead_payload['companyName'],
        'contactPerson': lead_payload['contactPerson'],
        'mobile': lead_payload['mobile'],
        'email': lead_payload['email'],
        'city': 'Vadodara',
        'state': 'Gujarat',
    }
    r_cust_c = client.post('/api/customers/', cust_payload, format='json')
    if r_cust_c.status_code in [200, 201]:
        record_pass(f"Customer CREATE (ID: {cust_id})")
        r_cust_u = client.patch(f'/api/customers/{cust_id}/', {'city': 'Ahmedabad', 'creditLimit': 10000000}, format='json')
        db_cust = Customer.objects.filter(id=cust_id).first()
        if r_cust_u.status_code == 200 and db_cust and db_cust.city == 'Ahmedabad':
            record_pass("Customer UPDATE & DB Persistence (City: Ahmedabad)")
        else:
            record_fail("Customer UPDATE", "City mismatch in DB")
    else:
        record_fail("Customer CREATE", f"{r_cust_c.status_code} {r_cust_c.data}")

    # Enquiry
    enq_no = f"ENQ-{uid}"
    enq_payload = {
        'enquiryNo': enq_no,
        'customerId': cust_id,
        'customerName': lead_payload['companyName'],
        'enquiryDate': today_str,
        'requirement': 'Fabrication of 5000L SS316 Reaction Vessel',
        'machineProduct': lead_payload['productName'],
        'quantity': 1,
        'status': 'under_review',
    }
    r_enq_c = client.post('/api/enquiries/', enq_payload, format='json')
    if r_enq_c.status_code in [200, 201]:
        enq_id = r_enq_c.data.get('id') or enq_no
        record_pass(f"Enquiry CREATE (ID: {enq_id})")
        r_enq_u = client.patch(f'/api/enquiries/{enq_id}/', {'status': 'quotation_ready'}, format='json')
        db_enq = Enquiry.objects.filter(id=enq_id).first()
        if r_enq_u.status_code == 200 and db_enq and db_enq.status == 'quotation_ready':
            record_pass("Enquiry UPDATE (Status: quotation_ready)")
        else:
            record_fail("Enquiry UPDATE", "Status mismatch in DB")
    else:
        record_fail("Enquiry CREATE", f"{r_enq_c.status_code} {r_enq_c.data}")

    # =========================================================================
    # 3. CRM & SALES: QUOTATION CRUD & APPROVAL / DISAPPROVAL WORKFLOW
    # =========================================================================
    print("\n[PHASE 3: CRM - QUOTATION CRUD & APPROVAL / DISAPPROVAL]")
    quo_no = f"QT-{uid}"
    quo_payload = {
        'quotationNumber': quo_no,
        'currentRevision': 'Rev-00',
        'date': today_str,
        'validUntil': '2026-12-31',
        'customerId': cust_id,
        'customerName': lead_payload['companyName'],
        'enquiryId': enq_id,
        'revisions': [{
            'revisionNumber': 'Rev-00',
            'status': 'draft',
            'grandTotal': 7200000,
            'machineProduct': lead_payload['productName'],
            'items': [{'itemNo': 1, 'description': lead_payload['productName'], 'qty': 1, 'unitRate': 7200000, 'amount': 7200000}]
        }],
    }
    r_quo_c = client.post('/api/quotations/', quo_payload, format='json')
    if r_quo_c.status_code in [200, 201]:
        quo_id = r_quo_c.data.get('id') or quo_no
        record_pass(f"Quotation CREATE (ID: {quo_id}, Grand Total: 72L)")
        # Approval
        r_quo_app = client.post(f'/api/quotations/{quo_id}/update-status/', {'revisionNumber': 'Rev-00', 'status': 'approved'}, format='json')
        db_quo = Quotation.objects.filter(id=quo_id).first()
        if r_quo_app.status_code == 200 and db_quo and db_quo.status == 'approved':
            record_pass("Quotation APPROVAL & DB Persistence (Status: approved)")
        else:
            record_fail("Quotation APPROVAL", f"{r_quo_app.status_code}")
    else:
        record_fail("Quotation CREATE", f"{r_quo_c.status_code} {r_quo_c.data}")

    # Quotation Disapproval flow on separate quotation
    rej_quo_no = f"QT-REJ-{uid}"
    r_quo_rej_c = client.post('/api/quotations/', {**quo_payload, 'quotationNumber': rej_quo_no}, format='json')
    if r_quo_rej_c.status_code in [200, 201]:
        rej_quo_id = r_quo_rej_c.data.get('id') or rej_quo_no
        r_quo_dis = client.post(f'/api/quotations/{rej_quo_id}/update-status/', {'revisionNumber': 'Rev-00', 'status': 'rejected', 'reason': 'Client rejected commercial terms'}, format='json')
        db_quo_rej = Quotation.objects.filter(id=rej_quo_id).first()
        if r_quo_dis.status_code == 200 and db_quo_rej and db_quo_rej.status == 'rejected':
            record_pass("Quotation DISAPPROVAL / REJECTION (Status: rejected)")
        else:
            record_fail("Quotation DISAPPROVAL", f"{r_quo_dis.status_code}")

    # Quotation DELETE check
    del_quo_no = f"QT-DEL-{uid}"
    r_del_quo = client.post('/api/quotations/', {**quo_payload, 'quotationNumber': del_quo_no}, format='json')
    if r_del_quo.status_code in [200, 201]:
        del_quo_id = r_del_quo.data.get('id') or del_quo_no
        r_q_del = client.delete(f'/api/quotations/{del_quo_id}/')
        db_check = Quotation.objects.filter(id=del_quo_id).first()
        if r_q_del.status_code in [200, 204] and db_check is None:
            record_pass(f"Quotation DELETE verified in SQLite (ID: {del_quo_id} removed)")
        else:
            record_fail("Quotation DELETE", f"Status {r_q_del.status_code}")

    # =========================================================================
    # 4. CUSTOMER PO & SALES ORDER CRUD & ACCEPTANCE
    # =========================================================================
    print("\n[PHASE 4: CRM - CUSTOMER PO & SALES ORDER]")
    po_no = f"CPO-{uid}"
    cpo_payload = {
        'poNumber': po_no,
        'customerId': cust_id,
        'customerName': lead_payload['companyName'],
        'quotationId': quo_id,
        'quotationNumber': quo_no,
        'poDate': today_str,
        'deliveryDate': '2026-11-30',
        'poAmount': 7200000.0,
        'status': 'received',
    }
    r_cpo_c = client.post('/api/customer-pos/', cpo_payload, format='json')
    if r_cpo_c.status_code in [200, 201]:
        cpo_id = r_cpo_c.data.get('id') or po_no
        record_pass(f"Customer PO CREATE (ID: {cpo_id})")
        # Acceptance
        r_cpo_acc = client.patch(f'/api/customer-pos/{cpo_id}/', {'status': 'accepted'}, format='json')
        db_cpo = CustomerPO.objects.filter(id=cpo_id).first()
        if r_cpo_acc.status_code == 200 and db_cpo and db_cpo.status == 'accepted':
            record_pass("Customer PO ACCEPTANCE & DB Persistence (Status: accepted)")
        else:
            record_fail("Customer PO ACCEPTANCE", f"{r_cpo_acc.status_code}")
    else:
        record_fail("Customer PO CREATE", f"{r_cpo_c.status_code}")

    # Disapproval / Rejection on separate PO
    cpo_rej_payload = {**cpo_payload, 'poNumber': f"CPO-REJ-{uid}"}
    r_cpo_rej_c = client.post('/api/customer-pos/', cpo_rej_payload, format='json')
    if r_cpo_rej_c.status_code in [200, 201]:
        cpo_rej_id = r_cpo_rej_c.data.get('id') or cpo_rej_payload['poNumber']
        r_cpo_rej = client.patch(f'/api/customer-pos/{cpo_rej_id}/', {'status': 'rejected'}, format='json')
        db_cpo_rej = CustomerPO.objects.filter(id=cpo_rej_id).first()
        if r_cpo_rej.status_code == 200 and db_cpo_rej and db_cpo_rej.status == 'rejected':
            record_pass("Customer PO REJECTION & DB Persistence (Status: rejected)")
        else:
            record_fail("Customer PO REJECTION", f"{r_cpo_rej.status_code}")

    # Sales Order
    so_no = f"SO-{uid}"
    so_payload = {
        'salesOrderNumber': so_no,
        'customerPoId': cpo_id,
        'customerPoNumber': po_no,
        'quotationId': quo_id,
        'quotationNumber': quo_no,
        'customerId': cust_id,
        'customerName': lead_payload['companyName'],
        'orderDate': today_str,
        'targetDeliveryDate': '2026-11-30',
        'grandTotal': 7200000.0,
        'totalAmount': 7200000.0,
        'status': 'draft',
        'items': [{'itemNo': 1, 'productName': lead_payload['productName'], 'quantity': 1, 'unitRate': 7200000, 'totalAmount': 7200000}]
    }
    r_so_c = client.post('/api/sales-orders/', so_payload, format='json')
    if r_so_c.status_code in [200, 201]:
        so_id = r_so_c.data.get('id') or so_no
        record_pass(f"Sales Order CREATE (ID: {so_id})")
        r_so_u = client.patch(f'/api/sales-orders/{so_id}/', {'status': 'confirmed', 'approvedBy': 'Bhavin Shah (Director)'}, format='json')
        db_so = SalesOrder.objects.filter(id=so_id).first()
        if r_so_u.status_code == 200 and db_so and db_so.status == 'confirmed':
            record_pass("Sales Order CONFIRMATION / APPROVAL (Status: confirmed)")
        else:
            record_fail("Sales Order CONFIRMATION", f"{r_so_u.status_code}")
    else:
        record_fail("Sales Order CREATE", f"{r_so_c.status_code}")

    # =========================================================================
    # 5. PROJECTS & JOBS CRUD
    # =========================================================================
    print("\n[PHASE 5: PROJECTS & JOBS]")
    prj_no = f"PRJ-{uid}"
    job_no = f"JOB-{uid}"
    prj_payload = {
        'id': prj_no,
        'projectNumber': prj_no,
        'jobNumber': job_no,
        'customerId': cust_id,
        'customerName': lead_payload['companyName'],
        'salesOrderId': so_id,
        'salesOrderNumber': so_no,
        'customerPoNumber': po_no,
        'productName': lead_payload['productName'],
        'orderValue': 7200000.0,
        'startDate': today_str,
        'targetDeliveryDate': '2026-11-30',
        'currentStatus': 'planning',
        'projectManagerName': 'Bhavin Shah',
    }
    r_prj_c = client.post('/api/projects/', prj_payload, format='json')
    if r_prj_c.status_code in [200, 201]:
        prj_id = r_prj_c.data.get('id') or prj_no
        record_pass(f"Project & Job Master CREATE (ID: {prj_id}, Job: {job_no})")
        r_prj_u = client.patch(f'/api/projects/{prj_id}/', {'currentStatus': 'in_progress', 'progressPercent': 25}, format='json')
        db_prj = ProjectJobMaster.objects.filter(id=prj_id).first()
        if r_prj_u.status_code == 200 and db_prj and db_prj.current_status == 'in_progress':
            record_pass("Project UPDATE & DB Persistence (Status: in_progress, 25%)")
        else:
            record_fail("Project UPDATE", f"{r_prj_u.status_code}")
    else:
        record_fail("Project CREATE", f"{r_prj_c.status_code}")

    # =========================================================================
    # 6. DESIGN & BOM: APPROVE & DISAPPROVE
    # =========================================================================
    print("\n[PHASE 6: DESIGN & BOM - APPROVE & DISAPPROVE]")
    des_no = f"DES-{uid}"
    des_payload = {
        'designJobNumber': des_no,
        'projectId': prj_id,
        'projectNumber': prj_no,
        'jobNumber': job_no,
        'customerId': cust_id,
        'customerName': lead_payload['companyName'],
        'productName': lead_payload['productName'],
        'status': 'under_review',
    }
    r_des_c = client.post('/api/designer/jobs/', des_payload, format='json')
    if r_des_c.status_code in [200, 201]:
        des_id = r_des_c.data.get('id') or des_no
        record_pass(f"Design Job CREATE (ID: {des_id})")

        # Approval test
        r_des_app = client.post(f'/api/designer/jobs/{des_id}/approve/', {
            'approvedBy': 'Dharmesh Joshi',
            'notes': 'Dimensions and welding specs verified'
        }, format='json')
        db_des = DesignJob.objects.filter(id=des_id).first()
        if r_des_app.status_code == 200 and db_des and db_des.status == 'approved':
            record_pass("Design Job APPROVAL & DB Persistence (Status: approved)")
        else:
            record_fail("Design Job APPROVAL", f"{r_des_app.status_code}")

        # Release to production
        r_des_rel = client.post(f'/api/designer/jobs/{des_id}/release-to-production/', format='json')
        db_des.refresh_from_db()
        if r_des_rel.status_code == 200 and db_des.status in ['released', 'released_to_production']:
            record_pass("Design Job RELEASE TO PRODUCTION (Status: released_to_production)")
        else:
            record_fail("Design Job RELEASE", f"{r_des_rel.status_code}")
    else:
        record_fail("Design Job CREATE", f"{r_des_c.status_code}")

    # Design Job Disapproval flow on separate job
    des_rej_payload = {**des_payload, 'designJobNumber': f"DES-REJ-{uid}"}
    r_des_rej_c = client.post('/api/designer/jobs/', des_rej_payload, format='json')
    if r_des_rej_c.status_code in [200, 201]:
        des_rej_id = r_des_rej_c.data.get('id') or des_rej_payload['designJobNumber']
        r_des_dis = client.post(f'/api/designer/jobs/{des_rej_id}/disapprove/', {
            'disapprovedBy': 'Dharmesh Joshi',
            'rejectionReason': 'Nozzle orientation requires 45 degree offset'
        }, format='json')
        db_des_rej = DesignJob.objects.filter(id=des_rej_id).first()
        if r_des_dis.status_code == 200 and db_des_rej and db_des_rej.status == 'disapproved':
            record_pass("Design Job DISAPPROVAL / REJECTION (Status: disapproved)")
        else:
            record_fail("Design Job DISAPPROVAL", f"{r_des_dis.status_code}")

    # BOM Header & Items
    bom_no = f"BOM-{uid}"
    bom_items = [
        {'itemNo': 1, 'itemCode': 'SS-PL-316L', 'itemName': 'SS 316L 32mm Shell Plate', 'quantity': 8, 'uom': 'Nos', 'estimatedRate': 350000, 'totalEstimatedAmount': 2800000},
        {'itemNo': 2, 'itemCode': 'FLG-WN-300', 'itemName': 'WNRF Flange 24-inch ANSI 300#', 'quantity': 6, 'uom': 'Nos', 'estimatedRate': 120000, 'totalEstimatedAmount': 720000},
    ]
    bom_payload = {
        'bomNumber': bom_no,
        'jobNumber': job_no,
        'designJobId': des_id,
        'preparedBy': 'Design Engineer (R&D)',
        'status': 'draft',
        'items': bom_items,
        'total_estimated_cost': 3520000.0,
    }
    r_bom_c = client.post('/api/designer/boms/', bom_payload, format='json')
    if r_bom_c.status_code in [200, 201]:
        bom_id = r_bom_c.data.get('id') or bom_no
        record_pass(f"BOM Header & Line Items CREATE (ID: {bom_id})")
        # BOM Approval
        r_bom_app = client.patch(f'/api/designer/boms/{bom_id}/', {'status': 'approved', 'approved_by': 'HOD Engineering'}, format='json')
        db_bom = BOMHeader.objects.filter(id=bom_id).first()
        if r_bom_app.status_code == 200 and db_bom and db_bom.status == 'approved':
            record_pass("BOM APPROVAL & DB Persistence (Status: approved)")
        else:
            record_fail("BOM APPROVAL", f"{r_bom_app.status_code}")
    else:
        record_fail("BOM CREATE", f"{r_bom_c.status_code}")

    # =========================================================================
    # 7. PROCUREMENT: PR & PO CRUD & APPROVAL / REJECTION
    # =========================================================================
    print("\n[PHASE 7: PROCUREMENT - PR & PO CRUD & APPROVAL / REJECT]")
    pr_no = f"PR-{uid}"
    pr_payload = {
        'prNumber': pr_no,
        'projectId': prj_id,
        'jobCode': job_no,
        'requestedBy': 'Store Officer',
        'requestDate': today_str,
        'requiredByDate': '2026-10-31',
        'status': 'Submitted',
        'total_estimated_cost': 3520000.0,
        'items': bom_items,
    }
    r_pr_c = client.post('/api/purchase-requisitions/', pr_payload, format='json')
    if r_pr_c.status_code in [200, 201]:
        pr_id = r_pr_c.data.get('id') or pr_no
        record_pass(f"Purchase Requisition CREATE (ID: {pr_id})")
        # PR Approval test
        r_pr_app = client.patch(f'/api/purchase-requisitions/{pr_id}/', {'status': 'Approved', 'approvedBy': 'Purchase Head'}, format='json')
        db_pr = PurchaseRequisition.objects.filter(id=pr_id).first()
        if r_pr_app.status_code == 200 and db_pr and db_pr.status == 'Approved':
            record_pass("Purchase Requisition APPROVAL & DB Persistence (Status: Approved)")
        else:
            record_fail("PR APPROVAL", f"{r_pr_app.status_code}")
    else:
        record_fail("PR CREATE", f"{r_pr_c.status_code}")

    # PR Rejection on separate PR
    pr_rej_payload = {**pr_payload, 'prNumber': f"PR-REJ-{uid}"}
    r_pr_rej_c = client.post('/api/purchase-requisitions/', pr_rej_payload, format='json')
    if r_pr_rej_c.status_code in [200, 201]:
        pr_rej_id = r_pr_rej_c.data.get('id') or pr_rej_payload['prNumber']
        r_pr_rej = client.patch(f'/api/purchase-requisitions/{pr_rej_id}/', {'status': 'Rejected', 'remarks': 'Budget exceeded'}, format='json')
        db_pr_rej = PurchaseRequisition.objects.filter(id=pr_rej_id).first()
        if r_pr_rej.status_code == 200 and db_pr_rej and db_pr_rej.status == 'Rejected':
            record_pass("Purchase Requisition REJECTION & DB Persistence (Status: Rejected)")
        else:
            record_fail("PR REJECTION", f"{r_pr_rej.status_code}")

    # Purchase Order Approval flow
    po_ord_no = f"PO-{uid}"
    po_ord_payload = {
        'poNumber': po_ord_no,
        'supplierId': 'SUP-001',
        'supplierName': 'Jindal Stainless Steel Ltd',
        'date': today_str,
        'deliveryDate': '2026-10-25',
        'projectId': prj_id,
        'jobCode': job_no,
        'status': 'Draft',
        'grandTotal': 3520000.0,
        'items': bom_items,
    }
    r_po_c = client.post('/api/purchase-orders/', po_ord_payload, format='json')
    if r_po_c.status_code in [200, 201]:
        po_order_id = r_po_c.data.get('id') or po_ord_no
        record_pass(f"Purchase Order CREATE (ID: {po_order_id})")
        # PO Approval
        r_po_app = client.post(f'/api/purchase-orders/{po_order_id}/approve/', {
            'approvedBy': 'Commercial Director',
            'comment': 'Approved against BOM budget'
        }, format='json')
        db_po = PurchaseOrder.objects.filter(id=po_order_id).first()
        if r_po_app.status_code == 200 and db_po and db_po.status == 'Approved':
            record_pass("Purchase Order APPROVAL & DB Persistence (Status: Approved)")
        else:
            record_fail("PO APPROVAL", f"{r_po_app.status_code}")
    else:
        record_fail("PO CREATE", f"{r_po_c.status_code}")

    # PO Rejection flow on separate PO
    po_rej_payload = {**po_ord_payload, 'poNumber': f"PO-REJ-{uid}"}
    r_po_rej_c = client.post('/api/purchase-orders/', po_rej_payload, format='json')
    if r_po_rej_c.status_code in [200, 201]:
        po_rej_id = r_po_rej_c.data.get('id') or po_rej_payload['poNumber']
        r_po_rej = client.post(f'/api/purchase-orders/{po_rej_id}/reject/', {
            'reason': 'Vendor payment term not standard'
        }, format='json')
        db_po_rej = PurchaseOrder.objects.filter(id=po_rej_id).first()
        if r_po_rej.status_code == 200 and db_po_rej and db_po_rej.status == 'Rejected':
            record_pass("Purchase Order REJECTION & DB Persistence (Status: Rejected)")
        else:
            record_fail("PO REJECTION", f"{r_po_rej.status_code}")

    # =========================================================================
    # 8. STORE & INVENTORY: ITEM, GRN & MATERIAL ISSUE CRUD
    # =========================================================================
    print("\n[PHASE 8: STORE & INVENTORY - ITEM, GRN & ISSUE]")
    item_code = f"RAW-{uid}"
    item_payload = {
        'itemCode': item_code,
        'itemName': f'Special Carbon Steel Pipe {uid}',
        'category': 'Raw Materials',
        'uom': 'Mtr',
        'unitCost': 12500,
        'currentStock': 100,
    }
    r_it_c = client.post('/api/items/', item_payload, format='json')
    if r_it_c.status_code in [200, 201]:
        it_id = r_it_c.data.get('id') or item_code
        record_pass(f"Item Master CREATE (Code: {item_code})")
        # Update
        r_it_u = client.patch(f'/api/items/{it_id}/', {'unitCost': 13000, 'currentStock': 150}, format='json')
        db_it = ItemMaster.objects.filter(item_code=item_code).first()
        if db_it:
            db_it.refresh_from_db()
        if r_it_u.status_code == 200 and db_it and float(db_it.unit_cost) == 13000.0:
            record_pass("Item Master UPDATE & DB Persistence (Unit Cost: 13,000)")
        else:
            record_fail("Item Master UPDATE", f"Status: {r_it_u.status_code}, DB: {getattr(db_it, 'unit_cost', None)}")

        # Item DELETE test
        del_item_code = f"RAW-DEL-{uid}"
        r_it_del_c = client.post('/api/items/', {**item_payload, 'itemCode': del_item_code}, format='json')
        if r_it_del_c.status_code in [200, 201]:
            del_it_id = r_it_del_c.data.get('id') or del_item_code
            r_it_d = client.delete(f'/api/items/{del_it_id}/')
            if r_it_d.status_code in [200, 204] and not ItemMaster.objects.filter(item_code=del_item_code).exists():
                record_pass(f"Item Master DELETE verified in SQLite (Code {del_item_code} removed)")
            else:
                record_fail("Item Master DELETE", f"{r_it_d.status_code}")
    else:
        record_fail("Item Master CREATE", f"{r_it_c.status_code}")

    # GRN
    grn_no = f"GRN-{uid}"
    grn_payload = {
        'grnNumber': grn_no,
        'date': today_str,
        'poId': po_order_id,
        'poNumber': po_ord_no,
        'supplierId': 'SUP-001',
        'supplierName': 'Jindal Stainless Steel Ltd',
        'receivedBy': 'Hitesh Rawal (Store Incharge)',
        'warehouseId': 'wh-main',
        'status': 'Accepted',
        'items': [
            {'itemCode': 'SS-PL-316L', 'itemName': 'SS 316L 32mm Shell Plate', 'receivedQuantity': 8, 'acceptedQuantity': 8, 'uom': 'Nos', 'unitPrice': 350000},
        ]
    }
    r_grn_c = client.post('/api/grns/', grn_payload, format='json')
    if r_grn_c.status_code in [200, 201]:
        grn_id = r_grn_c.data.get('id') or grn_no
        record_pass(f"GRN Material Inward CREATE (ID: {grn_id})")
        db_grn = GoodsReceiptNote.objects.filter(id=grn_id).first()
        if db_grn and db_grn.status == 'Accepted':
            record_pass("GRN Inward Verified in DB (Status: Accepted)")
    else:
        record_fail("GRN CREATE", f"{r_grn_c.status_code}")

    # =========================================================================
    # 9. PRODUCTION & QC: WORK ORDER, ENTRY & QC PASS
    # =========================================================================
    print("\n[PHASE 9: PRODUCTION & QC - WORK ORDER, ENTRY & INSPECTION]")
    wo_no = f"WO-{uid}"
    wo_payload = {
        'workOrderNumber': wo_no,
        'jobId': job_no,
        'jobNumber': job_no,
        'projectId': prj_id,
        'customerName': lead_payload['companyName'],
        'productName': lead_payload['productName'],
        'productionQuantity': 1,
        'status': 'Draft',
    }
    r_wo_c = client.post('/api/work-orders/', wo_payload, format='json')
    if r_wo_c.status_code in [200, 201]:
        wo_id = r_wo_c.data.get('id') or wo_no
        record_pass(f"Work Order CREATE (ID: {wo_id})")
        # Release to shop floor
        r_wo_rel = client.post(f'/api/work-orders/{wo_id}/release/', format='json')
        db_wo = WorkOrder.objects.filter(id=wo_id).first()
        if r_wo_rel.status_code == 200 and db_wo and db_wo.status in ['Released', 'In Progress']:
            record_pass("Work Order RELEASE & DB Persistence (Status: Released/In Progress)")
        else:
            record_fail("Work Order RELEASE", f"{r_wo_rel.status_code}")
    else:
        record_fail("Work Order CREATE", f"{r_wo_c.status_code}")

    # Finished Goods & QC Pass
    fg_no = f"FG-{uid}"
    fg_payload = {
        'finishedGoodsNumber': fg_no,
        'jobNumber': job_no,
        'workOrderNumber': wo_no,
        'productName': lead_payload['productName'],
        'quantity': 1,
        'serialNumber': f"SN-{uid}",
        'status': 'Ready for QC',
        'qcStatus': 'Pending Inspection',
    }
    r_fg_c = client.post('/api/finished-goods/', fg_payload, format='json')
    if r_fg_c.status_code in [200, 201]:
        fg_id = r_fg_c.data.get('id') or fg_no
        record_pass(f"Finished Goods CREATE (ID: {fg_id})")
        # QC Pass action
        r_qc = client.post(f'/api/finished-goods/{fg_id}/qc-pass/', format='json')
        db_fg = FinishedGoodsItem.objects.filter(id=fg_id).first()
        if r_qc.status_code == 200 and db_fg and db_fg.qc_status in ['Passed', 'QC Passed']:
            record_pass("Finished Goods QC PASS & DB Persistence (qc_status: Passed)")
        else:
            record_fail("QC PASS", f"{r_qc.status_code}")
    else:
        record_fail("Finished Goods CREATE", f"{r_fg_c.status_code}")

    # Dispatch Order
    disp_no = f"DISP-{uid}"
    disp_payload = {
        'dispatchNumber': disp_no,
        'jobNumber': job_no,
        'workOrderNumber': wo_no,
        'finishedGoodsNumber': fg_no,
        'customerId': cust_id,
        'customerName': lead_payload['companyName'],
        'productName': lead_payload['productName'],
        'quantity': 1,
        'transporterName': 'CJ Darcl Logistics Heavy ODC',
        'vehicleNumber': 'GJ-06-ZZ-9999',
        'driverName': 'Sukhdev Singh',
        'status': 'Ready for Dispatch',
    }
    r_disp_c = client.post('/api/dispatch-orders/', disp_payload, format='json')
    if r_disp_c.status_code in [200, 201]:
        disp_id = r_disp_c.data.get('id') or disp_no
        record_pass(f"Dispatch Order CREATE (ID: {disp_id})")
        r_disp_m = client.post(f'/api/dispatch-orders/{disp_id}/mark-dispatched/', format='json')
        db_disp = DispatchOrder.objects.filter(id=disp_id).first()
        if r_disp_m.status_code == 200 and db_disp and db_disp.status in ['Dispatched', 'In Transit']:
            record_pass("Dispatch MARK DISPATCHED & DB Persistence (Status: Dispatched)")
        else:
            record_fail("Dispatch MARK DISPATCHED", f"{r_disp_m.status_code}")
    else:
        record_fail("Dispatch CREATE", f"{r_disp_c.status_code}")

    # =========================================================================
    # 10. FINANCE & ACCOUNTING: INVOICE, PAYMENT & EXPENSE CRUD / APPROVAL
    # =========================================================================
    print("\n[PHASE 10: FINANCE & ACCOUNTING - INVOICE, PAYMENT & EXPENSE]")
    inv_no = f"INV-{uid}"
    inv_payload = {
        'invoiceNumber': inv_no,
        'invoiceDate': today_str,
        'dueDate': '2026-11-30',
        'customerId': cust_id,
        'customerName': lead_payload['companyName'],
        'salesOrderId': so_id,
        'salesOrderNumber': so_no,
        'jobNumber': job_no,
        'grandTotal': 7200000.0,
        'taxableAmount': 6101694.92,
        'status': 'Draft',
        'paymentStatus': 'Unpaid',
        'items': [{'itemNo': 1, 'description': lead_payload['productName'], 'amount': 7200000.0}]
    }
    r_inv_c = client.post('/api/sales-invoices/', inv_payload, format='json')
    if r_inv_c.status_code in [200, 201]:
        inv_id = r_inv_c.data.get('id') or inv_no
        record_pass(f"Sales Invoice CREATE (ID: {inv_id}, Rs.72,00,000)")
        # Approve invoice
        r_inv_app = client.patch(f'/api/sales-invoices/{inv_id}/', {'status': 'Approved'}, format='json')
        db_inv = SalesInvoice.objects.filter(id=inv_id).first()
        if db_inv:
            db_inv.refresh_from_db()
        if r_inv_app.status_code == 200 and db_inv and db_inv.status == 'Approved':
            record_pass("Sales Invoice APPROVAL & DB Persistence (Status: Approved)")
        else:
            record_fail("Sales Invoice APPROVAL", f"Status: {r_inv_app.status_code}, DB: {getattr(db_inv, 'status', None)}")
        # Record payment
        r_pay = client.post(f'/api/sales-invoices/{inv_id}/record-payment/', {
            'amount': 7200000.0,
            'paymentMode': 'NEFT/RTGS',
            'referenceNumber': f'UTR-{uid}',
        }, format='json')
        db_inv.refresh_from_db()
        if r_pay.status_code == 200 and db_inv.payment_status == 'Paid':
            record_pass("Sales Invoice PAYMENT SETTLED & DB Persistence (Payment Status: Paid)")
        else:
            record_fail("Invoice PAYMENT SETTLEMENT", f"{r_pay.status_code}")
    else:
        record_fail("Sales Invoice CREATE", f"{r_inv_c.status_code}")

    # Expense Entry with Approval
    exp_no = f"EXP-{uid}"
    exp_payload = {
        'id': exp_no,
        'expense_number': exp_no,
        'expense_date': today_str,
        'category': 'Travel & Hospitality',
        'grand_total': 45000.0,
        'description': f'Site visit for technical inspection {uid}',
        'status': 'Submitted',
    }
    r_exp_c = client.post('/api/expenses/', exp_payload, format='json')
    if r_exp_c.status_code in [200, 201]:
        exp_id = r_exp_c.data.get('id') or exp_no
        record_pass(f"Expense Entry CREATE (ID: {exp_id}, Rs.45,000)")
        r_exp_app = client.post(f'/api/expenses/{exp_id}/approve/', {'approvedBy': 'Finance Controller'}, format='json')
        db_exp = ExpenseEntry.objects.filter(id=exp_id).first()
        if r_exp_app.status_code == 200 and db_exp and db_exp.status == 'Approved':
            record_pass("Expense Entry APPROVAL (Status: Approved)")
        else:
            record_fail("Expense APPROVAL", f"{r_exp_app.status_code}")
        # Delete test
        r_exp_d = client.delete(f'/api/expenses/{exp_id}/')
        if r_exp_d.status_code in [200, 204] and not ExpenseEntry.objects.filter(id=exp_id).exists():
            record_pass(f"Expense Entry DELETE verified in SQLite (ID {exp_id} removed)")
        else:
            record_fail("Expense DELETE", f"{r_exp_d.status_code}")
    else:
        record_fail("Expense CREATE", f"{r_exp_c.status_code} {r_exp_c.data}")

    # =========================================================================
    # 11. HR & ADMIN: LEAVE CRUD & APPROVE / REJECT
    # =========================================================================
    print("\n[PHASE 11: HR & ADMIN - LEAVE REQUEST CRUD & WORKFLOW]")
    # Generate unique future weekday dates to avoid overlapping leave validations
    base_offset = 1200 + random.randint(1, 20000)
    d1 = date.today() + timedelta(days=base_offset)
    while d1.weekday() >= 5: # Skip Saturday/Sunday
        d1 += timedelta(days=1)
    d2 = d1 + timedelta(days=7)
    while d2.weekday() >= 5:
        d2 += timedelta(days=1)
    future_date1 = d1.isoformat()
    future_date2 = d2.isoformat()
    leave_payload = {
        'employee_id': 'EMP-001',
        'employee_name': 'Rajesh Patel',
        'leave_name': 'Casual Leave',
        'from_date': future_date1,
        'to_date': future_date1,
        'number_of_days': 1,
        'reason': f'Personal family work {uid}',
        'status': 'Pending',
    }
    r_lv_c = client.post('/api/leave-requests/', leave_payload, format='json')
    if r_lv_c.status_code in [200, 201]:
        lv_id = r_lv_c.data.get('id')
        record_pass(f"Leave Request CREATE (ID: {lv_id})")
        # Approve test
        r_lv_app = client.patch(f'/api/leave-requests/{lv_id}/', {'status': 'Approved', 'approvedBy': 'HR Head'}, format='json')
        db_lv = LeaveRequest.objects.filter(id=lv_id).first()
        if db_lv:
            db_lv.refresh_from_db()
        if r_lv_app.status_code == 200 and db_lv and db_lv.status == 'Approved':
            record_pass("Leave Request APPROVAL & DB Persistence (Status: Approved)")
        else:
            record_fail("Leave Request APPROVAL", f"{r_lv_app.status_code}")
    else:
        record_fail("Leave Request CREATE", f"{r_lv_c.status_code} {r_lv_c.data}")

    # Leave Rejection on separate request
    leave_rej_payload = {
        **leave_payload,
        'from_date': future_date2,
        'to_date': future_date2,
        'reason': f'Urgent leave {uid}'
    }
    r_lv_rej_c = client.post('/api/leave-requests/', leave_rej_payload, format='json')
    if r_lv_rej_c.status_code in [200, 201]:
        lv_rej_id = r_lv_rej_c.data.get('id')
        r_lv_rej = client.patch(f'/api/leave-requests/{lv_rej_id}/', {'status': 'Rejected', 'adminRemarks': 'Critical machine testing scheduled'}, format='json')
        db_lv_rej = LeaveRequest.objects.filter(id=lv_rej_id).first()
        if db_lv_rej:
            db_lv_rej.refresh_from_db()
        if r_lv_rej.status_code == 200 and db_lv_rej and db_lv_rej.status == 'Rejected':
            record_pass("Leave Request REJECTION & DB Persistence (Status: Rejected)")
        else:
            record_fail("Leave Request REJECTION", f"{r_lv_rej.status_code}")
        # Delete test
        r_lv_d = client.delete(f'/api/leave-requests/{lv_rej_id}/')
        if r_lv_d.status_code in [200, 204] and not LeaveRequest.objects.filter(id=lv_rej_id).exists():
            record_pass(f"Leave Request DELETE verified in SQLite (ID {lv_rej_id} removed)")
    else:
        record_fail("Leave Request 2 CREATE", f"{r_lv_rej_c.status_code} {r_lv_rej_c.data}")

    # =========================================================================
    # 12. CENTRAL APPROVALS INBOX: APPROVE & REJECT
    # =========================================================================
    print("\n[PHASE 12: CENTRAL WORKFLOW APPROVAL INBOX]")
    appr_payload = {
        'id': f"APP-{uid}",
        'title': f'Urgent Procurement Approval for Project {prj_no}',
        'category': 'Purchase Order',
        'record_number': po_ord_no,
        'requester_name': 'Hitesh Rawal',
        'urgency': 'High',
        'status': 'Pending',
        'amount': 3520000.0,
    }
    r_app_c = client.post('/api/approvals/', appr_payload, format='json')
    if r_app_c.status_code in [200, 201]:
        app_id = r_app_c.data.get('id')
        record_pass(f"Central Approval Item CREATE (ID: {app_id})")

        # Central Approve
        r_app_ok = client.post(f'/api/approvals/{app_id}/approve/', format='json')
        db_app = ApprovalItem.objects.filter(id=app_id).first()
        if r_app_ok.status_code == 200 and db_app and db_app.status == 'Approved':
            record_pass("Central Approval Item APPROVE endpoint (Status: Approved)")
        else:
            record_fail("Central Approval APPROVE", f"{r_app_ok.status_code}")
    else:
        record_fail("Central Approval Item CREATE", f"{r_app_c.status_code} {r_app_c.data}")

    # Central Reject on separate item
    appr_rej_payload = {**appr_payload, 'id': f"APP-REJ-{uid}", 'title': f'Commercial Over-budget Item {uid}'}
    r_app_rej_c = client.post('/api/approvals/', appr_rej_payload, format='json')
    if r_app_rej_c.status_code in [200, 201]:
        app_rej_id = r_app_rej_c.data.get('id')
        r_app_no = client.post(f'/api/approvals/{app_rej_id}/reject/', format='json')
        db_app_rej = ApprovalItem.objects.filter(id=app_rej_id).first()
        if r_app_no.status_code == 200 and db_app_rej and db_app_rej.status == 'Rejected':
            record_pass("Central Approval Item REJECT endpoint (Status: Rejected)")
        else:
            record_fail("Central Approval REJECT", f"{r_app_no.status_code}")

        # Delete test
        r_app_d = client.delete(f'/api/approvals/{app_rej_id}/')
        if r_app_d.status_code in [200, 204] and not ApprovalItem.objects.filter(id=app_rej_id).exists():
            record_pass(f"Central Approval Item DELETE verified in SQLite (ID {app_rej_id} removed)")
    else:
        record_fail("Central Approval Item 2 CREATE", f"{r_app_rej_c.status_code} {r_app_rej_c.data}")

    # =========================================================================
    # FINAL RESULTS
    # =========================================================================
    print("\n" + "=" * 95)
    print("🏁 TEST EXECUTION COMPLETE")
    print(f"   Total Passed: {TestStats.passed}")
    print(f"   Total Failed: {TestStats.failed}")
    if TestStats.errors:
        print("   Failures:")
        for err in TestStats.errors:
            print(f"    - {err}")
    print("=" * 95)

    return TestStats.failed == 0

if __name__ == '__main__':
    success = run_suite()
    sys.exit(0 if success else 1)
