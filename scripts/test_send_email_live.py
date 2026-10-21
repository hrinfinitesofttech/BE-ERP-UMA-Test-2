import requests

url = "https://erpuma.pythonanywhere.com/api/quotations/QT-2026-0143/send-email/"
payload = {
    "recipientEmail": "rinkaljadav11@gmail.com",
}

r = requests.post(url, json=payload, timeout=30)
print("Status code:", r.status_code)
print("Response text:", r.text)
