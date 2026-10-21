import os
import sys
import requests
import time

API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
DOMAIN = 'erpUMA.pythonanywhere.com'
BASE_URL = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}
WSGI_PATH = '/var/www/erpuma_pythonanywhere_com_wsgi.py'

TARGET_FILES = [
    'apps/maintenance/models.py',
    'apps/maintenance/serializers.py',
    'apps/maintenance/views.py',
    'apps/maintenance/admin.py',
    'apps/maintenance/migrations/0003_servicerequest_applicant_name_and_more.py',
    'apps/core/management/commands/seed_phase5.py',
]

def upload_file_to_pa(rel_path):
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path.replace('/', os.sep))
    if not os.path.exists(local_path):
        print(f"  [ERROR] Local file not found: {local_path}")
        return False
    with open(local_path, 'rb') as f:
        content = f.read()

    url = f"{BASE_URL}/files/path/home/{USERNAME}/BE-ERP-UMA/{rel_path}"
    for attempt in range(5):
        try:
            r = requests.post(url, headers=HEADERS, files={'content': content}, timeout=30)
            if r.status_code in [200, 201]:
                print(f"  [OK] Uploaded {rel_path} ({r.status_code})")
                return True
            elif r.status_code == 429:
                print(f"  [WAIT] Rate limited, waiting 3s...")
                time.sleep(3)
            else:
                print(f"  [FAIL] {rel_path}: {r.status_code} - {r.text[:80]}")
                return False
        except Exception as e:
            time.sleep(2)
    return False

def sync_files():
    print(f"\n[1/5] Uploading target backend files to {USERNAME} ({DOMAIN})...")
    for f in TARGET_FILES:
        upload_file_to_pa(f)
        time.sleep(0.5)

def run_migrations():
    print(f"\n[2/5] Triggering database migration via WSGI execution...")
    # Read clean WSGI
    r_get = requests.get(f"{BASE_URL}/files/path{WSGI_PATH}", headers=HEADERS)
    original_wsgi = r_get.text

    migration_hook_wsgi = """import os
import sys

path = '/home/erpUMA/BE-ERP-UMA'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'erp_backend.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

try:
    from django.core.management import call_command
    call_command('migrate')
    with open('/home/erpUMA/migrate_status.txt', 'w') as f:
        f.write('MIGRATE_SUCCESS')
except Exception as e:
    with open('/home/erpUMA/migrate_status.txt', 'w') as f:
        f.write(f'MIGRATE_ERROR: {e}')
"""
    # 1. Upload migration WSGI
    requests.post(f"{BASE_URL}/files/path{WSGI_PATH}", headers=HEADERS, files={'content': migration_hook_wsgi})
    print("  -> Migration hook placed into WSGI.")

    # 2. Reload Webapp
    r_rel = requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=HEADERS)
    print(f"  -> Webapp reload requested: {r_rel.status_code}")
    time.sleep(3)

    # 3. Hit endpoint to trigger WSGI startup
    try:
        requests.get(f"https://{DOMAIN}/api/service-requests/", timeout=20)
    except Exception as e:
        pass
    time.sleep(3)

    # 4. Read migrate_status.txt
    r_stat = requests.get(f"{BASE_URL}/files/path/home/{USERNAME}/migrate_status.txt", headers=HEADERS)
    print(f"  -> Migration result on PythonAnywhere: {r_stat.text.strip()}")

    # 5. Restore clean WSGI
    clean_wsgi = """import os
import sys

path = '/home/erpUMA/BE-ERP-UMA'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'erp_backend.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"""
    requests.post(f"{BASE_URL}/files/path{WSGI_PATH}", headers=HEADERS, files={'content': clean_wsgi})
    print("  -> Clean WSGI restored.")

    # 6. Final reload
    requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=HEADERS)
    print("  -> Final clean webapp reload triggered.")
    time.sleep(3)

def verify_live_endpoints():
    print(f"\n[3/5] Verifying live API response & fields on https://{DOMAIN} ...")
    base_api = f"https://{DOMAIN}/api"
    try:
        r_opt = requests.options(f"{base_api}/service-requests/", timeout=15)
        actions = list(r_opt.json().get('actions', {}).get('POST', {}).keys())
        print(f"  -> Live ServiceRequest Fields available in POST action:")
        new_fields = [
            'contactNumber', 'homeAddress', 'requestType', 'problemDescription',
            'requestedDateTime', 'urgencyLevel', 'applicantName', 'requestSubmissionDate',
            'completedBy', 'completedDate', 'approvedBy', 'approvedDate'
        ]
        all_present = True
        for nf in new_fields:
            present = nf in actions or nf.lower() in [a.lower() for a in actions]
            print(f"     {'[OK]' if present else '[MISSING]'} {nf}")
            if not present:
                all_present = False
        if all_present:
            print("\n>>> ALL NEW SERVICE REQUEST FIELDS ARE VERIFIED LIVE ON PYTHONANYWHERE! <<<")
        else:
            print("\n>>> Some fields are missing, checking serializer representation...")
    except Exception as e:
        print(f"  Options check error: {e}")

    try:
        r_get = requests.get(f"{base_api}/service-requests/", timeout=15)
        print(f"  -> GET /api/service-requests/ HTTP {r_get.status_code}")
    except Exception as e:
        print(f"  GET error: {e}")

if __name__ == '__main__':
    sync_files()
    run_migrations()
    verify_live_endpoints()
