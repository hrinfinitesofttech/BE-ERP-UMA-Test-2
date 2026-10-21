import requests
API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}
cid = 48766275
r_out = requests.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{cid}/get_latest_output/", headers=HEADERS)
print("Output:\n", r_out.json().get('output'))
