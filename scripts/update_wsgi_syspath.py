import requests
import time

API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
DOMAIN = 'erpUMA.pythonanywhere.com'
BASE_URL = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}
WSGI_PATH = '/var/www/erpuma_pythonanywhere_com_wsgi.py'

updated_wsgi = """import os
import sys

path = '/home/erpUMA/BE-ERP-UMA'
if path not in sys.path:
    sys.path.append(path)

global_pkgs = '/usr/local/lib/python3.10/dist-packages'
if global_pkgs not in sys.path:
    sys.path.append(global_pkgs)

os.environ['DJANGO_SETTINGS_MODULE'] = 'erp_backend.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"""

r1 = requests.post(f"{BASE_URL}/files/path{WSGI_PATH}", headers=HEADERS, files={'content': updated_wsgi.encode('utf-8')})
print("Upload WSGI status:", r1.status_code)

r2 = requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=HEADERS)
print("Reload status:", r2.status_code)
time.sleep(3)

# Test PDF endpoint now!
r_pdf = requests.get(f"https://{DOMAIN}/api/quotations/QT-2026-0143/pdf/", timeout=20)
print("PDF endpoint status:", r_pdf.status_code)
print("PDF length:", len(r_pdf.content))
if r_pdf.status_code == 200:
    print("[SUCCESS] PDF GENERATED PROPERLY!")
else:
    print(r_pdf.text[:300])
