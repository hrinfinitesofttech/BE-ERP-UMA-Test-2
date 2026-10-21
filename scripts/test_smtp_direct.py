import requests
import time

API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}

script = """
import os, sys, smtplib

res = []
try:
    import reportlab
    res.append(f"Reportlab: {reportlab.__version__}")
except Exception as e:
    res.append(f"Reportlab import error: {e}")

try:
    s = smtplib.SMTP('smtp.gmail.com', 587, timeout=7)
    s.starttls()
    res.append("SMTP connect: SUCCESS")
    s.quit()
except Exception as e:
    res.append(f"SMTP connect error: {type(e).__name__} - {e}")

with open('/home/erpUMA/smtp_test_result.txt', 'w') as f:
    f.write('\\n'.join(res))
"""

upload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/erpUMA/smtp_test.py"
requests.post(upload_url, files={'content': script.encode('utf-8')}, headers=HEADERS)

cid = 48766275
requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{cid}/send_input/", json={'input': '/home/erpUMA/.virtualenvs/erp-venv/bin/python /home/erpUMA/smtp_test.py\n'}, headers=HEADERS)

time.sleep(8)

res_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/erpUMA/smtp_test_result.txt"
r_res = requests.get(res_url, headers=HEADERS)
print("Status:", r_res.status_code)
if r_res.status_code == 200:
    print("RESULT:\n", r_res.text)
