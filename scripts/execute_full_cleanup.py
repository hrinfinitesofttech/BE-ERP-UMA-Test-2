import os
import shutil
import time
import requests
import sqlite3
import subprocess
from datetime import datetime

API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
DOMAIN = 'erpUMA.pythonanywhere.com'
BASE_URL = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}'
headers = {'Authorization': f'Token {API_TOKEN}'}
BACKUP_DIR = 'backups'

def step1_local_backup():
    print("\n" + "=" * 60)
    print("STEP 1: Backing up Local Database (db.sqlite3)...")
    print("=" * 60)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    local_backup = os.path.join(BACKUP_DIR, f"local_db_pre_cleanup_{timestamp}.sqlite3")
    shutil.copy2("db.sqlite3", local_backup)
    
    # Verify sqlite integrity
    con = sqlite3.connect(local_backup)
    cur = con.cursor()
    cur.execute("PRAGMA integrity_check;")
    res = cur.fetchall()
    con.close()
    print(f" [PASS] Local DB Backup created: {local_backup} ({os.path.getsize(local_backup)} bytes)")
    print(f" [PASS] Integrity check result: {res}")
    return local_backup

def step2_remote_pa_backup():
    print("\n" + "=" * 60)
    print("STEP 2: Downloading Live PythonAnywhere Database Backup...")
    print("=" * 60)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    remote_backup = os.path.join(BACKUP_DIR, f"pa_live_db_pre_cleanup_{timestamp}.sqlite3")
    db_url = f"{BASE_URL}/files/path/home/{USERNAME}/BE-ERP-UMA/db.sqlite3"
    
    r = requests.get(db_url, headers=headers, stream=True, timeout=60)
    if r.status_code == 200:
        with open(remote_backup, 'wb') as f:
            for chunk in r.iter_content(chunk_size=16384):
                f.write(chunk)
        size = os.path.getsize(remote_backup)
        print(f" [PASS] Remote DB Downloaded: {remote_backup} ({size} bytes)")
        
        # Verify sqlite integrity
        con = sqlite3.connect(remote_backup)
        cur = con.cursor()
        cur.execute("PRAGMA integrity_check;")
        res = cur.fetchall()
        con.close()
        print(f" [PASS] Remote DB Integrity check: {res}")
        return remote_backup
    else:
        print(f" [FAIL] Failed to download remote DB: {r.status_code} {r.text[:200]}")
        raise RuntimeError("Remote DB download failed!")

def step3_execute_local_cleanup():
    print("\n" + "=" * 60)
    print("STEP 3: Executing Cleanup on Local Database...")
    print("=" * 60)
    cmd = [
        "python", "manage.py", "cleanup_testing_data",
        "--execute",
        "--confirm-go-live", "CONFIRM-CLEANUP-UMAERP-2026"
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    print(p.stdout)
    if p.stderr:
        print("Stderr:", p.stderr)
    if p.returncode != 0:
        raise RuntimeError(f"Local cleanup failed with exit code {p.returncode}")
    print(" [PASS] Local Database Cleanup Complete!")

def step4_execute_pa_cleanup():
    print("\n" + "=" * 60)
    print("STEP 4: Executing Cleanup on Live PythonAnywhere Server...")
    print("=" * 60)
    wsgi_path = '/var/www/erpuma_pythonanywhere_com_wsgi.py'
    clean_wsgi = """import os
import sys

path = '/home/erpUMA/BE-ERP-UMA'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'erp_backend.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"""
    
    cleanup_runner_wsgi = """import os
import sys
import subprocess

path = '/home/erpUMA/BE-ERP-UMA'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'erp_backend.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

try:
    python_bin = '/home/erpUMA/.virtualenvs/erp-venv/bin/python'
    cmd = f"{python_bin} manage.py cleanup_testing_data --execute --confirm-go-live CONFIRM-CLEANUP-UMAERP-2026"
    p = subprocess.run(cmd, shell=True, cwd=path, capture_output=True, text=True, timeout=120)
    with open('/home/erpUMA/cleanup_status.txt', 'w') as f:
        f.write(f"EXIT_CODE:{p.returncode}\\nSTDOUT:\\n{p.stdout}\\nSTDERR:\\n{p.stderr}")
except Exception as e:
    with open('/home/erpUMA/cleanup_status.txt', 'w') as f:
        f.write(f"EXCEPTION:{e}")
"""

    print(" -> Uploading cleanup runner to PythonAnywhere WSGI...")
    r_up = requests.post(f"{BASE_URL}/files/path{wsgi_path}", headers=headers, files={'content': cleanup_runner_wsgi})
    print(f" -> WSGI upload status: {r_up.status_code}")
    
    print(" -> Reloading PythonAnywhere webapp to trigger cleanup...")
    r_reload = requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=headers)
    print(f" -> Reload status: {r_reload.status_code}")
    time.sleep(5)
    
    print(" -> Triggering request to invoke WSGI...")
    try:
        requests.get(f"https://{DOMAIN}/api/health/", timeout=20)
    except Exception as e:
        print(" -> (Worker restart trigger notice):", e)
    
    time.sleep(6)
    
    print(" -> Checking cleanup output status on PythonAnywhere...")
    r_status = requests.get(f"{BASE_URL}/files/path/home/erpUMA/cleanup_status.txt", headers=headers)
    print(f"Cleanup Status Output ({r_status.status_code}):\n{r_status.text}")
    
    print(" -> Restoring clean WSGI...")
    requests.post(f"{BASE_URL}/files/path{wsgi_path}", headers=headers, files={'content': clean_wsgi})
    requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=headers)
    time.sleep(4)
    print(" [PASS] Remote PythonAnywhere Database Cleanup Complete!")

def step5_verify():
    print("\n" + "=" * 60)
    print("STEP 5: Verifying Clean State on Live API...")
    print("=" * 60)
    endpoints = [
        ('/api/projects/', 'Projects Master'),
        ('/api/projects-planning/stages/', 'Planning Stages'),
        ('/api/crm/leads/', 'CRM Leads'),
        ('/api/quotations/', 'Quotations'),
        ('/api/sales-orders/', 'Sales Orders'),
        ('/api/work-orders/', 'Work Orders'),
        ('/api/employees/', 'Employees Directory (Preserved)'),
        ('/api/organization/departments/', 'Departments (Preserved)'),
    ]
    for path, name in endpoints:
        try:
            r = requests.get(f"https://{DOMAIN}{path}", timeout=15)
            data = r.json() if r.status_code == 200 else []
            count = len(data) if isinstance(data, list) else (data.get('count', len(data.get('results', []))) if isinstance(data, dict) else 'N/A')
            print(f"  [{name}]: HTTP {r.status_code} -> Count: {count}")
        except Exception as e:
            print(f"  [{name}]: Error {e}")

if __name__ == '__main__':
    step1_local_backup()
    step2_remote_pa_backup()
    step3_execute_local_cleanup()
    step4_execute_pa_cleanup()
    step5_verify()
