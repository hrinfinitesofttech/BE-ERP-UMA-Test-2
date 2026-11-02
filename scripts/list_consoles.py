import os
import requests
API_TOKEN = os.environ.get('PA_API_TOKEN', '')
USERNAME = 'erpUMA'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}
r = requests.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", headers=HEADERS)
print("Consoles:", r.json())
