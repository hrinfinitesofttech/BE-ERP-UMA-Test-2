import requests

API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}

# Check cpu / tier
r = requests.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/cpu/", headers=HEADERS)
print("CPU Info:", r.status_code, r.text)

# Check consoles
r_con = requests.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", headers=HEADERS)
print("Consoles:", r_con.status_code, r_con.text[:200])
