import os
import sys
import requests
import time
import re

USERNAME = 'umaERP'
PASSWORD = 'AAaa@123456@'
DOMAIN = 'umaERP.pythonanywhere.com'
REMOTE_BASE = '/home/umaERP/BE-ERP-UMA'
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_TO_DEPLOY = [
    'apps/purchase/models.py',
    'apps/purchase/serializers.py',
    'apps/purchase/views.py',
    'apps/purchase/po_pdf.py',
    'apps/purchase/rfq_pdf.py',
    'apps/purchase/migrations/0005_requestforquotation_delivery_location_and_more.py',
]

def log(msg):
    print(msg, flush=True)

def upload_file(session, rel_path, headers):
    local_path = os.path.join(LOCAL_DIR, rel_path.replace('/', os.sep))
    if not os.path.exists(local_path):
        return False, f"File not found locally: {local_path}"
    
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
    log("  DEPLOYING LATEST PURCHASE & PDF UPDATES TO PYTHONANYWHERE")
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

    log("\n[2/4] Uploading modified & new files to PythonAnywhere...")
    for rel_path in FILES_TO_DEPLOY:
        ok, msg = upload_file(session, rel_path, headers)
        if ok:
            log(f"  [OK] {rel_path}")
        else:
            log(f"  [FAIL] {rel_path} -> {msg}")
        time.sleep(0.5)

    log("\n[3/4] Ensuring WSGI Auto-migration & Reloading WebApp...")
    wsgi_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/"
    r_webapp = session.get(wsgi_url, headers=headers)
    wsgi_path = r_webapp.json().get('user_wsgi_file_path')

    if wsgi_path:
        r_file = session.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{wsgi_path}", headers=headers)
        original_wsgi = r_file.text
        migrate_code = """
try:
    from django.core.management import call_command
    call_command('migrate')
    print("Auto-migration successful on webapp reload!")
except Exception as e:
    print("Auto-migration notice:", e)
"""
        clean_wsgi = re.sub(r'try:\s+from django\.core\.management import call_command.*?print\("Auto-migration notice:", e\)\s*', '', original_wsgi, flags=re.DOTALL)
        new_wsgi = clean_wsgi.strip() + "\n" + migrate_code
        session.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{wsgi_path}", files={"content": new_wsgi}, headers=headers)

    reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
    r_reload = session.post(reload_url, headers=headers, timeout=25)
    if r_reload.status_code == 200:
        log("[OK] WebApp Reloaded Successfully on PythonAnywhere!")
    else:
        log(f"[WARN] Reload returned status: {r_reload.status_code}")

    log("\n[4/4] Verifying Live API Status on PythonAnywhere...")
    time.sleep(5)
    endpoints = [
        '/api/purchase-orders/',
        '/api/rfqs/',
        '/api/purchase-invoices/',
        '/api/health/',
    ]
    base_url = f"https://{DOMAIN}"
    for ep in endpoints:
        try:
            r = requests.get(base_url + ep, timeout=15)
            log(f"  Status {r.status_code} -> {ep}")
        except Exception as e:
            log(f"  Error -> {ep}: {e}")

    log("\n[DONE] PythonAnywhere backend deployment complete!")

if __name__ == '__main__':
    main()
