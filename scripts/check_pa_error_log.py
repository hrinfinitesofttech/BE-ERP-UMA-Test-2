import requests

usernames = ['erpuma', 'umaERP']
passwords = ['AAaa@123456@']

for user in usernames:
    session = requests.Session()
    login_url = 'https://www.pythonanywhere.com/login/'
    r_login_page = session.get(login_url)
    csrf = session.cookies.get('csrftoken')
    login_data = {
        'auth-username': user,
        'auth-password': 'AAaa@123456@',
        'login_view-current_step': 'auth',
        'csrfmiddlewaretoken': csrf
    }
    r_login = session.post(login_url, data=login_data, headers={'Referer': login_url})
    print(f"User {user}: login status {r_login.status_code}")
    if r_login.status_code == 200:
        csrf_token = session.cookies.get('csrftoken')
        headers = {'X-CSRFToken': csrf_token, 'Referer': 'https://www.pythonanywhere.com/'}
        # Check error log
        for domain in [f"{user}.pythonanywhere.com", f"{user.lower()}.pythonanywhere.com"]:
            log_url = f"https://www.pythonanywhere.com/api/v0/user/{user}/files/path/var/log/{domain}.error.log"
            r_log = session.get(log_url, headers=headers)
            print(f"Log {domain}: status {r_log.status_code}")
            if r_log.status_code == 200:
                lines = r_log.text.strip().split('\n')
                print(f"=== Last 30 lines of {domain}.error.log ===")
                print('\n'.join(lines[-30:]))
