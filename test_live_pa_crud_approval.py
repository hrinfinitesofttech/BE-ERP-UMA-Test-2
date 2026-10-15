"""
UMA ERP - LIVE PYTHONANYWHERE CRUD & APPROVAL API VERIFICATION
Tests Create, Read, Update, Delete & Approvals against https://umaERP.pythonanywhere.com/api
"""

import requests
import json
import time
from datetime import date

BASE_URL = "https://umaERP.pythonanywhere.com/api"
RUN_ID = str(int(time.time()))
today_str = date.today().isoformat()

session = requests.Session()
session.headers.update({
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

passed = 0
failed = 0
errors = []

def record(ok, msg):
    global passed, failed
    if ok:
        passed += 1
        print(f"  [PASS] {msg}")
    else:
        failed += 1
        errors.append(msg)
        print(f"  [FAIL] {msg}")

def login():
    res = session.post(f"{BASE_URL}/auth/login/", json={
        "username": "rajesh.admin",
        "password": "admin123"
    }, timeout=15)
    if res.status_code != 200:
        raise Exception(f"Login failed: {res.status_code} - {res.text}")
    data = res.json()
    token = data.get('access') or data.get('tokens', {}).get('access') or data.get('token')
    session.headers.update({'Authorization': f"Bearer {token}"})
    print("[OK] Authenticated on Live PythonAnywhere via JWT Token.")

def test_live():
    print("\n" + "=" * 80)
    print("TESTING LIVE PYTHONANYWHERE: FULL CRUD & APPROVALS / DISAPPROVALS")
    print("=" * 80)

    # 1. LEAD: CREATE, READ, UPDATE, DELETE
    print("\n[1. LEAD CRUD on Live PA]")
    lead_no = f"LEAD-LIVE-{RUN_ID}"
    r_lead = session.post(f"{BASE_URL}/leads/", json={
        'leadNo': lead_no,
        'companyName': f'Live Test Industries {RUN_ID}',
        'contactPerson': 'Deepak Patel',
        'mobile': '9898001122',
        'email': f'deepak_{RUN_ID}@livetest.com',
        'productName': 'SS316 Heat Exchanger 2000L',
        'status': 'new',
        'priority': 'high',
        'createdDate': today_str,
    }, timeout=15)
    record(r_lead.status_code in [200, 201], f"Lead CREATE: {r_lead.status_code}")
    lead_id = r_lead.json().get('id') or lead_no

    r_lead_get = session.get(f"{BASE_URL}/leads/{lead_id}/", timeout=15)
    record(r_lead_get.status_code == 200, f"Lead READ: {r_lead_get.status_code}")

    r_lead_patch = session.patch(f"{BASE_URL}/leads/{lead_id}/", json={'status': 'qualified', 'budget': 6500000}, timeout=15)
    record(r_lead_patch.status_code == 200 and r_lead_patch.json().get('status') == 'qualified', "Lead UPDATE (status: qualified)")

    r_lead_del = session.delete(f"{BASE_URL}/leads/{lead_id}/", timeout=15)
    record(r_lead_del.status_code in [200, 204], f"Lead DELETE: {r_lead_del.status_code}")
    r_lead_del_check = session.get(f"{BASE_URL}/leads/{lead_id}/", timeout=15)
    record(r_lead_del_check.status_code == 404, "Lead Verified Deleted (GET returns 404)")

    # 2. CUSTOMER & QUOTATION APPROVAL & REJECTION
    print("\n[2. QUOTATION APPROVAL & REJECTION on Live PA]")
    cust_id = f"CUST-LIVE-{RUN_ID}"
    r_cust = session.post(f"{BASE_URL}/customers/", json={
        'id': cust_id,
        'customerCode': cust_id,
        'companyName': f'Live Customer {RUN_ID}',
        'contactPerson': 'Deepak Patel',
        'mobile': '9898001122',
        'email': f'deepak_{RUN_ID}@livetest.com',
        'city': 'Surat',
    }, timeout=15)
    record(r_cust.status_code in [200, 201], f"Customer CREATE: {r_cust.status_code}")

    quo_no1 = f"QT-APP-{RUN_ID}"
    r_q1 = session.post(f"{BASE_URL}/quotations/", json={
        'quotationNumber': quo_no1,
        'currentRevision': 'Rev-00',
        'date': today_str,
        'validUntil': '2026-12-31',
        'customerId': cust_id,
        'customerName': f'Live Customer {RUN_ID}',
        'revisions': [{'revisionNumber': 'Rev-00', 'status': 'draft', 'grandTotal': 5000000, 'items': []}],
    }, timeout=15)
    record(r_q1.status_code in [200, 201], f"Quotation 1 CREATE: {r_q1.status_code}")
    q1_id = r_q1.json().get('id') or quo_no1

    # Approve Quotation 1
    r_q1_app = session.post(f"{BASE_URL}/quotations/{q1_id}/update-status/", json={'revisionNumber': 'Rev-00', 'status': 'approved'}, timeout=15)
    record(r_q1_app.status_code == 200, "Quotation 1 APPROVE: Status 200")

    # Reject Quotation 2
    quo_no2 = f"QT-REJ-{RUN_ID}"
    r_q2 = session.post(f"{BASE_URL}/quotations/", json={
        'quotationNumber': quo_no2,
        'currentRevision': 'Rev-00',
        'date': today_str,
        'validUntil': '2026-12-31',
        'customerId': cust_id,
        'customerName': f'Live Customer {RUN_ID}',
        'revisions': [{'revisionNumber': 'Rev-00', 'status': 'draft', 'grandTotal': 5000000, 'items': []}],
    }, timeout=15)
    q2_id = r_q2.json().get('id') or quo_no2
    r_q2_rej = session.post(f"{BASE_URL}/quotations/{q2_id}/update-status/", json={'revisionNumber': 'Rev-00', 'status': 'rejected', 'reason': 'Budget constraint'}, timeout=15)
    record(r_q2_rej.status_code == 200, "Quotation 2 REJECT/DISAPPROVE: Status 200")

    # Delete Quotation 2
    r_q2_del = session.delete(f"{BASE_URL}/quotations/{q2_id}/", timeout=15)
    record(r_q2_del.status_code in [200, 204], f"Quotation 2 DELETE: {r_q2_del.status_code}")

    # 3. PURCHASE ORDER APPROVAL & REJECTION
    print("\n[3. PURCHASE ORDER WORKFLOW on Live PA]")
    po_no1 = f"PO-APP-{RUN_ID}"
    r_po1 = session.post(f"{BASE_URL}/purchase-orders/", json={
        'poNumber': po_no1,
        'supplierId': 'SUP-001',
        'supplierName': 'Jindal Steel',
        'date': today_str,
        'deliveryDate': '2026-11-15',
        'status': 'Draft',
        'grandTotal': 1500000.0,
        'items': [{'itemNo': 1, 'itemCode': 'SS-316', 'itemName': 'SS 316 Sheet', 'quantity': 10, 'uom': 'Nos', 'estimatedRate': 150000, 'totalEstimatedAmount': 1500000}],
    }, timeout=15)
    record(r_po1.status_code in [200, 201], f"PO 1 CREATE: {r_po1.status_code}")
    po1_id = r_po1.json().get('id') or po_no1

    r_po1_app = session.patch(f"{BASE_URL}/purchase-orders/{po1_id}/", json={'status': 'Approved', 'approvedBy': 'Commercial Head'}, timeout=15)
    record(r_po1_app.status_code == 200 and r_po1_app.json().get('status') == 'Approved', "PO 1 APPROVE (Status: Approved)")

    po_no2 = f"PO-REJ-{RUN_ID}"
    r_po2 = session.post(f"{BASE_URL}/purchase-orders/", json={
        'poNumber': po_no2,
        'supplierId': 'SUP-001',
        'supplierName': 'Jindal Steel',
        'date': today_str,
        'deliveryDate': '2026-11-15',
        'status': 'Draft',
        'grandTotal': 1500000.0,
        'items': [],
    }, timeout=15)
    po2_id = r_po2.json().get('id') or po_no2

    r_po2_rej = session.post(f"{BASE_URL}/purchase-orders/{po2_id}/reject/", json={'reason': 'Vendor payment term not standard'}, timeout=15)
    if r_po2_rej.status_code != 200:
        r_po2_rej = session.patch(f"{BASE_URL}/purchase-orders/{po2_id}/", json={'status': 'Rejected', 'rejectionReason': 'Vendor payment term'}, timeout=15)
    po_rej_ok = r_po2_rej.status_code == 200 and (r_po2_rej.json().get('status') in ['Rejected', 'rejected'] or 'Rejected' in r_po2_rej.text)
    record(po_rej_ok, f"PO 2 REJECT (Status: Rejected, HTTP {r_po2_rej.status_code})")

    r_po2_del = session.delete(f"{BASE_URL}/purchase-orders/{po2_id}/", timeout=15)
    record(r_po2_del.status_code in [200, 204], f"PO 2 DELETE: {r_po2_del.status_code}")

    # 4. ITEM MASTER CRUD
    print("\n[4. ITEM MASTER CRUD on Live PA]")
    item_code = f"ITM-{RUN_ID}"
    r_it = session.post(f"{BASE_URL}/items/", json={
        'itemCode': item_code,
        'itemName': f'Precision Bearing {RUN_ID}',
        'category': 'Consumables',
        'uom': 'Nos',
        'unitCost': 8500,
        'currentStock': 50,
    }, timeout=15)
    record(r_it.status_code in [200, 201], f"Item CREATE: {r_it.status_code}")
    it_id = r_it.json().get('id') or item_code

    r_it_del = session.delete(f"{BASE_URL}/items/{it_id}/", timeout=15)
    record(r_it_del.status_code in [200, 204], f"Item DELETE: {r_it_del.status_code}")

    # 5. CENTRAL APPROVALS INBOX
    print("\n[5. CENTRAL APPROVALS INBOX on Live PA]")
    app_id = f"APP-LIVE-{RUN_ID}"
    r_app = session.post(f"{BASE_URL}/approvals/", json={
        'id': app_id,
        'category': 'Purchase Order',
        'title': f'Live PO Approval {po_no1}',
        'record_number': po_no1,
        'requester_name': 'Hitesh Rawal',
        'status': 'Pending',
        'amount': 1500000.0,
    }, timeout=15)
    record(r_app.status_code in [200, 201], f"Central Approval CREATE: {r_app.status_code}")

    r_app_ok = session.post(f"{BASE_URL}/approvals/{app_id}/approve/", timeout=15)
    record(r_app_ok.status_code == 200 and r_app_ok.json().get('status') == 'Approved', "Central Approval APPROVE: Status Approved")

    app_id2 = f"APP-REJ-LIVE-{RUN_ID}"
    session.post(f"{BASE_URL}/approvals/", json={
        'id': app_id2,
        'category': 'Leave',
        'title': 'Emergency Leave',
        'record_number': 'LV-999',
        'requester_name': 'Rajesh Patel',
        'status': 'Pending',
    }, timeout=15)
    r_app_rej = session.post(f"{BASE_URL}/approvals/{app_id2}/reject/", timeout=15)
    record(r_app_rej.status_code == 200 and r_app_rej.json().get('status') == 'Rejected', "Central Approval REJECT: Status Rejected")

    r_app_del = session.delete(f"{BASE_URL}/approvals/{app_id2}/", timeout=15)
    record(r_app_del.status_code in [200, 204], f"Central Approval DELETE: {r_app_del.status_code}")

    # FINAL
    print("\n" + "=" * 80)
    print(f"LIVE PYTHONANYWHERE RESULTS: {passed} Passed, {failed} Failed")
    if errors:
        for e in errors:
            print(f"  - {e}")
    print("=" * 80)
    return failed == 0

if __name__ == '__main__':
    login()
    test_live()
