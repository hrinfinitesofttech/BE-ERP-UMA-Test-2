import os
import requests
import time
import re

USERNAME = 'umaERP'
PASSWORD = 'AAaa@123456@'
DOMAIN = 'umaERP.pythonanywhere.com'
REMOTE_BASE = '/home/umaERP/BE-ERP-UMA'
LOCAL_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES_TO_SYNC = [
    'apps/crm/views.py',
    'apps/crm/serializers.py',
    'apps/production/views.py',
]

def upload_file(session, rel_path, headers):
    local_path = os.path.join(LOCAL_BASE, rel_path.replace('/', os.sep))
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
    print("=" * 60)
    print("  SYNCING MODIFIED BACKEND FILES TO PYTHONANYWHERE LIVE ")
    print("=" * 60)

    print("\n[1/3] Authenticating with PythonAnywhere...")
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

    print("\n[2/3] Uploading updated backend files to PythonAnywhere...")
    for fpath in FILES_TO_SYNC:
        ok, msg = upload_file(session, fpath, headers)
        print(f"  -> {fpath}: {'SUCCESS' if ok else 'FAILED'} ({msg})", flush=True)
        time.sleep(0.5)

    print("\n[3/3] Reloading PythonAnywhere WebApp (umaERP.pythonanywhere.com)...")
    reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
    r_reload = session.post(reload_url, headers=headers, timeout=25)
    if r_reload.status_code == 200:
        print("[OK] WebApp Reloaded Successfully!")
    else:
        print(f"[WARN] Reload returned: {r_reload.status_code} - {r_reload.text[:100]}")

    print("\nChecking Live API Health...")
    time.sleep(3)
    try:
        r_health = requests.get(f"https://{DOMAIN}/api/leads/", timeout=15)
        print(f"Live API status code: {r_health.status_code}")
    except Exception as e:
        print(f"Error checking health: {e}")

if __name__ == '__main__':
    main()
