import os
import requests
import time

token = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
username = 'erpUMA'
headers = {'Authorization': f'Token {token}'}

base_dir = r'D:\UMA ERP Test 3\BE-ERP-UMA-Test-2'

files_to_upload = [
    (r'apps\store\views.py', f'/home/{username}/BE-ERP-UMA/apps/store/views.py'),
    (r'db.sqlite3', f'/home/{username}/BE-ERP-UMA/db.sqlite3'),
]

for local_rel, remote_path in files_to_upload:
    local_path = os.path.join(base_dir, local_rel)
    size_mb = os.path.getsize(local_path) / (1024 * 1024)
    print(f"Uploading {local_rel} ({size_mb:.2f} MB) -> {remote_path}...")
    with open(local_path, 'rb') as f:
        content = f.read()

    upload_url = f'https://www.pythonanywhere.com/api/v0/user/{username}/files/path{remote_path}'
    r = requests.post(upload_url, files={'content': content}, headers=headers, timeout=120)
    print(f"  Result: {r.status_code}")
    if r.status_code not in [200, 201]:
        print(f"  Error: {r.text[:300]}")
    time.sleep(2)

print("\nReloading PythonAnywhere webapp...")
reload_url = f'https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{username.lower()}.pythonanywhere.com/reload/'
r_reload = requests.post(reload_url, headers=headers, timeout=30)
print(f"Reload status: {r_reload.status_code}")
if r_reload.status_code == 200:
    print("WebApp successfully reloaded!")
else:
    print(f"Reload response: {r_reload.text[:200]}")

time.sleep(3)
print("\nVerifying live endpoints...")
try:
    r_cat = requests.get('https://erpuma.pythonanywhere.com/api/item-categories/', timeout=15)
    print(f"Item Categories live API: {r_cat.status_code}, count: {len(r_cat.json()) if r_cat.status_code == 200 else 'N/A'}")
except Exception as e:
    print(f"Error checking categories: {e}")

try:
    r_uom = requests.get('https://erpuma.pythonanywhere.com/api/uoms/', timeout=15)
    print(f"UOMs live API: {r_uom.status_code}, count: {len(r_uom.json()) if r_uom.status_code == 200 else 'N/A'}")
except Exception as e:
    print(f"Error checking UOMs: {e}")

try:
    r_items = requests.get('https://erpuma.pythonanywhere.com/api/items/', timeout=15)
    print(f"Items live API: {r_items.status_code}, count: {len(r_items.json()) if r_items.status_code == 200 else 'N/A'}")
except Exception as e:
    print(f"Error checking items: {e}")
