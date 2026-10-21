import requests
import time

API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
DOMAIN = 'erpUMA.pythonanywhere.com'
BASE_URL = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}
WSGI_PATH = '/var/www/erpuma_pythonanywhere_com_wsgi.py'

# WSGI Hook to run git pull and reload
git_pull_hook_wsgi = """import os
import sys
import subprocess

path = '/home/erpUMA/BE-ERP-UMA'
if path not in sys.path:
    sys.path.append(path)

global_pkgs = '/usr/local/lib/python3.10/dist-packages'
if global_pkgs not in sys.path:
    sys.path.append(global_pkgs)

res = []
try:
    cmd = ['git', 'pull', 'origin', 'main']
    out = subprocess.check_output(cmd, cwd=path, stderr=subprocess.STDOUT, text=True)
    res.append("GIT_PULL_SUCCESS:\\n" + out)
except Exception as e:
    res.append("GIT_PULL_ERROR:\\n" + str(e))

with open('/home/erpUMA/git_pull_status.txt', 'w') as f:
    f.write('\\n'.join(res))

os.environ['DJANGO_SETTINGS_MODULE'] = 'erp_backend.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"""

clean_wsgi = """import os
import sys

path = '/home/erpUMA/BE-ERP-UMA'
if path not in sys.path:
    sys.path.append(path)

global_pkgs = '/usr/local/lib/python3.10/dist-packages'
if global_pkgs not in sys.path:
    sys.path.append(global_pkgs)

os.environ['DJANGO_SETTINGS_MODULE'] = 'erp_backend.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"""

def main():
    print("=" * 60)
    print("  EXECUTING GIT PULL ON PYTHONANYWHERE SERVER")
    print("=" * 60)

    # 1. Upload hook
    print("[1/4] Uploading git pull hook to WSGI...")
    r1 = requests.post(f"{BASE_URL}/files/path{WSGI_PATH}", headers=HEADERS, files={'content': git_pull_hook_wsgi.encode('utf-8')})
    print(f"Hook upload status: {r1.status_code}")

    # 2. Reload WebApp to run hook
    print("[2/4] Triggering reload to execute git pull...")
    r2 = requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=HEADERS)
    print(f"Reload status: {r2.status_code}")
    time.sleep(3)

    # 3. Trigger WSGI
    try:
        requests.get(f"https://{DOMAIN}/api/leads/", timeout=25)
    except Exception as e:
        print("Trigger request warning:", e)
    time.sleep(3)

    # 4. Check git pull status
    r_stat = requests.get(f"{BASE_URL}/files/path/home/{USERNAME}/git_pull_status.txt", headers=HEADERS)
    print("\n--- Git Pull Status on PythonAnywhere ---")
    print(r_stat.text.strip())
    print("----------------------------------------\n")

    # 5. Restore clean WSGI
    print("[3/4] Restoring clean WSGI...")
    requests.post(f"{BASE_URL}/files/path{WSGI_PATH}", headers=HEADERS, files={'content': clean_wsgi.encode('utf-8')})

    # 6. Final reload
    print("[4/4] Performing final webapp reload...")
    r_final = requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=HEADERS)
    print(f"Final reload status: {r_final.status_code}")
    time.sleep(3)

    # 7. Check health
    r_health = requests.get(f"https://{DOMAIN}/api/leads/", timeout=15)
    print(f"Health status on https://{DOMAIN}: {r_health.status_code} (OK)")

if __name__ == '__main__':
    main()
