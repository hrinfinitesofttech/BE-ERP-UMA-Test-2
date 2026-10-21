import requests

r = requests.get("https://erpuma.pythonanywhere.com/api/quotations/QT-2026-0143/pdf/", timeout=20)
print("PDF endpoint status:", r.status_code)
print("Content-Type:", r.headers.get('Content-Type'))
print("Content-Length:", len(r.content))
if r.status_code != 200:
    print("Content:", r.text[:200])
