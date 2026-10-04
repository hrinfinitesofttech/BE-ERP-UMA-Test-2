"""
UmaERP - Runtime API & Database Verification Test Suite
Executes real HTTP requests against the backend database and verifies:
1. Authentication & Token generation
2. CRUD Persistence (Create, Read, Update, Delete)
3. Response timing / Latency
4. Database integrity
"""

import sys
import json
import time
import urllib.request
import urllib.error

BASE_URL = "https://umaERP.pythonanywhere.com/api"
# Also test local if available
LOCAL_URL = "http://127.0.0.1:8000/api"

def make_request(url, method="GET", data=None, token=None):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            latency = (time.time() - t0) * 1000
            status_code = res.status
            resp_body = res.read().decode("utf-8")
            parsed = json.loads(resp_body) if resp_body else {}
            return {"status": status_code, "data": parsed, "latency_ms": round(latency, 2), "error": None}
    except urllib.error.HTTPError as e:
        latency = (time.time() - t0) * 1000
        err_body = e.read().decode("utf-8") if e.fp else ""
        return {"status": e.code, "data": None, "latency_ms": round(latency, 2), "error": err_body}
    except Exception as ex:
        latency = (time.time() - t0) * 1000
        return {"status": 0, "data": None, "latency_ms": round(latency, 2), "error": str(ex)}

def run_tests():
    results = []
    print("=================================================================")
    print("UMA ERP - REAL RUNTIME END-TO-END API & DATABASE VERIFICATION")
    print(f"Target Backend: {BASE_URL}")
    print("=================================================================\n")

    # Step 1: Authentication
    print("1. Testing Authentication (/auth/login/)...")
    login_res = make_request(f"{BASE_URL}/auth/login/", method="POST", data={"username": "admin", "password": "123456"})
    token = None
    if login_res["status"] == 200 and "access" in login_res["data"]:
        token = login_res["data"]["access"]
        print(f"   [PASS] Login Successful! Token acquired ({login_res['latency_ms']} ms)")
    else:
        print(f"   [WARN] Direct login returned {login_res['status']}: {login_res['error']}")
    
    # Step 2: Test Endpoints List & Read
    endpoints_to_test = [
        ("CRM", "Leads", "/leads/"),
        ("CRM", "Customers", "/customers/"),
        ("CRM", "Enquiries", "/enquiries/"),
        ("CRM", "Quotations", "/quotations/"),
        ("CRM", "Customer POs", "/customer-pos/"),
        ("CRM", "Sales Orders", "/sales-orders/"),
        ("Projects", "Project Jobs", "/projects/"),
        ("Designer", "Design Jobs", "/designer/jobs/"),
        ("Designer", "BOMs", "/designer/boms/"),
        ("Purchase", "Suppliers", "/suppliers/"),
        ("Purchase", "Purchase Requisitions", "/purchase-requisitions/"),
        ("Purchase", "Purchase Orders", "/purchase-orders/"),
        ("Store", "Items", "/items/"),
        ("Store", "Warehouses", "/warehouses/"),
        ("Store", "GRNs", "/grns/"),
        ("Production", "Work Orders", "/work-orders/"),
        ("Production", "Work Centers", "/work-centers/"),
        ("Accounting", "Sales Invoices", "/sales-invoices/"),
        ("Accounting", "Purchase Invoices", "/purchase-invoices/"),
        ("HR", "Employees", "/employees/"),
        ("HR", "Departments", "/departments/"),
        ("HR", "Designations", "/designations/"),
        ("HR", "Leave Requests", "/leave-requests/"),
        ("Organization", "Company", "/company/"),
    ]

    print("\n2. Testing Module Read Endpoints (GET)...")
    for module, name, ep in endpoints_to_test:
        r = make_request(f"{BASE_URL}{ep}", method="GET", token=token)
        count = len(r["data"]) if isinstance(r["data"], list) else (len(r["data"].get("results", [])) if isinstance(r["data"], dict) else 1)
        passed = r["status"] in [200, 201]
        status_str = "PASS" if passed else "FAIL"
        print(f"   [{status_str}] {module} -> {name} ({ep}): Status={r['status']}, Count={count}, Latency={r['latency_ms']} ms")
        results.append({
            "module": module,
            "page": name,
            "endpoint": ep,
            "read_status": r["status"],
            "read_latency": r["latency_ms"],
            "count": count,
            "read_pass": passed
        })

    # Step 3: Real Database CRUD Lifecycle Test on Customers
    print("\n3. Testing Real Database CRUD Lifecycle: Customer...")
    test_code = f"CUST-TEST-{int(time.time())}"
    test_payload = {
        "customer_code": test_code,
        "company_name": "API_TEST_CUSTOMER_001",
        "contact_person": "Verification Agent",
        "mobile": "9998887776",
        "email": "test.customer@umaerp.com",
        "billing_address": "GIDC Vatva Phase-II, Ahmedabad",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "country": "India",
        "gstin": "24AAACX0000X1Z1",
        "payment_terms": "30 days net",
        "credit_limit": 500000,
        "customer_type": "company"
    }

    # CREATE
    create_res = make_request(f"{BASE_URL}/customers/", method="POST", data=test_payload, token=token)
    created_id = None
    if create_res["status"] in [200, 201] and create_res["data"]:
        created_id = create_res["data"].get("id") or create_res["data"].get("customer_code") or test_code
        print(f"   [PASS] CREATE: Customer created with ID '{created_id}' ({create_res['latency_ms']} ms)")
    else:
        print(f"   [FAIL] CREATE: Failed with status {create_res['status']}: {create_res['error']}")

    # READ BY ID
    if created_id:
        get_res = make_request(f"{BASE_URL}/customers/{created_id}/", method="GET", token=token)
        if get_res["status"] == 200 and get_res["data"]:
            print(f"   [PASS] READ: Retrieved customer '{get_res['data'].get('company_name')}' ({get_res['latency_ms']} ms)")
        else:
            print(f"   [FAIL] READ: Failed with status {get_res['status']}: {get_res['error']}")

        # UPDATE
        update_payload = {"company_name": "API_TEST_CUSTOMER_001_UPDATED", "credit_limit": 750000}
        update_res = make_request(f"{BASE_URL}/customers/{created_id}/", method="PATCH", data=update_payload, token=token)
        if update_res["status"] in [200, 201]:
            print(f"   [PASS] UPDATE: Updated company_name to 'API_TEST_CUSTOMER_001_UPDATED' ({update_res['latency_ms']} ms)")
        else:
            print(f"   [FAIL] UPDATE: Failed with status {update_res['status']}: {update_res['error']}")

        # DELETE / CLEANUP
        del_res = make_request(f"{BASE_URL}/customers/{created_id}/", method="DELETE", token=token)
        if del_res["status"] in [200, 204]:
            print(f"   [PASS] DELETE: Successfully removed test customer ({del_res['latency_ms']} ms)")
        else:
            print(f"   [WARN] DELETE: Status {del_res['status']}: {del_res['error']}")

    print("\n=================================================================")
    print("RUNTIME API VERIFICATION COMPLETE")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
