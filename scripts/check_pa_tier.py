import os
import requests

API_TOKEN = os.environ.get('PA_API_TOKEN', '')
USERNAME = 'erpUMA'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}

# Check cpu / tier
r = requests.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/cpu/", headers=HEADERS)
print("CPU Info:", r.status_code, r.text)

# Check consoles
r_con = requests.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", headers=HEADERS)
print("Consoles:", r_con.status_code, r_con.text[:200])
