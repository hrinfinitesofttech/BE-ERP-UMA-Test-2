import os
import requests
API_TOKEN = os.environ.get('PA_API_TOKEN', '')
USERNAME = 'erpUMA'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}
cid = 48766275
r_out = requests.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{cid}/get_latest_output/", headers=HEADERS)
print("Output:\n", r_out.json().get('output'))
