import requests
import time

API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
DOMAIN = 'erpUMA.pythonanywhere.com'
BASE_URL = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}
WSGI_PATH = '/var/www/erpuma_pythonanywhere_com_wsgi.py'

hook_wsgi = """import os
import sys
import subprocess

path = '/home/erpUMA/BE-ERP-UMA'
if path not in sys.path:
    sys.path.append(path)

try:
    cmd = [sys.executable, '-m', 'pip', 'install', 'reportlab']
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
    with open('/home/erpUMA/pip_status.txt', 'w') as f:
        f.write('PIP_SUCCESS:\\n' + out)
except Exception as e:
    with open('/home/erpUMA/pip_status.txt', 'w') as f:
        f.write('PIP_ERROR:\\n' + str(e))

os.environ['DJANGO_SETTINGS_MODULE'] = 'erp_backend.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"""

clean_wsgi = """import os
import sys

path = '/home/erpUMA/BE-ERP-UMA'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'erp_backend.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"""

def main():
    print("[1/4] Placing pip install hook in WSGI...")
    r1 = requests.post(f"{BASE_URL}/files/path{WSGI_PATH}", headers=HEADERS, files={'content': hook_wsgi.encode('utf-8')})
    print("Hook upload status:", r1.status_code)

    print("[2/4] Triggering reload...")
    r2 = requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=HEADERS)
    print("Reload status:", r2.status_code)
    time.sleep(3)

    # Hit endpoint to invoke WSGI
    print("[3/4] Hitting endpoint to trigger WSGI startup...")
    try:
        requests.get(f"https://{DOMAIN}/api/leads/", timeout=25)
    except Exception as e:
        print("Hit warning:", e)
    time.sleep(3)

    # Check status
    r_stat = requests.get(f"{BASE_URL}/files/path/home/{USERNAME}/pip_status.txt", headers=HEADERS)
    print("Pip result:\n", r_stat.text)

    # Restore clean WSGI
    print("[4/4] Restoring clean WSGI...")
    requests.post(f"{BASE_URL}/files/path{WSGI_PATH}", headers=HEADERS, files={'content': clean_wsgi.encode('utf-8')})
    requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=HEADERS)
    print("Clean WSGI restored and webapp reloaded!")

if __name__ == '__main__':
    main()
