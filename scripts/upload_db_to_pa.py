import os
import requests
import time

token = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
username = 'erpUMA'
headers = {'Authorization': f'Token {token}'}

local_db = r'd:\UMA ERP Test 3\BE-ERP-UMA-Test-2\db.sqlite3'
remote_path = f'/home/{username}/BE-ERP-UMA/db.sqlite3'

print(f"Uploading db.sqlite3 ({os.path.getsize(local_db) / (1024*1024):.2f} MB) to PythonAnywhere...")
with open(local_db, 'rb') as f:
    content = f.read()

upload_url = f'https://www.pythonanywhere.com/api/v0/user/{username}/files/path{remote_path}'
r = requests.post(upload_url, files={'content': content}, headers=headers)
print(f"Upload status: {r.status_code}")

if r.status_code in [200, 201]:
    print("Database uploaded successfully!")
    print("Reloading PythonAnywhere webapp...")
    reload_url = f'https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{username.lower()}.pythonanywhere.com/reload/'
    r_reload = requests.post(reload_url, headers=headers)
    print(f"Reload status: {r_reload.status_code}")
else:
    print(f"Upload failed: {r.status_code} - {r.text[:200]}")
