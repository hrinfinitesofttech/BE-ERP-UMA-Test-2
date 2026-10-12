import requests
import time

API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
DOMAIN = 'erpUMA.pythonanywhere.com'
BASE_URL = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}'
headers = {'Authorization': f'Token {API_TOKEN}'}
wsgi_path = '/var/www/erpuma_pythonanywhere_com_wsgi.py'

print(">>> 1. Reading current WSGI...")
r_wsgi = requests.get(f"{BASE_URL}/files/path{wsgi_path}", headers=headers)
print(f"Current WSGI fetch status: {r_wsgi.status_code}")
clean_wsgi = """import os
import sys

path = '/home/erpUMA/BE-ERP-UMA'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'erp_backend.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"""

seed_wsgi = f"""import os
import sys

path = '/home/erpUMA/BE-ERP-UMA'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'erp_backend.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

try:
    import scripts.seed_user_roles
    with open('/home/erpUMA/seed_status.txt', 'w') as f:
        f.write('SEED_COMPLETED_SUCCESS')
except Exception as e:
    with open('/home/erpUMA/seed_status.txt', 'w') as f:
        f.write(f'SEED_ERROR: {{e}}')
"""

print(">>> 2. Uploading seed runner to WSGI...")
r_up = requests.post(f"{BASE_URL}/files/path{wsgi_path}", headers=headers, files={'content': seed_wsgi})
print(f"WSGI upload status: {r_up.status_code}")

print(">>> 3. Reloading webapp to execute seed...")
r_reload = requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=headers)
print(f"Reload status: {r_reload.status_code}")
time.sleep(3)

print(">>> 4. Triggering WSGI request...")
try:
    requests.get(f"https://{DOMAIN}/api/employees/", timeout=15)
except Exception as e:
    print("Trigger error (expected during worker restart):", e)

time.sleep(3)

print(">>> 5. Checking seed output status...")
r_status = requests.get(f"{BASE_URL}/files/path/home/erpUMA/seed_status.txt", headers=headers)
print(f"Seed status file ({r_status.status_code}):\n{r_status.text}")

print(">>> 6. Restoring clean WSGI...")
requests.post(f"{BASE_URL}/files/path{wsgi_path}", headers=headers, files={'content': clean_wsgi})
requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=headers)
time.sleep(3)

print(">>> 7. Verifying /api/employees/ live...")
r_emp = requests.get(f"https://{DOMAIN}/api/employees/", timeout=15)
print(f"Employees response ({r_emp.status_code}):")
if r_emp.status_code == 200:
    for u in r_emp.json():
        print(f"  {u.get('id')}: {u.get('name')} | roleType={u.get('roleType')} | role={u.get('role')} | dataScope={u.get('dataScope')}")
