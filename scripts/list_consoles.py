import requests
API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}
r = requests.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", headers=HEADERS)
print("Consoles:", r.json())
