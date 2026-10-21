import requests

API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}

# Check if reportlab exists anywhere in python 3.10
urls = [
    f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/usr/lib/python3/dist-packages/reportlab/__init__.py",
    f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/usr/local/lib/python3.10/dist-packages/reportlab/__init__.py",
    f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/erpUMA/.local/lib/python3.10/site-packages/reportlab/__init__.py",
]
for u in urls:
    r = requests.get(u, headers=HEADERS)
    print(u.split('path')[-1], r.status_code)
