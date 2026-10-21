import os
import requests
import time

API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
DOMAIN = 'erpUMA.pythonanywhere.com'
BASE_URL = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}

LOCAL_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES_TO_DEPLOY = [
    'apps/crm/quotation_pdf.py',
    'apps/crm/views.py',
    'apps/crm/serializers.py',
    'apps/production/views.py',
]

def upload_file(rel_path):
    local_path = os.path.join(LOCAL_BASE, rel_path.replace('/', os.sep))
    if not os.path.exists(local_path):
        print(f"[FAIL] Local file not found: {local_path}")
        return False

    with open(local_path, 'rb') as f:
        content = f.read()

    remote_path = f"/home/{USERNAME}/BE-ERP-UMA/{rel_path}"
    upload_url = f"{BASE_URL}/files/path{remote_path}"

    for attempt in range(5):
        try:
            r = requests.post(upload_url, files={'content': content}, headers=HEADERS, timeout=30)
            if r.status_code in [200, 201]:
                print(f"[OK] Uploaded {rel_path} ({r.status_code})")
                return True
            elif r.status_code == 429:
                time.sleep(3)
            else:
                print(f"[FAIL] {rel_path} -> {r.status_code}: {r.text[:80]}")
                return False
        except Exception as e:
            time.sleep(2)
    return False

def main():
    print("=" * 60)
    print(f"  DEPLOYING FIXES TO PYTHONANYWHERE ({USERNAME})")
    print("=" * 60)

    for f in FILES_TO_DEPLOY:
        upload_file(f)
        time.sleep(0.5)

    print("\nReloading WebApp...")
    r_reload = requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=HEADERS, timeout=25)
    print(f"Reload status: {r_reload.status_code}")
    time.sleep(3)

    print("\nVerifying live API health...")
    r_health = requests.get(f"https://{DOMAIN}/api/leads/", timeout=15)
    print(f"Leads API status: {r_health.status_code}")

if __name__ == '__main__':
    main()
