import requests
import time

API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}

# Create a fresh bash console
r = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", json={'executable': 'bash'}, headers=HEADERS)
print("Create console:", r.status_code)
cid = r.json()['id']
print("Console ID:", cid)
time.sleep(3)

# Send pip install reportlab command
cmd = "/home/erpUMA/.virtualenvs/erp-venv/bin/pip install reportlab\n"
r2 = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{cid}/send_input/", json={'input': cmd}, headers=HEADERS)
print("Send command status:", r2.status_code)

for i in range(8):
    time.sleep(4)
    r_out = requests.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{cid}/get_latest_output/", headers=HEADERS)
    out = r_out.json().get('output', '')
    print(f"[{i*4}s] Output: {out[-300:] if out else 'None'}")
    if "Successfully installed" in out or "Requirement already satisfied" in out:
        print("[SUCCESS] ReportLab installed!")
        break
