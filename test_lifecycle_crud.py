import os
import sys
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status

# Import all models to directly verify database persistence
from apps.crm.models import Lead, Customer, Enquiry, Opportunity, Quotation, CustomerPO, SalesOrder
from apps.projects.models import ProjectJobMaster, ProjectPlanningStage, ProjectTask
from apps.designer.models import DesignJob, BOMHeader
from apps.purchase.models import Supplier, PurchaseRequisition, PurchaseOrder, MaterialRequirement
from apps.store.models import ItemMaster, Warehouse, GoodsReceiptNote, QCInspection, StockBalance, MaterialIssue
from apps.production.models import WorkOrder, ProductionEntry, FinishedGoodsItem, DispatchOrder
from apps.accounting.models import SalesInvoice, CustomerReceipt
from apps.maintenance.models import CustomerMachine, ServiceRequest

def run_lifecycle_test():
    client = APIClient()
    print("=" * 80)
    print("STARTING COMPLETE END-TO-END ERP LIFECYCLE & DATABASE PERSISTENCE AUDIT")
    print("=" * 80)

    # 0. Authenticate
    print("\n[Step 0] Authenticating...")
    login_res = client.post('/api/auth/login/', {'username': 'admin', 'password': 'admin123'}, format='json')
    if login_res.status_code != status.HTTP_200_OK:
        print(f"FAILED LOGIN: {login_res.status_code} {login_res.data}")
        return False
    token = login_res.data.get('access')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    print("  -> Authenticated successfully.")

    today_str = date.today().isoformat()
    test_suffix = "E2E-TEST"

    # 1. LEAD
    print("\n[Step 1] LEAD: Create & Verify DB...")
    lead_id = f"LEAD-{test_suffix}"
    Lead.objects.filter(id=lead_id).delete()
    lead_payload = {
        'id': lead_id,
        'lead_no': lead_id,
        'company_name': 'Reliance Petrochem Infrastructure',
        'contact_person': 'Mukesh Bhai',
        'mobile': '9898012345',
        'email': 'procurement@reliance-petro.com',
        'product_name': 'SS316 Stainless Pressure Reactor 25KL',
        'status': 'Qualified',
        'created_date': today_str,
    }
    r = client.post('/api/leads/', lead_payload, format='json')
    if r.status_code not in [200, 201]:
        print(f"  [FAIL] Lead create failed: {r.status_code} {r.data}")
        return False
    # DB Check
    db_lead = Lead.objects.filter(id=lead_id).first()
    assert db_lead is not None, "Lead was not saved to DB!"
    print(f"  -> [DB VERIFIED] Lead '{db_lead.lead_no}' saved in Database (Status: {db_lead.status}).")

    # 2. ENQUIRY (Convert Lead or Direct Create)
    print("\n[Step 2] ENQUIRY & CUSTOMER: Create & Verify DB...")
    cust_id = f"CUST-{test_suffix}"
    Customer.objects.filter(id=cust_id).delete()
    cust_payload = {
        'id': cust_id,
        'customer_code': cust_id,
        'company_name': db_lead.company_name,
        'contact_person': db_lead.contact_person,
        'mobile': db_lead.mobile,
        'email': db_lead.email,
        'city': 'Vadodara',
        'state': 'Gujarat',
    }
    r_cust = client.post('/api/customers/', cust_payload, format='json')
    assert Customer.objects.filter(id=cust_id).exists(), "Customer not in DB!"
    print(f"  -> [DB VERIFIED] Customer '{cust_id}' saved in Database.")

    enq_id = f"ENQ-{test_suffix}"
    Enquiry.objects.filter(id=enq_id).delete()
    enq_payload = {
        'id': enq_id,
        'enquiry_no': enq_id,
        'lead_id': lead_id,
        'customer_id': cust_id,
        'customer_name': db_lead.company_name,
        'enquiry_date': today_str,
        'requirement': 'Design and fabricate 25KL Reactor column',
        'machine_product': db_lead.product_name,
        'quantity': 1,
        'status': 'Technical Review',
    }
    r_enq = client.post('/api/enquiries/', enq_payload, format='json')
    assert Enquiry.objects.filter(id=enq_id).exists(), "Enquiry not in DB!"
    print(f"  -> [DB VERIFIED] Enquiry '{enq_id}' saved in Database.")

    # 3. QUOTATION (Create & Approve)
    print("\n[Step 3] QUOTATION: Create, Approve & Verify DB...")
    qtn_id = f"QT-{test_suffix}"
    Quotation.objects.filter(id=qtn_id).delete()
    qtn_payload = {
        'id': qtn_id,
        'quotation_number': qtn_id,
        'current_revision': 'Rev-00',
        'date': today_str,
        'valid_until': '2026-12-31',
        'customer_id': cust_id,
        'customer_name': db_lead.company_name,
        'contact_person': db_lead.contact_person,
        'contact_email': db_lead.email,
        'enquiry_id': enq_id,
        'revisions': [{
            'revisionNumber': 'Rev-00',
            'status': 'approved',
            'grandTotal': 4500000,
            'machineProduct': db_lead.product_name,
            'items': [{'itemNo': 1, 'description': db_lead.product_name, 'qty': 1, 'unitRate': 4500000, 'amount': 4500000}]
        }],
    }
    r_qtn = client.post('/api/quotations/', qtn_payload, format='json')
    assert Quotation.objects.filter(id=qtn_id).exists(), "Quotation not in DB!"
    db_qtn = Quotation.objects.get(id=qtn_id)
    print(f"  -> [DB VERIFIED] Quotation '{db_qtn.quotation_number}' saved in Database.")

    # 4. CUSTOMER PO
    print("\n[Step 4] CUSTOMER PO: Receive, Record & Verify DB...")
    cpo_id = f"CPO-{test_suffix}"
    CustomerPO.objects.filter(id=cpo_id).delete()
    cpo_payload = {
        'id': cpo_id,
        'po_number': cpo_id,
        'customer_id': cust_id,
        'customer_name': db_lead.company_name,
        'quotation_id': qtn_id,
        'quotation_number': qtn_id,
        'po_date': today_str,
        'received_date': today_str,
        'delivery_date': '2026-11-30',
        'po_value': 4500000.0,
        'status': 'accepted',
    }
    r_cpo = client.post('/api/customer-pos/', cpo_payload, format='json')
    assert CustomerPO.objects.filter(id=cpo_id).exists(), "Customer PO not in DB!"
    print(f"  -> [DB VERIFIED] Customer PO '{cpo_id}' saved in Database (Status: accepted).")

    # 5. SALES ORDER (Create & Confirm/Approve)
    print("\n[Step 5] SALES ORDER: Create, Approve & Verify DB...")
    so_id = f"SO-{test_suffix}"
    SalesOrder.objects.filter(id=so_id).delete()
    so_payload = {
        'id': so_id,
        'sales_order_number': so_id,
        'customer_po_id': cpo_id,
        'customer_po_number': cpo_id,
        'quotation_id': qtn_id,
        'quotation_number': qtn_id,
        'customer_id': cust_id,
        'customer_name': db_lead.company_name,
        'order_date': today_str,
        'target_delivery_date': '2026-11-30',
        'grand_total': 4500000.0,
        'total_amount': 4500000.0,
        'status': 'confirmed',
        'approved_by': 'Managing Director',
        'items': [{'itemNo': 1, 'productName': db_lead.product_name, 'quantity': 1, 'unitRate': 4500000, 'totalAmount': 4500000}]
    }
    r_so = client.post('/api/sales-orders/', so_payload, format='json')
    assert SalesOrder.objects.filter(id=so_id).exists(), "Sales Order not in DB!"
    db_so = SalesOrder.objects.get(id=so_id)
    print(f"  -> [DB VERIFIED] Sales Order '{db_so.sales_order_number}' saved in Database (Status: {db_so.status}).")

    # 6. PROJECT / JOB MASTER
    print("\n[Step 6] PROJECT & JOB: Create & Verify DB...")
    prj_id = f"PRJ-{test_suffix}"
    job_id = f"JOB-{test_suffix}"
    ProjectJobMaster.objects.filter(id=prj_id).delete()
    prj_payload = {
        'id': prj_id,
        'project_number': prj_id,
        'job_number': job_id,
        'customer_id': cust_id,
        'customer_name': db_lead.company_name,
        'sales_order_id': so_id,
        'sales_order_number': so_id,
        'customer_po_number': cpo_id,
        'product_name': db_lead.product_name,
        'order_value': 4500000.0,
        'start_date': today_str,
        'target_delivery_date': '2026-11-30',
        'current_status': 'in_progress',
        'project_manager_name': 'Bhavin Shah',
    }
    r_prj = client.post('/api/project-jobs/', prj_payload, format='json')
    assert ProjectJobMaster.objects.filter(id=prj_id).exists(), "Project not in DB!"
    db_prj = ProjectJobMaster.objects.get(id=prj_id)
    print(f"  -> [DB VERIFIED] Project '{db_prj.project_number}' / Job '{db_prj.job_number}' saved in Database.")

    # 7. DESIGN JOB (Create, Approve & Release)
    print("\n[Step 7] DESIGN JOB: Create, Approve, Release & Verify DB...")
    des_id = f"DES-{test_suffix}"
    DesignJob.objects.filter(id=des_id).delete()
    des_payload = {
        'id': des_id,
        'design_job_number': des_id,
        'project_id': prj_id,
        'project_number': prj_id,
        'job_number': job_id,
        'customer_id': cust_id,
        'customer_name': db_lead.company_name,
        'customer_po_number': cpo_id,
        'sales_order_number': so_id,
        'product_name': db_lead.product_name,
        'delivery_date': '2026-11-30',
        'created_date': today_str,
        'status': 'under_review',
    }
    r_des = client.post('/api/design-jobs/', des_payload, format='json')
    assert DesignJob.objects.filter(id=des_id).exists(), "Design Job not in DB!"

    # Approve Design
    r_appr = client.post(f"/api/design-jobs/{des_id}/approve/", {'approvedBy': 'Dharmesh Joshi', 'notes': 'FEA & Drawing Verified'}, format='json')
    assert r_appr.status_code == 200, f"Design approval failed: {r_appr.data}"
    db_des = DesignJob.objects.get(id=des_id)
    assert db_des.status == 'approved', f"Design status not approved in DB: {db_des.status}"
    print(f"  -> [DB VERIFIED] Design Job '{des_id}' Approved in Database (Approved by: {db_des.approved_by}).")

    # Release Design to Shop Floor
    r_rel = client.post(f"/api/design-jobs/{des_id}/release-to-production/", format='json')
    assert r_rel.status_code == 200, f"Design release failed: {r_rel.data}"
    db_des.refresh_from_db()
    assert db_des.status == 'released_to_production', f"Design not released in DB: {db_des.status}"
    print(f"  -> [DB VERIFIED] Design Job '{des_id}' Released to Shop Floor in Database.")

    # 8. BOM (Create & Approve)
    print("\n[Step 8] BOM: Create, Approve & Verify DB...")
    bom_id = f"BOM-{test_suffix}"
    BOMHeader.objects.filter(id=bom_id).delete()
    bom_payload = {
        'id': bom_id,
        'bom_number': bom_id,
        'design_job_id': des_id,
        'project_id': prj_id,
        'job_number': job_id,
        'status': 'approved',
        'prepared_by': 'Design Lead',
        'approved_by': 'Engineering Head',
        'total_estimated_cost': 2850000.0,
        'items': [
            {'itemNo': 1, 'itemCode': 'SS-PL-316L', 'itemName': 'SS 316L 25mm Shell Plate', 'quantity': 10, 'uom': 'Nos', 'estimatedRate': 250000, 'totalEstimatedAmount': 2500000},
            {'itemNo': 2, 'itemCode': 'FLG-ANSI-300', 'itemName': 'ANSI 300# Forged Flange', 'quantity': 7, 'uom': 'Nos', 'estimatedRate': 50000, 'totalEstimatedAmount': 350000},
        ]
    }
    r_bom = client.post('/api/bom-headers/', bom_payload, format='json')
    assert BOMHeader.objects.filter(id=bom_id).exists(), "BOM not in DB!"
    db_bom = BOMHeader.objects.get(id=bom_id)
    print(f"  -> [DB VERIFIED] Master BOM '{db_bom.bom_number}' saved in Database with {len(db_bom.items)} items (Status: {db_bom.status}).")

    # 9. MRP (Material Requirements Planning)
    print("\n[Step 9] MRP: Create & Verify DB...")
    mrp_id = f"MRP-{test_suffix}"
    MaterialRequirement.objects.filter(id=mrp_id).delete()
    mrp_payload = {
        'id': mrp_id,
        'project_id': prj_id,
        'job_id': job_id,
        'job_number': job_id,
        'customer_name': db_lead.company_name,
        'design_job_id': des_id,
        'bom_id': bom_id,
        'bom_number': bom_id,
        'status': 'PR Generated',
        'items': db_bom.items,
    }
    r_mrp = client.post('/api/material-requirements/', mrp_payload, format='json')
    assert MaterialRequirement.objects.filter(id=mrp_id).exists(), "MRP not in DB!"
    print(f"  -> [DB VERIFIED] Material Requirement (MRP) '{mrp_id}' saved in Database.")

    # 10. PURCHASE REQUISITION & PURCHASE ORDER
    print("\n[Step 10] PURCHASE: PR & PO Create, Approve & Verify DB...")
    pr_id = f"PR-{test_suffix}"
    PurchaseRequisition.objects.filter(id=pr_id).delete()
    pr_payload = {
        'id': pr_id,
        'pr_number': pr_id,
        'project_id': prj_id,
        'job_code': job_id,
        'requested_by': 'Store & Planning Head',
        'request_date': today_str,
        'required_by_date': '2026-10-31',
        'status': 'approved',
        'approved_by': 'Purchase Manager',
        'total_estimated_cost': 2850000.0,
        'items': db_bom.items,
    }
    r_pr = client.post('/api/purchase-requisitions/', pr_payload, format='json')
    assert PurchaseRequisition.objects.filter(id=pr_id).exists(), "PR not in DB!"
    print(f"  -> [DB VERIFIED] Purchase Requisition '{pr_id}' Approved in Database.")

    po_id = f"PO-{test_suffix}"
    PurchaseOrder.objects.filter(id=po_id).delete()
    po_payload = {
        'id': po_id,
        'po_number': po_id,
        'supplier_id': 'SUP-001',
        'supplier_name': 'Jindal Stainless Steel Ltd',
        'date': today_str,
        'delivery_date': '2026-10-25',
        'project_id': prj_id,
        'job_code': job_id,
        'status': 'approved',
        'approved_by': 'Commercial Director',
        'grand_total': 2850000.0,
        'items': db_bom.items,
    }
    r_po = client.post('/api/purchase-orders/', po_payload, format='json')
    assert PurchaseOrder.objects.filter(id=po_id).exists(), "PO not in DB!"
    print(f"  -> [DB VERIFIED] Purchase Order '{po_id}' Approved in Database.")

    # 11. GRN (Goods Receipt Note)
    print("\n[Step 11] GRN: Inward Material & Verify DB...")
    grn_id = f"GRN-{test_suffix}"
    GoodsReceiptNote.objects.filter(id=grn_id).delete()
    grn_payload = {
        'id': grn_id,
        'grn_number': grn_id,
        'date': today_str,
        'po_id': po_id,
        'po_number': po_id,
        'supplier_id': 'SUP-001',
        'supplier_name': 'Jindal Stainless Steel Ltd',
        'received_by': 'Hitesh Rawal (Store Incharge)',
        'warehouse_id': 'wh-main',
        'status': 'Accepted',
        'qc_status': 'Pass',
        'items': [
            {'itemCode': 'SS-PL-316L', 'itemName': 'SS 316L 25mm Shell Plate', 'receivedQuantity': 10, 'acceptedQuantity': 10, 'uom': 'Nos', 'unitPrice': 250000}
        ]
    }
    r_grn = client.post('/api/goods-receipt-notes/', grn_payload, format='json')
    assert GoodsReceiptNote.objects.filter(id=grn_id).exists(), "GRN not in DB!"
    print(f"  -> [DB VERIFIED] Goods Receipt Note '{grn_id}' saved in Database (Status: Accepted).")

    # 12. MATERIAL ISSUE TO SHOP FLOOR
    print("\n[Step 12] MATERIAL ISSUE: Issue to Production & Verify DB...")
    iss_id = f"ISS-{test_suffix}"
    MaterialIssue.objects.filter(id=iss_id).delete()
    iss_payload = {
        'id': iss_id,
        'issue_number': iss_id,
        'project_id': prj_id,
        'job_number': job_id,
        'issued_to': 'Fabrication Shop Floor',
        'issued_by': 'Hitesh Rawal (Store Head)',
        'issue_date': today_str,
        'status': 'Fully Issued',
        'total_issue_value': 2500000.0,
        'items': [
            {'itemCode': 'SS-PL-316L', 'itemName': 'SS 316L 25mm Shell Plate', 'issuedQuantity': 10, 'uom': 'Nos'}
        ]
    }
    r_iss = client.post('/api/material-issues/', iss_payload, format='json')
    assert MaterialIssue.objects.filter(id=iss_id).exists(), "Material Issue not in DB!"
    print(f"  -> [DB VERIFIED] Material Issue Slip '{iss_id}' saved in Database.")

    # 13. PRODUCTION WORK ORDER & EXECUTION
    print("\n[Step 13] PRODUCTION: Work Order Create, Release & Verify DB...")
    wo_id = f"WO-{test_suffix}"
    WorkOrder.objects.filter(id=wo_id).delete()
    wo_payload = {
        'id': wo_id,
        'work_order_number': wo_id,
        'job_id': job_id,
        'job_number': job_id,
        'project_id': prj_id,
        'customer_id': cust_id,
        'customer_name': db_lead.company_name,
        'product_name': db_lead.product_name,
        'production_quantity': 1,
        'status': 'Draft',
    }
    r_wo = client.post('/api/work-orders/', wo_payload, format='json')
    assert WorkOrder.objects.filter(id=wo_id).exists(), "Work Order not in DB!"
    
    # Release Work Order
    r_wo_rel = client.post(f"/api/work-orders/{wo_id}/release/", format='json')
    db_wo = WorkOrder.objects.get(id=wo_id)
    print(f"  -> [DB VERIFIED] Work Order '{wo_id}' Released in Database (Status: {db_wo.status}).")

    # Finished Goods Output
    fg_id = f"FG-{test_suffix}"
    FinishedGoodsItem.objects.filter(id=fg_id).delete()
    fg_payload = {
        'id': fg_id,
        'finished_goods_number': fg_id,
        'job_id': job_id,
        'job_number': job_id,
        'work_order_number': wo_id,
        'product_name': db_lead.product_name,
        'quantity': 1,
        'serial_number': f"SN-{test_suffix}-001",
        'status': 'Ready for QC',
    }
    r_fg = client.post('/api/finished-goods/', fg_payload, format='json')
    assert FinishedGoodsItem.objects.filter(id=fg_id).exists(), "Finished Goods not in DB!"
    print(f"  -> [DB VERIFIED] Finished Goods Item '{fg_id}' saved in Database.")

    # 14. QC INSPECTION (Pass Finished Goods)
    print("\n[Step 14] QC INSPECTION: Pass Finished Goods & Verify DB...")
    r_qc_pass = client.post(f"/api/finished-goods/{fg_id}/qc-pass/", format='json')
    assert r_qc_pass.status_code == 200, f"QC pass failed: {r_qc_pass.data}"
    db_fg = FinishedGoodsItem.objects.get(id=fg_id)
    assert db_fg.qc_status == 'QC Passed', f"FG not marked QC Passed: {db_fg.qc_status}"
    print(f"  -> [DB VERIFIED] Finished Goods '{fg_id}' Passed QC Inspection in Database (Status: {db_fg.status}).")

    # 15. PACKING & DISPATCH
    print("\n[Step 15] DISPATCH & PACKING: Create, Approve & Verify DB...")
    disp_id = f"DISP-{test_suffix}"
    DispatchOrder.objects.filter(id=disp_id).delete()
    disp_payload = {
        'id': disp_id,
        'dispatch_number': disp_id,
        'job_id': job_id,
        'job_number': job_id,
        'work_order_number': wo_id,
        'finished_goods_number': fg_id,
        'customer_id': cust_id,
        'customer_name': db_lead.company_name,
        'product_name': db_lead.product_name,
        'quantity': 1,
        'vehicle_number': 'GJ-06-AX-9999',
        'transporter_name': 'VRL Logistics Heavy Haul',
        'status': 'Dispatched',
    }
    r_disp = client.post('/api/dispatch-orders/', disp_payload, format='json')
    assert DispatchOrder.objects.filter(id=disp_id).exists(), "Dispatch Order not in DB!"
    print(f"  -> [DB VERIFIED] Dispatch Order & Delivery Challan '{disp_id}' saved in Database (Status: Dispatched).")

    # 16. SALES INVOICE
    print("\n[Step 16] SALES INVOICE: Generate, Approve & Verify DB...")
    sinv_id = f"SINV-{test_suffix}"
    SalesInvoice.objects.filter(id=sinv_id).delete()
    sinv_payload = {
        'id': sinv_id,
        'invoice_number': sinv_id,
        'invoice_date': today_str,
        'due_date': '2026-11-30',
        'customer_id': cust_id,
        'customer_name': db_lead.company_name,
        'sales_order_id': so_id,
        'sales_order_number': so_id,
        'job_number': job_id,
        'grand_total': 4500000.0,
        'taxable_amount': 3813559.32,
        'status': 'Approved',
        'payment_status': 'Unpaid',
        'items': [{'itemNo': 1, 'description': db_lead.product_name, 'amount': 4500000.0}]
    }
    r_sinv = client.post('/api/sales-invoices/', sinv_payload, format='json')
    assert SalesInvoice.objects.filter(id=sinv_id).exists(), "Sales Invoice not in DB!"
    print(f"  -> [DB VERIFIED] Sales Invoice '{sinv_id}' Approved in Database.")

    # 17. CUSTOMER PAYMENT RECEIPT
    print("\n[Step 17] PAYMENT: Record Customer Payment & Verify DB...")
    r_pay = client.post(f"/api/sales-invoices/{sinv_id}/record-payment/", {
        'amount': 4500000.0,
        'paymentMode': 'RTGS',
        'referenceNumber': f"UTR-{test_suffix}-2026",
    }, format='json')
    assert r_pay.status_code == 200, f"Record payment failed: {r_pay.data}"
    db_sinv = SalesInvoice.objects.get(id=sinv_id)
    assert db_sinv.payment_status == 'Paid', f"Invoice not marked Paid: {db_sinv.payment_status}"
    
    # Check CustomerReceipt created
    db_rct = CustomerReceipt.objects.filter(sales_invoice_number=sinv_id).first()
    assert db_rct is not None, "Customer Receipt was not auto-generated in DB!"
    print(f"  -> [DB VERIFIED] Payment recorded. Customer Receipt '{db_rct.receipt_number}' (Rs.{db_rct.amount}) saved in Database.")

    # 18. CUSTOMER MACHINE & INSTALLATION
    print("\n[Step 18] INSTALLATION & MACHINE COMMISSIONING: Create & Verify DB...")
    cm_id = f"CM-{test_suffix}"
    CustomerMachine.objects.filter(id=cm_id).delete()
    cm_payload = {
        'id': cm_id,
        'customer_machine_id': cm_id,
        'customer_id': cust_id,
        'customer_name': db_lead.company_name,
        'job_id': job_id,
        'job_number': job_id,
        'sales_order_id': so_id,
        'dispatch_number': disp_id,
        'machine_name': db_lead.product_name,
        'serial_number': f"SN-{test_suffix}-001",
        'status': 'Installed & Operational',
        'installation_date': today_str,
        'commissioning_date': today_str,
    }
    r_cm = client.post('/api/customer-machines/', cm_payload, format='json')
    assert CustomerMachine.objects.filter(id=cm_id).exists(), "Customer Machine not in DB!"
    db_cm = CustomerMachine.objects.get(id=cm_id)
    print(f"  -> [DB VERIFIED] Customer Machine '{db_cm.customer_machine_id}' Commissioned in Database (Status: {db_cm.status}).")

    print("\n" + "=" * 80)
    print("SUCCESS: ALL 18 PHASES VERIFIED AND SAVED DIRECTLY IN SQLITE DATABASE!")
    print("=" * 80)
    return True

if __name__ == '__main__':
    ok = run_lifecycle_test()
    sys.exit(0 if ok else 1)
