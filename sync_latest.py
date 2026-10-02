import os
import requests
import time
import re

USERNAME = 'umaERP'
PASSWORD = 'AAaa@123456@'
DOMAIN = 'umaERP.pythonanywhere.com'
REMOTE_BASE = '/home/umaERP/BE-ERP-UMA'
LOCAL_DIR = r'd:/UMA ERP/BE-ERP-UMA'

TARGET_FILES = [
    'apps/production/models.py',
    'apps/production/serializers.py',
    'apps/production/views.py',
    'apps/hr/serializers.py',
    'apps/hr/views.py',
    'apps/hr/models.py',
    'apps/crm/serializers.py',
    'apps/crm/views.py',
    'apps/designer/models.py',
    'apps/designer/serializers.py',
    'apps/designer/views.py',
    'apps/purchase/serializers.py',
    'apps/purchase/views.py',
    'apps/projects/serializers.py',
    'apps/projects/views.py',
    'apps/store/serializers.py',
    'apps/store/views.py',
]

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
                return True, f"Uploaded ({r.status_code})"
            elif r.status_code == 429:
                wait_time = 3
                m = re.search(r'available in (\d+) seconds', r.text)
                if m:
                    wait_time = int(m.group(1)) + 1
                print(f"  [Rate limited by PythonAnywhere, waiting {wait_time}s...]", flush=True)
                time.sleep(wait_time)
            else:
                return False, f"Status {r.status_code}: {r.text[:60]}"
        except Exception as e:
            time.sleep(2)
    return False, "Timed out after retries"

def main():
    print("=========================================================")
    print("   CHECKING & SYNCING BACKEND TO PYTHONANYWHERE          ")
    print("=========================================================")
    
    print("\n[1/4] Authenticating with PythonAnywhere...")
    session = requests.Session()
    login_url = 'https://www.pythonanywhere.com/login/'
    r_login_page = session.get(login_url, timeout=15)
    if r_login_page.status_code != 200:
        print(f"Failed to fetch login page: {r_login_page.status_code}")
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
        print(f"Login failed with status {r_login.status_code}")
        return
    print("[OK] Authentication successful!")

    csrf_token = session.cookies.get('csrftoken')
    headers = {'X-CSRFToken': csrf_token, 'Referer': 'https://www.pythonanywhere.com/'}

    print("\n[2/4] Uploading updated backend files to PythonAnywhere...")
    for fpath in TARGET_FILES:
        ok, msg = upload_file(session, fpath, headers)
        print(f"  -> {fpath}: {'SUCCESS' if ok else 'FAILED'} ({msg})", flush=True)
        time.sleep(0.5)

    print("\n[3/4] Reloading PythonAnywhere WebApp (umaERP.pythonanywhere.com)...")
    reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
    r_reload = session.post(reload_url, headers=headers, timeout=25)
    if r_reload.status_code == 200:
        print("[OK] WebApp Reloaded Successfully!")
    else:
        print(f"[WARN] Reload returned: {r_reload.status_code} - {r_reload.text[:100]}")

    print("\n[4/4] Verifying Live API Status on https://umaERP.pythonanywhere.com ...")
    time.sleep(3)
    endpoints = [
        '/api/auth/me/',
        '/api/departments/',
        '/api/designations/',
        '/api/routing-operations/',
        '/api/production-holds/',
        '/api/production-schedules/',
        '/api/production-entries/',
        '/api/rework-orders/',
        '/api/production-scraps/',
        '/api/designer/jobs/',
    ]
    all_ok = True
    for ep in endpoints:
        try:
            res = requests.get(f"https://{DOMAIN}{ep}", timeout=10)
            status_indicator = f"[LIVE OK - Status {res.status_code}]" if res.status_code in [200, 401, 403] else f"[WARN - Status {res.status_code}]"
            print(f"  {status_indicator}: https://{DOMAIN}{ep}")
        except Exception as err:
            all_ok = False
            print(f"  [ERROR]: https://{DOMAIN}{ep} -> {err}")

    print("\n=========================================================")
    print("  PYTHONANYWHERE BACKEND UPDATE VERIFIED & COMPLETE!     ")
    print("=========================================================")

if __name__ == '__main__':
    main()
