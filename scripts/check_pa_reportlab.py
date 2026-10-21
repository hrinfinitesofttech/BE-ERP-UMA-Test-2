import requests

API_TOKEN = 'e023a655a10e258afcd2b8ff184bdc339fd4c30a'
USERNAME = 'erpUMA'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}

# Check if reportlab exists in virtualenv
check_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/erpUMA/.virtualenvs/erp-venv/lib/python3.10/site-packages/reportlab/__init__.py"
r = requests.get(check_url, headers=HEADERS)
print(f"Reportlab in venv status: {r.status_code}")

# Check quotation_pdf.py on erpUMA
pdf_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/erpUMA/BE-ERP-UMA/apps/crm/quotation_pdf.py"
r_pdf = requests.get(pdf_url, headers=HEADERS)
print(f"quotation_pdf.py on erpUMA status: {r_pdf.status_code}")
