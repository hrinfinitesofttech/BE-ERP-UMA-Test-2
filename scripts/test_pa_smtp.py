import requests

API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}

# Let's upload a test script to /home/erpUMA/test_email.py
script = """
import smtplib
try:
    s = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
    s.starttls()
    print("SMTP connection OK!")
except Exception as e:
    print("SMTP error:", type(e), e)
"""

upload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/erpUMA/test_email.py"
r = requests.post(upload_url, files={'content': script.encode('utf-8')}, headers=HEADERS)
print("Upload test_email.py:", r.status_code)

# Send input to console 48738994
console_id = 48738994
send_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/"
r2 = requests.post(send_url, json={'input': 'python3 /home/erpUMA/test_email.py\n'}, headers=HEADERS)
print("Sent command to console:", r2.status_code)

import time
time.sleep(3)
get_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/get_latest_output/"
r3 = requests.get(get_url, headers=HEADERS)
print("Console output:\n", r3.json().get('output', ''))
