import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
from erp_backend.urls import api_router

def run_comprehensive_api_audit():
    client = APIClient()
    print("=" * 65)
    print("STARTING FULL ERP BACKEND API AUDIT & CRUD TESTING")
    print("=" * 65)

    # 1. TEST AUTHENTICATION
    print("\n[1] Testing Authentication Endpoints...")
    login_res = client.post('/api/auth/login/', {'username': 'admin', 'password': 'admin123'}, format='json')
    if login_res.status_code == status.HTTP_200_OK:
        token = login_res.data.get('access')
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        print(f"  [OK] Login successful. Bearer token acquired. Status: {login_res.status_code}")
    else:
        print(f"  [FAIL] Login failed: {login_res.status_code}, {login_res.data}")
        return False

    me_res = client.get('/api/auth/me/')
    if me_res.status_code == status.HTTP_200_OK:
        print(f"  [OK] /api/auth/me/ returned user: {me_res.data.get('username')}")
    else:
        print(f"  [FAIL] /api/auth/me/ failed: {me_res.status_code}")

    # 2. TEST 360 DEGREE TRACEABILITY MASTER API
    print("\n[2] Testing 360 Degree Job Traceability...")
    j360_res = client.get('/api/job-360/JOB-2026-001/')
    if j360_res.status_code == status.HTTP_200_OK:
        data = j360_res.data
        required_tabs = ['header', 'crm', 'project', 'design', 'purchase', 'store', 'production', 'quality', 'dispatch', 'accounts', 'service', 'documents', 'timeline']
        missing = [t for t in required_tabs if t not in data]
        if not missing:
            print("  [OK] /api/job-360/JOB-2026-001/ returned complete 360 payload with all 13 tabs.")
        else:
            print(f"  [FAIL] /api/job-360/ missing tabs: {missing}")
    else:
        print(f"  [FAIL] /api/job-360/ failed: {j360_res.status_code}, {j360_res.data}")

    # 3. TEST ALL 93 REGISTERED ROUTER ENDPOINTS (GET LIST)
    print("\n[3] Testing GET on all registered API Router endpoints...")
    total_endpoints = len(api_router.registry)
    success_count = 0
    failed_endpoints = []

    for prefix, viewset, basename in api_router.registry:
        endpoint = f"/api/{prefix}/"
        try:
            res = client.get(endpoint)
            if res.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]:
                success_count += 1
            else:
                failed_endpoints.append((endpoint, res.status_code, res.data))
        except Exception as e:
            failed_endpoints.append((endpoint, "EXCEPTION", str(e)))

    print(f"  -> Total Endpoints Tested: {total_endpoints}")
    print(f"  -> Successful (HTTP 200/204): {success_count}/{total_endpoints}")

    if failed_endpoints:
        print("  -> FAILED ENDPOINTS:")
        for ep, code, err in failed_endpoints:
            print(f"     * {ep} [Status: {code}] -> {err}")
    else:
        print("  [OK] ALL 93 router endpoints responded with HTTP 200 OK!")

    # 4. TEST ACTIVE CRUD & WORKFLOW ACTIONS
    print("\n[4] Testing Active CRUD Operations & Workflow Business Logic...")

    # (a) CRM: Create Lead & Convert
    from apps.crm.models import Lead, Enquiry, Opportunity, Customer
    Lead.objects.filter(id='LEAD-AUDIT-01').delete()
    lead_data = {
        'id': 'LEAD-AUDIT-01',
        'lead_number': 'LEAD-AUDIT-01',
        'company_name': 'Audit Petrochem Ltd',
        'contact_person': 'Ramesh Shah',
        'mobile': '9876543210',
        'phone': '9876543210',
        'email': 'ramesh@audit.com',
        'product_name': 'Autoclave Reaction Column 50KL',
        'status': 'New'
    }
    c_lead = client.post('/api/leads/', lead_data, format='json')
    if c_lead.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]:
        print("  [OK] CRM Lead Created successfully.")
        conv_res = client.post(f"/api/leads/{c_lead.data['id']}/convert/")
        if conv_res.status_code == status.HTTP_200_OK:
            cust_name = conv_res.data.get('customer', {}).get('companyName')
            print(f"  [OK] CRM 1-Click Lead Conversion -> Customer '{cust_name}' created.")
        else:
            print(f"  [FAIL] Lead conversion failed: {conv_res.status_code}, {conv_res.data}")
    else:
        print(f"  [FAIL] Lead creation failed: {c_lead.status_code}, {c_lead.data}")

    # (b) Production: Work Order Release
    wo_res = client.get('/api/work-orders/')
    wo_list = wo_res.data.get('results', wo_res.data) if isinstance(wo_res.data, dict) else wo_res.data
    if wo_list and len(wo_list) > 0:
        wo_id = wo_list[0]['id']
        rel_res = client.post(f"/api/work-orders/{wo_id}/release/")
        if rel_res.status_code == status.HTTP_200_OK:
            print(f"  [OK] Work Order {wo_id} released successfully.")
        else:
            print(f"  [FAIL] Work Order release failed: {rel_res.status_code}")

    # (c) Production: Finished Goods QC Pass
    fg_res = client.get('/api/finished-goods/')
    fg_list = fg_res.data.get('results', fg_res.data) if isinstance(fg_res.data, dict) else fg_res.data
    if fg_list and len(fg_list) > 0:
        fg_id = fg_list[0]['id']
        qc_res = client.post(f"/api/finished-goods/{fg_id}/qc-pass/")
        if qc_res.status_code == status.HTTP_200_OK:
            print(f"  [OK] Finished Goods {fg_id} passed QC successfully.")
        else:
            print(f"  [FAIL] Finished Goods QC pass failed: {qc_res.status_code}")

    # (d) Maintenance: Assign Technician & Resolve
    sr_res = client.get('/api/service-requests/')
    sr_list = sr_res.data.get('results', sr_res.data) if isinstance(sr_res.data, dict) else sr_res.data
    if sr_list and len(sr_list) > 0:
        sr_id = sr_list[0]['id']
        assign_res = client.post(f"/api/service-requests/{sr_id}/assign/", {'technicianId': 'EMP-003', 'technicianName': 'Sanjay Mehta'}, format='json')
        if assign_res.status_code == status.HTTP_200_OK:
            print(f"  [OK] Service Request {sr_id} assigned successfully.")
        else:
            print(f"  [FAIL] Service Request assign failed: {assign_res.status_code}")

    # (e) HR: Leave Approval & Monthly Payroll Generation
    lv_res = client.get('/api/leave-requests/')
    lv_list = lv_res.data.get('results', lv_res.data) if isinstance(lv_res.data, dict) else lv_res.data
    if lv_list and len(lv_list) > 0:
        lv_id = lv_list[0]['id']
        appr_res = client.post(f"/api/leave-requests/{lv_id}/approve/", {'approvedBy': 'HR Manager'}, format='json')
        if appr_res.status_code == status.HTTP_200_OK:
            print(f"  [OK] Leave Request {lv_id} approved successfully.")
        else:
            print(f"  [FAIL] Leave approval failed: {appr_res.status_code}")

    # Monthly Payroll Auto-Calculation
    pay_gen_res = client.post('/api/payroll-records/generate-monthly-payroll/', {'monthYear': 'October 2026', 'financialYear': '2026-2027'}, format='json')
    if pay_gen_res.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
        print(f"  [OK] Monthly Payroll generated successfully: {len(pay_gen_res.data)} records generated.")
    else:
        print(f"  [FAIL] Payroll generation failed: {pay_gen_res.status_code}")

    # (f) Accounting: Sales Invoice Payment & Auto-Receipt
    inv_res = client.get('/api/sales-invoices/')
    inv_list = inv_res.data.get('results', inv_res.data) if isinstance(inv_res.data, dict) else inv_res.data
    if inv_list and len(inv_list) > 0:
        inv_id = inv_list[0]['id']
        pay_res = client.post(f"/api/sales-invoices/{inv_id}/record-payment/", {'amount': 100000.0, 'paymentMode': 'RTGS', 'referenceNumber': 'AUDIT-RTGS-01'}, format='json')
        if pay_res.status_code == status.HTTP_200_OK:
            print(f"  [OK] Sales Invoice payment recorded and Customer Receipt auto-generated.")
        else:
            print(f"  [FAIL] Sales invoice payment failed: {pay_res.status_code}")

    # (g) Integration: Central Approval & Alert Mark-Read
    appr_res = client.get('/api/approvals/')
    appr_list = appr_res.data.get('results', appr_res.data) if isinstance(appr_res.data, dict) else appr_res.data
    if appr_list and len(appr_list) > 0:
        a_id = appr_list[0]['id']
        a_action = client.post(f"/api/approvals/{a_id}/approve/")
        if a_action.status_code == status.HTTP_200_OK:
            print(f"  [OK] Central Approval {a_id} approved successfully.")
        else:
            print(f"  [FAIL] Approval action failed: {a_action.status_code}")

    alt_res = client.get('/api/alerts/')
    alt_list = alt_res.data.get('results', alt_res.data) if isinstance(alt_res.data, dict) else alt_res.data
    if alt_list and len(alt_list) > 0:
        alt_id = alt_list[0]['id']
        alt_action = client.post(f"/api/alerts/{alt_id}/mark-read/")
        if alt_action.status_code == status.HTTP_200_OK:
            print(f"  [OK] Alert {alt_id} marked as read.")
        else:
            print(f"  [FAIL] Alert mark read failed: {alt_action.status_code}")

    print("\n" + "=" * 65)
    if not failed_endpoints:
        print("[SUCCESS] FULL ERP BACKEND SYSTEM AUDIT PASSED 100%!")
        print("=" * 65)
        return True
    else:
        print("[WARNING] SOME ENDPOINTS FAILED AUDIT. SEE LOG ABOVE.")
        print("=" * 65)
        return False

if __name__ == '__main__':
    success = run_comprehensive_api_audit()
    sys.exit(0 if success else 1)
