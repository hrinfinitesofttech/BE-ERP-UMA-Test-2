import os
import requests
import time
import re
import json

USERNAME = 'umaERP'
PASSWORD = 'AAaa@123456@'
DOMAIN = 'umaERP.pythonanywhere.com'
LOCAL_DIR = r'd:/UMA ERP/BE-ERP-UMA'
REMOTE_BASE = '/home/umaERP/BE-ERP-UMA'

EXCLUDE_DIRS = {'.git', '__pycache__', 'env', 'venv', '.vscode', '.idea'}
EXCLUDE_EXTS = {'.pyc', '.log', '.sqlite3'}
EXCLUDE_FILES = {'db.sqlite3', 'db.sqlite3-journal'}

def upload_with_retry(session, url, content, headers, max_retries=5):
    for attempt in range(max_retries):
        try:
            r = session.post(url, files={'content': content}, headers=headers)
            if r.status_code in [200, 201]:
                return True, r.status_code, "OK"
            elif r.status_code == 429:
                # Extract wait time from error message if possible
                wait = 3
                match = re.search(r'available in (\d+) seconds', r.text)
                if match:
                    wait = int(match.group(1)) + 2
                print(f"  [Rate limited - waiting {wait}s...]")
                time.sleep(wait)
            else:
                return False, r.status_code, r.text[:100]
        except Exception as e:
            time.sleep(2)
    return False, 500, "Max retries exceeded"

def deploy():
    print("=== Step 1: Authenticating with PythonAnywhere ===")
    session = requests.Session()
    login_url = 'https://www.pythonanywhere.com/login/'
    r_login_page = session.get(login_url)
    if r_login_page.status_code != 200:
        raise Exception(f"Failed to fetch login page: {r_login_page.status_code}")
    
    csrf = session.cookies.get('csrftoken')
    login_data = {
        'auth-username': USERNAME,
        'auth-password': PASSWORD,
        'login_view-current_step': 'auth',
        'csrfmiddlewaretoken': csrf
    }
    r_login = session.post(login_url, data=login_data, headers={'Referer': login_url})
    if r_login.status_code != 200:
        raise Exception(f"Login failed: status {r_login.status_code}")
    print("Authentication successful!")

    csrf_token = session.cookies.get('csrftoken')
    headers = {'X-CSRFToken': csrf_token, 'Referer': 'https://www.pythonanywhere.com/'}

    print("\n=== Step 2: Syncing Critical App Files to PythonAnywhere (with Throttle Handling) ===")
    
    # Prioritize HR and core files
    files_to_sync = []
    for root, dirs, files in os.walk(LOCAL_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file in EXCLUDE_FILES or any(file.endswith(ext) for ext in EXCLUDE_EXTS):
                continue
            local_path = os.path.join(root, file)
            rel_path = os.path.relpath(local_path, LOCAL_DIR).replace('\\', '/')
            files_to_sync.append((local_path, rel_path))

    # Sort store, HR, and core files first
    files_to_sync.sort(key=lambda x: (0 if 'apps/store' in x[1] else (1 if 'apps/hr' in x[1] else (2 if 'erp_backend' in x[1] else 3)), x[1]))

    success_count = 0
    fail_count = 0
    for local_path, rel_path in files_to_sync:
        remote_path = f"{REMOTE_BASE}/{rel_path}"
        with open(local_path, 'rb') as f:
            content = f.read()

        upload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_path}"
        ok, code, msg = upload_with_retry(session, upload_url, content, headers)
        
        if ok:
            print(f"[OK] {rel_path}")
            success_count += 1
        else:
            print(f"[FAIL] {rel_path} ({code}): {msg}")
            fail_count += 1
        
        # Friendly delay to avoid hitting PythonAnywhere 429 rate limit
        time.sleep(0.5)

    print(f"\nUpload Summary: {success_count} succeeded, {fail_count} failed.")

    print("\n=== Step 3: Reloading WebApp on PythonAnywhere ===")
    time.sleep(2)
    reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
    r_reload = session.post(reload_url, headers=headers)
    if r_reload.status_code == 200:
        print("[OK] WebApp reloaded successfully!")
    else:
        print(f"[FAIL] Reload returned: {r_reload.status_code} - {r_reload.text}")

    print("\n=== Step 4: Health Check on Live API Endpoints ===")
    time.sleep(5)
    endpoints = [
        '/api/auth/me/',
        '/api/items/',
        '/api/item-categories/',
        '/api/uoms/',
        '/api/warehouses/',
        '/api/goods-receipts/',
        '/api/qc-inspections/',
        '/api/stock-balances/',
        '/api/material-issues/',
        '/api/material-returns/',
        '/api/holidays/',
        '/api/wfh-requests/',
        '/api/missed-punches/',
        '/api/overtime-records/',
        '/api/early-checkouts/',
        '/api/employee-appraisals/',
        '/api/employees/',
        '/api/departments/',
        '/api/designations/',
        '/api/shifts/',
        '/api/leave-requests/',
        '/api/salary-structures/',
        '/api/payroll-records/',
        '/api/advance-loans/',
        '/api/reimbursements/',
        '/api/employee-onboardings/',
        '/api/employee-transfers/',
        '/api/employee-promotions/',
        '/api/employee-exits/',
        '/api/leads/',
        '/api/customers/',
        '/api/quotations/',
        '/api/sales-orders/',
        '/api/purchase-orders/',
        '/api/financial-years/',
        '/api/chart-of-accounts/',
        '/api/customer-machines/',
        '/api/drawings-2d/',
        '/api/models-3d/',
        '/api/customer-requirements/',
        '/api/designer/tasks/',
        '/api/designer/boms/',
        '/api/designer/assembly-drawings/',
        '/api/projects/project-delays/',
        '/api/projects/project-documents/',
        '/api/projects/change-requests/',
        '/api/approvals/',
        '/api/alerts/',
    ]

    base_api = f"https://{DOMAIN}"
    all_ok = True
    for ep in endpoints:
        url = base_api + ep
        try:
            r = requests.get(url, timeout=15)
            status_str = f"Status: {r.status_code}"
            if r.status_code == 200:
                print(f"[PASS] {ep} -> {status_str}")
            else:
                print(f"[WARN] {ep} -> {status_str} - {r.text[:80]}")
                all_ok = False
        except Exception as e:
            print(f"[ERROR] {ep} -> {e}")
            all_ok = False

    if all_ok:
        print("\n>>> ALL BACKEND ENDPOINTS ARE LIVE & RESPONDING 200 OK ON PYTHONANYWHERE! <<<")
    else:
        print("\nSome endpoints returned warnings. Review above output.")

if __name__ == '__main__':
    deploy()
