import requests
import time

USERNAME = 'umaERP'
PASSWORD = 'AAaa@123456@'
DOMAIN = 'umaERP.pythonanywhere.com'

session = requests.Session()
login_url = 'https://www.pythonanywhere.com/login/'
r_login_page = session.get(login_url)
csrf = session.cookies.get('csrftoken')
login_data = {
    'auth-username': USERNAME,
    'auth-password': PASSWORD,
    'login_view-current_step': 'auth',
    'csrfmiddlewaretoken': csrf
}
r_login = session.post(login_url, data=login_data, headers={'Referer': login_url})
csrf_token = session.cookies.get('csrftoken')
headers = {'X-CSRFToken': csrf_token, 'Referer': f'https://www.pythonanywhere.com/user/{USERNAME}/consoles/'}

# Check wsgi file path
wsgi_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/"
r_webapp = session.get(wsgi_url, headers=headers)
print("Webapp info:", r_webapp.json())
wsgi_path = r_webapp.json().get('user_wsgi_file_path')

# Read wsgi file
r_file = session.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{wsgi_path}", headers=headers)
original_wsgi = r_file.text
print("Original WSGI:\n", original_wsgi[:300])

# Append migrate command to WSGI so it runs on webapp reload
migrate_code = """
try:
    from django.core.management import call_command
    call_command('migrate')
    print("Auto-migration successful on webapp reload!")
except Exception as e:
    print("Auto-migration error:", e)
"""

if "call_command('migrate')" not in original_wsgi:
    new_wsgi = original_wsgi + "\n" + migrate_code
    # Upload updated wsgi file
    r_up = session.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{wsgi_path}", files={"content": new_wsgi}, headers=headers)
    print("WSGI file update status:", r_up.status_code)

# Reload webapp
reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
r_reload = session.post(reload_url, headers=headers)
print("Reload status:", r_reload.status_code)

# Test APIs
time.sleep(5)
for ep in ['/api/designer/jobs/', '/api/hr/transfers/', '/api/hr/documents/', '/api/hr/onboarding/']:
    r = requests.get(f"https://{DOMAIN}{ep}")
    print(f"{ep} -> Status: {r.status_code}")
