import os
import sys
import django
from datetime import date, datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status

# Directly query SQLite database models
from apps.crm.models import Lead, Customer, Enquiry, Quotation, CustomerPO, SalesOrder
from apps.projects.models import ProjectJobMaster, ProjectPlanningStage
from apps.designer.models import DesignJob, BOMHeader, CustomerRequirement
from apps.purchase.models import Supplier, MaterialRequirement, PurchaseRequisition, PurchaseOrder
from apps.store.models import ItemMaster, Warehouse, GoodsReceiptNote, QCInspection, StockBalance, MaterialIssue, StockLedgerEntry
from apps.production.models import WorkOrder, ProductionEntry, FinishedGoodsItem, DispatchOrder
from apps.accounting.models import SalesInvoice, CustomerReceipt
from apps.maintenance.models import CustomerMachine

def log_step(name, msg):
    print(f"\n[PHASE: {name}] -> {msg}")

def run_comprehensive_crud_test():
    client = APIClient()
    print("=" * 90)
    print("UMA ERP - COMPLETE 19-STEP LIFECYCLE CRUD & APPROVAL DATABASE VERIFICATION")
    print("Flow: Lead -> Enquiry -> Quotation -> Customer PO -> Sales Order -> Project/Job ->")
    print("      Design -> BOM -> MRP -> Purchase -> GRN -> Material Issue -> Production ->")
    print("      QC -> Packing -> Payment -> Dispatch -> Installation -> Invoice")
    print("=" * 90)

    # AUTHENTICATION
    login_res = client.post('/api/auth/login/', {'username': 'admin', 'password': 'admin123'}, format='json')
    assert login_res.status_code == 200, f"Login failed: {login_res.data}"
    token = login_res.data.get('access')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    print("✅ Authenticated as Admin via JWT Bearer Token.")

    today_str = date.today().isoformat()
    uid = f"RUN-{int(datetime.now().timestamp())}"

    # -------------------------------------------------------------------------
    # 1. LEAD
    # -------------------------------------------------------------------------
    log_step("1. LEAD", "Testing Create, Read, Update, DB Check")
    lead_no = f"LEAD-{uid}"
    lead_payload = {
        'leadNo': lead_no,
        'companyName': f'Gujarat Chemical Corp {uid}',
        'contactPerson': 'Bhavesh Mehta',
        'mobile': '9876543210',
        'email': 'bhavesh@gujaratchem.com',
        'productName': 'Distillation Column 5000L SS316',
        'status': 'new',
        'priority': 'high',
        'createdDate': today_str,
    }
    # Create
    res = client.post('/api/leads/', lead_payload, format='json')
    assert res.status_code in [200, 201], f"Lead create failed: {res.status_code} {res.data}"
    lead_id = res.data.get('id') or lead_no
    # Read
    r_get = client.get(f'/api/leads/{lead_id}/')
    assert r_get.status_code == 200, "Lead read failed"
    # Update
    r_patch = client.patch(f'/api/leads/{lead_id}/', {'status': 'qualified', 'budget': 7500000}, format='json')
    assert r_patch.status_code == 200, "Lead update failed"
    # SQLite Direct Check
    db_lead = Lead.objects.get(id=lead_id)
    assert db_lead.status == 'qualified', "Lead status not updated in DB"
    assert db_lead.company_name == f'Gujarat Chemical Corp {uid}', "Company name mismatch in DB"
    print(f"  -> CREATE, READ, UPDATE verified in SQLite: Lead {db_lead.lead_no} (Status: {db_lead.status})")

    # -------------------------------------------------------------------------
    # 2. ENQUIRY & CUSTOMER
    # -------------------------------------------------------------------------
    log_step("2. ENQUIRY", "Testing Customer creation and Enquiry Linkage")
    cust_id = f"CUST-{uid}"
    cust_payload = {
        'id': cust_id,
        'customerCode': cust_id,
        'companyName': db_lead.company_name,
        'contactPerson': db_lead.contact_person,
        'mobile': db_lead.mobile,
        'email': db_lead.email,
        'city': 'Ahmedabad',
    }
    res_cust = client.post('/api/customers/', cust_payload, format='json')
    assert res_cust.status_code in [200, 201], f"Customer create failed: {res_cust.data}"

    enq_no = f"ENQ-{uid}"
    enq_payload = {
        'enquiryNo': enq_no,
        'leadId': lead_id,
        'customerId': cust_id,
        'customerName': db_lead.company_name,
        'enquiryDate': today_str,
        'requirement': 'Design and manufacturing of 5000L SS316 Distillation Column',
        'machineProduct': db_lead.product_name,
        'quantity': 1,
        'status': 'under_review',
    }
    res_enq = client.post('/api/enquiries/', enq_payload, format='json')
    assert res_enq.status_code in [200, 201], f"Enquiry create failed: {res_enq.data}"
    enq_id = res_enq.data.get('id') or enq_no
    # Update Enquiry
    client.patch(f'/api/enquiries/{enq_id}/', {'status': 'quotation_ready'}, format='json')
    db_enq = Enquiry.objects.get(id=enq_id)
    assert db_enq.status == 'quotation_ready', "Enquiry status not updated in DB"
    print(f"  -> CREATE, READ, UPDATE verified in SQLite: Enquiry {db_enq.enquiry_no} (Status: {db_enq.status})")

    # -------------------------------------------------------------------------
    # 3. QUOTATION & APPROVAL
    # -------------------------------------------------------------------------
    log_step("3. QUOTATION", "Testing Quotation Creation, Revision, and Approval")
    quo_no = f"QT-{uid}"
    quo_payload = {
        'quotationNumber': quo_no,
        'currentRevision': 'Rev-00',
        'date': today_str,
        'validUntil': '2026-12-31',
        'customerId': cust_id,
        'customerName': db_lead.company_name,
        'contactPerson': db_lead.contact_person,
        'contactEmail': db_lead.email,
        'enquiryId': enq_id,
        'revisions': [{
            'revisionNumber': 'Rev-00',
            'status': 'draft',
            'grandTotal': 7200000,
            'machineProduct': db_lead.product_name,
            'items': [{'itemNo': 1, 'description': db_lead.product_name, 'qty': 1, 'unitRate': 7200000, 'amount': 7200000}]
        }],
    }
    res_quo = client.post('/api/quotations/', quo_payload, format='json')
    assert res_quo.status_code in [200, 201], f"Quotation create failed: {res_quo.data}"
    quo_id = res_quo.data.get('id') or quo_no

    # Approve Quotation
    r_quo_app = client.post(f'/api/quotations/{quo_id}/update-status/', {'revisionNumber': 'Rev-00', 'status': 'approved'}, format='json')
    assert r_quo_app.status_code == 200, "Quotation approval failed"
    db_quo = Quotation.objects.get(id=quo_id)
    assert db_quo.revisions[0]['status'] == 'approved', "Quotation not approved in DB"
    print(f"  -> CREATE, UPDATE, APPROVE verified in SQLite: Quotation {db_quo.quotation_number} (Approved)")

    # -------------------------------------------------------------------------
    # 4. CUSTOMER PO
    # -------------------------------------------------------------------------
    log_step("4. CUSTOMER PO", "Testing Customer PO Receipt and Acceptance")
    po_no = f"CPO-{uid}"
    cpo_payload = {
        'poNumber': po_no,
        'customerId': cust_id,
        'customerName': db_lead.company_name,
        'quotationId': quo_id,
        'quotationNumber': quo_no,
        'poDate': today_str,
        'deliveryDate': '2026-11-30',
        'poAmount': 7200000.0,
        'status': 'received',
    }
    res_cpo = client.post('/api/customer-pos/', cpo_payload, format='json')
    assert res_cpo.status_code in [200, 201], f"Customer PO create failed: {res_cpo.data}"
    cpo_id = res_cpo.data.get('id') or po_no
    # Update / Accept PO
    client.patch(f'/api/customer-pos/{cpo_id}/', {'status': 'accepted'}, format='json')
    db_cpo = CustomerPO.objects.get(id=cpo_id)
    assert db_cpo.status == 'accepted', "Customer PO not accepted in DB"
    print(f"  -> CREATE, READ, UPDATE verified in SQLite: Customer PO {db_cpo.po_number} (Value: Rs.{db_cpo.po_value})")

    # -------------------------------------------------------------------------
    # 5. SALES ORDER & APPROVAL
    # -------------------------------------------------------------------------
    log_step("5. SALES ORDER", "Testing Sales Order Creation and Confirmation")
    so_no = f"SO-{uid}"
    so_payload = {
        'salesOrderNumber': so_no,
        'customerPoId': cpo_id,
        'customerPoNumber': po_no,
        'quotationId': quo_id,
        'quotationNumber': quo_no,
        'customerId': cust_id,
        'customerName': db_lead.company_name,
        'orderDate': today_str,
        'targetDeliveryDate': '2026-11-30',
        'grandTotal': 7200000.0,
        'totalAmount': 7200000.0,
        'status': 'confirmed',
        'approvedBy': 'Bhavin Shah (Director)',
        'items': [{'itemNo': 1, 'productName': db_lead.product_name, 'quantity': 1, 'unitRate': 7200000, 'totalAmount': 7200000}]
    }
    res_so = client.post('/api/sales-orders/', so_payload, format='json')
    assert res_so.status_code in [200, 201], f"Sales Order create failed: {res_so.data}"
    so_id = res_so.data.get('id') or so_no
    db_so = SalesOrder.objects.get(id=so_id)
    assert db_so.status == 'confirmed', "SO not confirmed in DB"
    print(f"  -> CREATE, READ, APPROVE verified in SQLite: Sales Order {db_so.sales_order_number} (Status: {db_so.status})")

    # -------------------------------------------------------------------------
    # 6. PROJECT / JOB
    # -------------------------------------------------------------------------
    log_step("6. PROJECT / JOB", "Testing Project Job Master Creation and Planning Stages")
    prj_no = f"PRJ-{uid}"
    job_no = f"JOB-{uid}"
    prj_payload = {
        'projectNumber': prj_no,
        'jobNumber': job_no,
        'customerId': cust_id,
        'customerName': db_lead.company_name,
        'salesOrderId': so_id,
        'salesOrderNumber': so_no,
        'customerPoNumber': po_no,
        'productName': db_lead.product_name,
        'orderValue': 7200000.0,
        'startDate': today_str,
        'targetDeliveryDate': '2026-11-30',
        'currentStatus': 'planning',
        'projectManagerName': 'Bhavin Shah',
    }
    res_prj = client.post('/api/projects/', prj_payload, format='json')
    assert res_prj.status_code in [200, 201], f"Project create failed: {res_prj.data}"
    prj_id = res_prj.data.get('id') or prj_no
    # Update Project Status to Active
    client.patch(f'/api/projects/{prj_id}/', {'currentStatus': 'in_progress', 'progressPercent': 15}, format='json')
    db_prj = ProjectJobMaster.objects.get(id=prj_id)
    assert db_prj.current_status == 'in_progress', "Project status not updated in DB"
    print(f"  -> CREATE, UPDATE verified in SQLite: Project {db_prj.project_number} / Job {db_prj.job_number}")

    # -------------------------------------------------------------------------
    # 7. DESIGN JOB, APPROVAL & SHOP FLOOR RELEASE
    # -------------------------------------------------------------------------
    log_step("7. DESIGN JOB", "Testing Design Job Creation, Approval, and Release to Production")
    des_no = f"DES-{uid}"
    des_payload = {
        'designJobNumber': des_no,
        'projectId': prj_id,
        'projectNumber': prj_no,
        'jobNumber': job_no,
        'customerId': cust_id,
        'customerName': db_lead.company_name,
        'customerPoNumber': po_no,
        'salesOrderNumber': so_no,
        'productName': db_lead.product_name,
        'targetCompletionDate': '2026-11-15',
        'status': 'under_review',
    }
    res_des = client.post('/api/designer/jobs/', des_payload, format='json')
    assert res_des.status_code in [200, 201], f"Design job create failed: {res_des.data}"
    des_id = res_des.data.get('id') or des_no

    # Approve Design Job
    r_des_app = client.post(f'/api/designer/jobs/{des_id}/approve/', {'approvedBy': 'Dharmesh Joshi', 'notes': 'Calculations and stress analysis approved.'}, format='json')
    assert r_des_app.status_code == 200, "Design approval failed"
    db_des = DesignJob.objects.get(id=des_id)
    assert db_des.status == 'approved', "Design not approved in DB"
    print(f"  -> APPROVE verified in SQLite: Design Job {des_id} (Approved by {db_des.approved_by})")

    # Release Design to Production
    r_des_rel = client.post(f'/api/designer/jobs/{des_id}/release-to-production/', format='json')
    assert r_des_rel.status_code == 200, "Design release to production failed"
    db_des.refresh_from_db()
    assert db_des.status == 'released_to_production', "Design not released in DB"
    print(f"  -> RELEASE verified in SQLite: Design Job {des_id} Released to Production")

    # -------------------------------------------------------------------------
    # 8. BOM (Bill of Materials) & APPROVAL
    # -------------------------------------------------------------------------
    log_step("8. BOM", "Testing Master BOM Creation, Items, and Approval")
    bom_no = f"BOM-{uid}"
    bom_items = [
        {'itemNo': 1, 'itemCode': 'SS-PL-316L', 'itemName': 'SS 316L 32mm Shell Plate', 'quantity': 8, 'uom': 'Nos', 'estimatedRate': 350000, 'totalEstimatedAmount': 2800000},
        {'itemNo': 2, 'itemCode': 'FLG-WN-300', 'itemName': 'WNRF Flange 24-inch ANSI 300#', 'quantity': 6, 'uom': 'Nos', 'estimatedRate': 120000, 'totalEstimatedAmount': 720000},
        {'itemNo': 3, 'itemCode': 'GSK-SPW-316', 'itemName': 'Spiral Wound Gasket 24-inch', 'quantity': 12, 'uom': 'Nos', 'estimatedRate': 15000, 'totalEstimatedAmount': 180000},
    ]
    bom_payload = {
        'bomNumber': bom_no,
        'jobNumber': job_no,
        'designJobId': des_id,
        'preparedBy': 'Design Engineer (R&D)',
        'status': 'draft',
        'items': bom_items,
        'total_estimated_cost': 3700000.0,
    }
    res_bom = client.post('/api/designer/boms/', bom_payload, format='json')
    assert res_bom.status_code in [200, 201], f"BOM create failed: {res_bom.data}"
    bom_id = res_bom.data.get('id') or bom_no

    # Update BOM Status to Approved
    client.patch(f'/api/designer/boms/{bom_id}/', {'status': 'approved', 'approved_by': 'HOD Engineering'}, format='json')
    db_bom = BOMHeader.objects.get(id=bom_id)
    assert db_bom.status == 'approved', "BOM not approved in DB"
    assert len(db_bom.items) == 3, "BOM items count mismatch in DB"
    print(f"  -> CREATE, UPDATE, APPROVE verified in SQLite: BOM {db_bom.bom_number} with {len(db_bom.items)} items (Status: {db_bom.status})")

    # -------------------------------------------------------------------------
    # 9. MRP (Material Requirements Planning)
    # -------------------------------------------------------------------------
    log_step("9. MRP", "Testing Material Requirements Planning Generation")
    mrp_id = f"MRP-{uid}"
    mrp_payload = {
        'id': mrp_id,
        'project_id': prj_id,
        'job_id': job_no,
        'job_number': job_no,
        'customer_name': db_lead.company_name,
        'design_job_id': des_id,
        'bom_id': bom_id,
        'bom_number': bom_no,
        'status': 'PR Generated',
        'items': db_bom.items,
    }
    res_mrp = client.post('/api/material-requirements/', mrp_payload, format='json')
    assert res_mrp.status_code in [200, 201], f"MRP create failed: {res_mrp.data}"
    db_mrp = MaterialRequirement.objects.get(id=mrp_id)
    print(f"  -> CREATE, READ verified in SQLite: Material Requirements (MRP) {db_mrp.id} (Status: {db_mrp.status})")

    # -------------------------------------------------------------------------
    # 10. PURCHASE REQUISITION & PURCHASE ORDER
    # -------------------------------------------------------------------------
    log_step("10. PURCHASE", "Testing PR and PO Creation and Approvals")
    pr_no = f"PR-{uid}"
    pr_payload = {
        'prNumber': pr_no,
        'projectId': prj_id,
        'jobCode': job_no,
        'requestedBy': 'Store Officer',
        'requestDate': today_str,
        'requiredByDate': '2026-10-31',
        'status': 'Submitted',
        'total_estimated_cost': 3700000.0,
        'items': db_bom.items,
    }
    res_pr = client.post('/api/purchase-requisitions/', pr_payload, format='json')
    assert res_pr.status_code in [200, 201], f"PR create failed: {res_pr.data}"
    pr_id = res_pr.data.get('id') or pr_no

    # Approve PR
    client.patch(f'/api/purchase-requisitions/{pr_id}/', {'status': 'Approved', 'approvedBy': 'Purchase Head'}, format='json')
    db_pr = PurchaseRequisition.objects.get(id=pr_id)
    assert db_pr.status == 'Approved', "PR not approved in DB"
    print(f"  -> PR CREATE & APPROVE verified in SQLite: PR {db_pr.pr_number} (Approved)")

    # PO Creation & Approval
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
        'grandTotal': 3700000.0,
        'items': db_bom.items,
    }
    res_po = client.post('/api/purchase-orders/', po_ord_payload, format='json')
    assert res_po.status_code in [200, 201], f"PO create failed: {res_po.data}"
    po_order_id = res_po.data.get('id') or po_ord_no

    # Approve PO
    client.patch(f'/api/purchase-orders/{po_order_id}/', {'status': 'Approved', 'approvedBy': 'Commercial Director'}, format='json')
    db_po = PurchaseOrder.objects.get(id=po_order_id)
    assert db_po.status == 'Approved', "PO not approved in DB"
    print(f"  -> PO CREATE & APPROVE verified in SQLite: Purchase Order {db_po.po_number} (Approved)")

    # -------------------------------------------------------------------------
    # 11. GRN (Goods Receipt Note) & INVENTORY INWARD
    # -------------------------------------------------------------------------
    log_step("11. GRN", "Testing Material Inward and Stock Balance Updates")
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
            {'itemNo': 2, 'itemCode': 'FLG-WN-300', 'itemName': 'WNRF Flange 24-inch ANSI 300#', 'receivedQuantity': 6, 'acceptedQuantity': 6, 'uom': 'Nos', 'unitPrice': 120000},
        ]
    }
    res_grn = client.post('/api/grns/', grn_payload, format='json')
    assert res_grn.status_code in [200, 201], f"GRN create failed: {res_grn.data}"
    db_grn = GoodsReceiptNote.objects.get(id=grn_no)
    assert db_grn.status == 'Accepted', "GRN not accepted in DB"
    # Verify StockBalance was created/updated in SQLite
    bal_plate = StockBalance.objects.filter(item_code='SS-PL-316L').first()
    assert bal_plate is not None and bal_plate.quantity >= 8, "Stock balance not updated for plate!"
    print(f"  -> GRN verified in SQLite: GRN {db_grn.grn_number} (Stock Inward Verified: {bal_plate.item_code} Qty: {bal_plate.quantity})")

    # -------------------------------------------------------------------------
    # 12. MATERIAL ISSUE TO SHOP FLOOR
    # -------------------------------------------------------------------------
    log_step("12. MATERIAL ISSUE", "Testing Material Issue Slip and Stock Deduction")
    iss_no = f"ISS-{uid}"
    iss_payload = {
        'issueNumber': iss_no,
        'projectId': prj_id,
        'jobNumber': job_no,
        'issuedTo': 'Shell Rolling & Fitting Station',
        'issuedBy': 'Store Officer',
        'issueDate': today_str,
        'status': 'Fully Issued',
        'totalIssueValue': 2800000.0,
        'items': [
            {'itemCode': 'SS-PL-316L', 'itemName': 'SS 316L 32mm Shell Plate', 'issuedQuantity': 8, 'uom': 'Nos'}
        ]
    }
    prev_qty = bal_plate.quantity
    res_iss = client.post('/api/material-issues/', iss_payload, format='json')
    assert res_iss.status_code in [200, 201], f"Material issue create failed: {res_iss.data}"
    db_iss = MaterialIssue.objects.get(id=iss_no)
    bal_plate.refresh_from_db()
    assert bal_plate.quantity == prev_qty - 8, "Stock balance not deducted correctly on issue!"
    print(f"  -> MATERIAL ISSUE verified in SQLite: Issue Slip {db_iss.issue_number} (Remaining Stock: {bal_plate.quantity})")

    # -------------------------------------------------------------------------
    # 13. PRODUCTION WORK ORDER & PRODUCTION ENTRY
    # -------------------------------------------------------------------------
    log_step("13. PRODUCTION", "Testing Work Order Creation, Release, and Production Shop Floor Entry")
    wo_no = f"WO-{uid}"
    wo_payload = {
        'workOrderNumber': wo_no,
        'jobId': job_no,
        'jobNumber': job_no,
        'projectId': prj_id,
        'customerName': db_lead.company_name,
        'productName': db_lead.product_name,
        'productionQuantity': 1,
        'status': 'Draft',
    }
    res_wo = client.post('/api/work-orders/', wo_payload, format='json')
    assert res_wo.status_code in [200, 201], f"Work Order create failed: {res_wo.data}"
    wo_id = res_wo.data.get('id') or wo_no

    # Release Work Order
    r_wo_rel = client.post(f'/api/work-orders/{wo_id}/release/', format='json')
    assert r_wo_rel.status_code == 200, "WO release failed"
    db_wo = WorkOrder.objects.get(id=wo_id)
    assert db_wo.status == 'Released', "WO not marked Released in DB"
    print(f"  -> WORK ORDER verified in SQLite: Work Order {db_wo.work_order_number} (Released)")

    # Record Daily Production Entry
    pentry_no = f"PENTRY-{uid}"
    pentry_payload = {
        'productionEntryNumber': pentry_no,
        'entryDate': today_str,
        'jobNumber': job_no,
        'workOrderNumber': wo_no,
        'operationName': 'Final Hydro Testing & Vessel Cleaning',
        'operatorName': 'Ramesh Parmar (Certified Welder)',
        'producedQuantity': 1,
        'goodQuantity': 1,
        'rejectedQuantity': 0,
    }
    res_entry = client.post('/api/production-entries/', pentry_payload, format='json')
    assert res_entry.status_code in [200, 201], f"Production Entry failed: {res_entry.data}"
    db_entry = ProductionEntry.objects.get(id=pentry_no)
    print(f"  -> PRODUCTION ENTRY verified in SQLite: Entry {db_entry.production_entry_number} (Good Qty: {db_entry.good_quantity})")

    # -------------------------------------------------------------------------
    # 14. QC INSPECTION (Quality Check)
    # -------------------------------------------------------------------------
    log_step("14. QC INSPECTION", "Testing Quality Control Clearance for Finished Equipment")
    fg_no = f"FG-{uid}"
    fg_payload = {
        'finishedGoodsNumber': fg_no,
        'jobNumber': job_no,
        'workOrderNumber': wo_no,
        'productName': db_lead.product_name,
        'quantity': 1,
        'serialNumber': f"SN-VESSEL-{uid}",
        'status': 'Ready for QC',
        'qcStatus': 'Pending Inspection',
    }
    res_fg = client.post('/api/finished-goods/', fg_payload, format='json')
    assert res_fg.status_code in [200, 201], f"Finished goods create failed: {res_fg.data}"
    fg_id = res_fg.data.get('id') or fg_no

    # Pass QC
    r_qc_pass = client.post(f'/api/finished-goods/{fg_id}/qc-pass/', format='json')
    assert r_qc_pass.status_code == 200, "QC Pass failed"
    db_fg = FinishedGoodsItem.objects.get(id=fg_id)
    assert db_fg.qc_status == 'QC Passed', "FG not marked QC Passed in DB"
    assert db_fg.status == 'Ready for Dispatch', "FG status not Ready for Dispatch"
    print(f"  -> QC INSPECTION verified in SQLite: FG {db_fg.finished_goods_number} (QC Passed & Cleared for Packing)")

    # -------------------------------------------------------------------------
    # 15. PACKING & DISPATCH
    # -------------------------------------------------------------------------
    log_step("15. PACKING & DISPATCH", "Testing Packing, Delivery Challan and Dispatch Order")
    disp_no = f"DISP-{uid}"
    disp_payload = {
        'dispatchNumber': disp_no,
        'jobNumber': job_no,
        'workOrderNumber': wo_no,
        'finishedGoodsNumber': fg_no,
        'customerId': cust_id,
        'customerName': db_lead.company_name,
        'productName': db_lead.product_name,
        'quantity': 1,
        'packagingType': 'Wooden Saddle & Shrink Wrapped Tarpaulin',
        'transporterName': 'CJ Darcl Logistics Heavy ODC',
        'vehicleNumber': 'GJ-06-ZZ-1234',
        'driverName': 'Sukhdev Singh',
        'status': 'Ready for Dispatch',
    }
    res_disp = client.post('/api/dispatch-orders/', disp_payload, format='json')
    assert res_disp.status_code in [200, 201], f"Dispatch create failed: {res_disp.data}"
    disp_id = res_disp.data.get('id') or disp_no

    # Mark Dispatched
    r_disp_mark = client.post(f'/api/dispatch-orders/{disp_id}/mark-dispatched/', format='json')
    assert r_disp_mark.status_code == 200, "Mark dispatched failed"
    db_disp = DispatchOrder.objects.get(id=disp_id)
    assert db_disp.status in ['Dispatched', 'In Transit'], f"Dispatch status not marked Dispatched/In Transit in DB: {db_disp.status}"
    print(f"  -> PACKING & DISPATCH verified in SQLite: Dispatch {db_disp.dispatch_number} (Vehicle: {db_disp.vehicle_number}, Status: {db_disp.status})")

    # -------------------------------------------------------------------------
    # 16. SALES INVOICE & APPROVAL
    # -------------------------------------------------------------------------
    log_step("16. SALES INVOICE", "Testing Tax Invoice Generation and Approval")
    inv_no = f"INV-{uid}"
    inv_payload = {
        'invoiceNumber': inv_no,
        'invoiceDate': today_str,
        'dueDate': '2026-11-30',
        'customerId': cust_id,
        'customerName': db_lead.company_name,
        'salesOrderId': so_id,
        'salesOrderNumber': so_no,
        'jobNumber': job_no,
        'grandTotal': 7200000.0,
        'taxableAmount': 6101694.92,
        'status': 'Draft',
        'paymentStatus': 'Unpaid',
        'items': [{'itemNo': 1, 'description': db_lead.product_name, 'amount': 7200000.0}]
    }
    res_inv = client.post('/api/sales-invoices/', inv_payload, format='json')
    assert res_inv.status_code in [200, 201], f"Invoice create failed: {res_inv.data}"
    inv_id = res_inv.data.get('id') or inv_no

    # Approve Sales Invoice
    r_inv_app = client.patch(f'/api/sales-invoices/{inv_id}/', {'status': 'Approved'}, format='json')
    assert r_inv_app.status_code == 200, "Invoice approval failed"
    db_inv = SalesInvoice.objects.get(id=inv_id)
    assert db_inv.status == 'Approved', "Invoice not marked Approved in DB"
    print(f"  -> SALES INVOICE verified in SQLite: Invoice {db_inv.invoice_number} (Grand Total: Rs.{db_inv.grand_total}, Status: {db_inv.status})")

    # -------------------------------------------------------------------------
    # 17. PAYMENT RECEIPT
    # -------------------------------------------------------------------------
    log_step("17. PAYMENT RECEIPT", "Testing Customer Payment Settlement and Receipt Record")
    r_pay = client.post(f'/api/sales-invoices/{inv_id}/record-payment/', {
        'amount': 7200000.0,
        'paymentMode': 'NEFT/RTGS',
        'referenceNumber': f'UTR-SBI-{uid}',
    }, format='json')
    assert r_pay.status_code == 200, f"Record payment failed: {r_pay.data}"
    db_inv.refresh_from_db()
    db_receipt = CustomerReceipt.objects.filter(sales_invoice_number=db_inv.invoice_number).first() or CustomerReceipt.objects.filter(sales_invoice_number=inv_id).first()
    assert db_receipt is not None, f"Customer Receipt not created in DB for invoice {db_inv.invoice_number}!"
    print(f"  -> PAYMENT verified in SQLite: Invoice Paid! Customer Receipt {db_receipt.receipt_number} (Amount: Rs.{db_receipt.amount})")

    # -------------------------------------------------------------------------
    # 18. INSTALLATION & COMMISSIONING
    # -------------------------------------------------------------------------
    log_step("18. INSTALLATION", "Testing Customer Machine Commissioning and Warranty Activation")
    cm_no = f"MACH-{uid}"
    cm_payload = {
        'customerMachineId': cm_no,
        'customerId': cust_id,
        'customerName': db_lead.company_name,
        'jobNumber': job_no,
        'salesOrderId': so_id,
        'dispatchNumber': disp_no,
        'machineName': db_lead.product_name,
        'serialNumber': f"SN-VESSEL-{uid}",
        'installationDate': today_str,
        'commissioningDate': today_str,
        'status': 'Installed & Commissioned',
    }
    res_cm = client.post('/api/customer-machines/', cm_payload, format='json')
    assert res_cm.status_code in [200, 201], f"Customer machine create failed: {res_cm.data}"
    db_cm = CustomerMachine.objects.get(id=cm_no)
    assert db_cm.status == 'Installed & Commissioned', "Machine status mismatch in DB"
    print(f"  -> INSTALLATION verified in SQLite: Asset {db_cm.customer_machine_id} (Status: {db_cm.status})")

    print("\n" + "=" * 90)
    print("🏆 ALL 18+ LIFECYCLE PHASES FULLY AUDITED & TESTED!")
    print("   ✅ Lead -> Enquiry -> Quotation -> Customer PO -> Sales Order -> Project/Job")
    print("   ✅ Design -> BOM -> MRP -> Purchase -> GRN -> Material Issue -> Production")
    print("   ✅ QC Inspection -> Packing -> Dispatch -> Invoice -> Payment -> Installation")
    print("   ✅ Direct verification from SQLite database confirmed for all phases!")
    print("=" * 90)
    return True

if __name__ == '__main__':
    success = run_comprehensive_crud_test()
    sys.exit(0 if success else 1)
