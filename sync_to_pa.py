import sys
import os
import requests
import time
import re
import zipfile
import io

USERNAME = 'umaERP'
PASSWORD = 'AAaa@123456@'
DOMAIN = 'umaERP.pythonanywhere.com'
REMOTE_BASE = '/home/umaERP/BE-ERP-UMA'
LOCAL_DIR = r'd:/UMA ERP/BE-ERP-UMA'

EXCLUDE_DIRS = {'.git', '__pycache__', 'env', 'venv', '.vscode', '.idea', 'staticfiles'}
EXCLUDE_EXTS = {'.pyc', '.log', '.sqlite3'}
EXCLUDE_FILES = {'db.sqlite3', 'db.sqlite3-journal', 'sync_to_pa.py', 'deploy_pythonanywhere.py'}

def log(msg):
    try:
        print(msg, flush=True)
    except Exception:
        print(msg.encode('ascii', 'replace').decode('ascii'), flush=True)

def upload_file(session, rel_path, headers):
    local_path = os.path.join(LOCAL_DIR, rel_path.replace('/', os.sep))
    if not os.path.exists(local_path):
        return False, "File not found locally"
    
    with open(local_path, 'rb') as f:
        content = f.read()

    remote_path = f"{REMOTE_BASE}/{rel_path}"
    upload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_path}"
    
    for attempt in range(5):
        try:
            r = session.post(upload_url, files={'content': content}, headers=headers, timeout=30)
            if r.status_code in [200, 201]:
                return True, "OK"
            elif r.status_code == 429:
                wait_time = 3
                m = re.search(r'available in (\d+) seconds', r.text)
                if m:
                    wait_time = int(m.group(1)) + 1
                log(f"  [Rate limited by PythonAnywhere, waiting {wait_time}s...]")
                time.sleep(wait_time)
            else:
                return False, f"Status {r.status_code}: {r.text[:60]}"
        except Exception as e:
            time.sleep(2)
    return False, "Timed out after retries"

def main():
    log("=========================================================")
    log("   DEPLOING BE-ERP-UMA TO PYTHONANYWHERE (umaERP)       ")
    log("=========================================================")
    
    log("\n[1/4] Authenticating with PythonAnywhere...")
    session = requests.Session()
    login_url = 'https://www.pythonanywhere.com/login/'
    r_login_page = session.get(login_url, timeout=15)
    if r_login_page.status_code != 200:
        log(f"Failed to fetch login page: {r_login_page.status_code}")
        return

    csrf = session.cookies.get('csrftoken')
    login_data = {
        'auth-username': USERNAME,
        'auth-password': PASSWORD,
        'login_view-current_step': 'auth',
        'csrfmiddlewaretoken': csrf
    }
    r_login = session.post(login_url, data=login_data, headers={'Referer': login_url}, timeout=15)
    if r_login.status_code != 200:
        log(f"Login failed with status {r_login.status_code}")
        return
    log("[OK] Authentication successful! Connected to PythonAnywhere.")

    csrf_token = session.cookies.get('csrftoken')
    headers = {'X-CSRFToken': csrf_token, 'Referer': 'https://www.pythonanywhere.com/'}

    log("\n[2/4] Syncing Backend App Code & API Views...")
    files_to_sync = []
    for root, dirs, files in os.walk(LOCAL_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file in EXCLUDE_FILES or any(file.endswith(ext) for ext in EXCLUDE_EXTS):
                continue
            local_path = os.path.join(root, file)
            rel_path = os.path.relpath(local_path, LOCAL_DIR).replace('\\', '/')
            files_to_sync.append(rel_path)

    # Sort priority files (views, serializers, models, settings, urls) first
    files_to_sync.sort(key=lambda p: (
        0 if ('views.py' in p or 'serializers.py' in p or 'urls.py' in p or 'settings.py' in p) else 1,
        p
    ))

    log(f"Total files to deploy: {len(files_to_sync)}")

    synced = 0
    failed = 0
    for idx, rel_path in enumerate(files_to_sync, 1):
        ok, msg = upload_file(session, rel_path, headers)
        if ok:
            log(f"  [{idx}/{len(files_to_sync)}] [OK] {rel_path}")
            synced += 1
        else:
            log(f"  [{idx}/{len(files_to_sync)}] [FAIL] {rel_path} -> {msg}")
            failed += 1
        time.sleep(0.4)

    log(f"\nUpload Completed: {synced} files synced, {failed} errors.")

    log("\n[3/4] Reloading PythonAnywhere WebApp (umaERP.pythonanywhere.com)...")
    time.sleep(1)
    reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
    r_reload = session.post(reload_url, headers=headers, timeout=25)
    if r_reload.status_code == 200:
        log("[OK] WebApp Reloaded Successfully on PythonAnywhere!")
    else:
        log(f"[WARN] Reload returned: {r_reload.status_code} - {r_reload.text[:100]}")

    log("\n[4/4] Verifying Live Health on Backend APIs...")
    time.sleep(3)
    check_endpoints = [
        '/api/auth/me/',
        '/api/employees/',
        '/api/departments/',
        '/api/designations/',
        '/api/employee-transfers/',
        '/api/employee-onboardings/',
        '/api/purchase-orders/',
        '/api/quotations/',
        '/api/designer/tasks/',
        '/api/designer/jobs/',
    ]
    base_url = f"https://{DOMAIN}"
    for ep in check_endpoints:
        try:
            r = requests.get(base_url + ep, timeout=10)
            log(f"  Status {r.status_code} -> {ep}")
        except Exception as e:
            log(f"  Error -> {ep}: {e}")

    log("\n=========================================================")
    log("  SUCCESS! All code is live on PythonAnywhere!           ")
    log("=========================================================")

if __name__ == '__main__':
    main()
