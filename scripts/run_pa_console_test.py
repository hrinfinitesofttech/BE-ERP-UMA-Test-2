import requests
import time

API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}

# Create a new bash console
r = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", json={'executable': 'bash'}, headers=HEADERS)
print("Create console:", r.status_code, r.text)
if r.status_code == 201:
    cid = r.json()['id']
    time.sleep(2)
    # run test_email.py
    requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{cid}/send_input/", json={'input': 'python3 /home/erpUMA/test_email.py\n'}, headers=HEADERS)
    time.sleep(4)
    r_out = requests.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{cid}/get_latest_output/", headers=HEADERS)
    print("Output:\n", r_out.json().get('output'))
