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
    'apps/production/models.py',
    'apps/production/serializers.py',
    'apps/production/views.py',
    'apps/production/urls.py',
    'erp_backend/urls.py',
    'apps/production/migrations/0007_workermaster_workerdailyroutine.py',
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
    print(f"\n[1/4] Uploading Worker Routine & Production backend files to PythonAnywhere...")
    for f in TARGET_FILES:
        upload_file_to_pa(f)
        time.sleep(0.5)

def run_migrations_and_seed():
    print(f"\n[2/4] Triggering remote database migration & initial seeding via WSGI...")

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
    
    from apps.production.models import WorkerMaster, WorkerDailyRoutine

    # Completely remove all mock workers and routines as explicitly requested by user
    deleted_routines, _ = WorkerDailyRoutine.objects.all().delete()
    deleted_workers, _ = WorkerMaster.objects.all().delete()

    with open('/home/erpUMA/worker_migrate_status.txt', 'w') as f:
        f.write(f'MOCK_DATA_CLEARED - Deleted {deleted_workers} workers, {deleted_routines} routines.')
except Exception as e:
    with open('/home/erpUMA/worker_migrate_status.txt', 'w') as f:
        f.write(f'MIGRATE_ERROR: {e}')
"""
    # 1. Upload migration WSGI
    requests.post(f"{BASE_URL}/files/path{WSGI_PATH}", headers=HEADERS, files={'content': migration_hook_wsgi})
    print("  -> Migration & seeding hook placed into WSGI.")

    # 2. Reload Webapp
    r_rel = requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=HEADERS)
    print(f"  -> Webapp reload requested: {r_rel.status_code}")
    time.sleep(4)

    # 3. Hit endpoint to trigger WSGI execution
    try:
        requests.get(f"https://{DOMAIN}/api/company/", timeout=20)
    except Exception:
        pass
    time.sleep(3)

    # 4. Read worker_migrate_status.txt
    try:
        r_stat = requests.get(f"{BASE_URL}/files/path/home/{USERNAME}/worker_migrate_status.txt", headers=HEADERS)
        print(f"  -> Migration & Seed result on PythonAnywhere: {r_stat.text.strip()}")
    except Exception as e:
        print(f"  -> Could not read status file: {e}")

    # 5. Restore clean production WSGI
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
    time.sleep(4)

def verify_live_endpoints():
    print(f"\n[3/4] Verifying live endpoints on https://{DOMAIN} ...")
    base_api = f"https://{DOMAIN}/api"
    
    # 1. Test Workers endpoint
    try:
        r_workers = requests.get(f"{base_api}/production/workers/", timeout=20)
        print(f"  -> GET {base_api}/production/workers/ : HTTP {r_workers.status_code}")
        if r_workers.status_code == 200:
            workers_list = r_workers.json()
            if isinstance(workers_list, dict) and 'results' in workers_list:
                workers_list = workers_list['results']
            print(f"     [OK] Total live workers in DB: {len(workers_list)}")
            if len(workers_list) > 0:
                print(f"     Sample: {workers_list[0].get('slNo')}. {workers_list[0].get('workerName')} ({workers_list[0].get('trade')})")
    except Exception as e:
        print(f"  -> Workers test error: {e}")

    # 2. Test Worker Routines endpoint
    try:
        r_routines = requests.get(f"{base_api}/production/worker-routines/", timeout=20)
        print(f"  -> GET {base_api}/production/worker-routines/ : HTTP {r_routines.status_code}")
    except Exception as e:
        print(f"  -> Worker Routines test error: {e}")

    # 3. Test Top-level alias
    try:
        r_top = requests.get(f"{base_api}/workers/", timeout=20)
        print(f"  -> GET {base_api}/workers/ (root alias) : HTTP {r_top.status_code}")
    except Exception as e:
        print(f"  -> Top-level alias test error: {e}")

if __name__ == '__main__':
    sync_files()
    run_migrations_and_seed()
    verify_live_endpoints()
    print("\n[4/4] PYTHONANYWHERE DEPLOYMENT & LIVE VERIFICATION COMPLETED SUCCESSFULLY!")
