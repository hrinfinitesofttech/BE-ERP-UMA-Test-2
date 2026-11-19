import os
import json
import base64
import urllib.request
from datetime import datetime
import sqlite3

CORP_ID = 'UMATECHNOFAB'
USERNAME = 'UMATECHNOFAB'
PASSWORD = 'KPS@0102'

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'db.sqlite3')

def run_punchlog_sync():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # User lookup
    cur.execute("SELECT id, username, first_name, last_name FROM authentication_user WHERE is_active=1")
    users = cur.fetchall()
    user_by_id = {u[0]: u for u in users}

    cur.execute("SELECT machine_emp_code, employee_id FROM hr_biometricemployeemapping WHERE is_active=1")
    mapping_by_code = {m[0]: m[1] for m in cur.fetchall()}

    def resolve_emp_id(code):
        code_str = str(code).strip()
        if code_str in mapping_by_code:
            return mapping_by_code[code_str]
        if code_str in user_by_id:
            return code_str
        if f"EMP-{code_str}" in user_by_id:
            return f"EMP-{code_str}"
        try:
            num = int(code_str)
            for cand in [f"EMP-{num:04d}", f"EMP-{num:03d}", f"EMP-{num:05d}", f"EMP-{num}"]:
                if cand in user_by_id:
                    return cand
        except ValueError:
            pass
        return f"EMP-{code_str}"

    auth_str = f"{CORP_ID}:{USERNAME}:{PASSWORD}:true"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    headers = {'Authorization': f'Basic {b64_auth}', 'User-Agent': 'Mozilla/5.0'}

    ranges = [
        ('01/09/2026_00:00', '30/09/2026_23:59'),
        ('01/10/2026_00:00', '31/10/2026_23:59'),
        ('01/11/2026_00:00', '19/11/2026_23:59'),
    ]

    total_inserted = 0

    for f_date, t_date in ranges:
        url = f"https://api.etimeoffice.com/api/DownloadPunchDataMCID?Empcode=ALL&FromDate={f_date}&ToDate={t_date}"
        print(f"Fetching raw punches: {f_date} to {t_date}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                punches = data.get('PunchData', [])
                print(f"  Got {len(punches)} raw punch logs.")

                for p in punches:
                    emp_code = str(p.get('Empcode') or '').strip()
                    emp_name = str(p.get('Name') or '').strip()
                    p_date_str = str(p.get('PunchDate') or '').strip()
                    mcid = str(p.get('mcid') or '1').strip()

                    if not emp_code or not p_date_str:
                        continue

                    try:
                        # 18/11/2026 20:03:00
                        p_dt = datetime.strptime(p_date_str, '%d/%m/%Y %H:%M:%S')
                    except Exception:
                        continue

                    iso_dt_str = p_dt.strftime('%Y-%m-%d %H:%M:%S')
                    iso_date = p_dt.strftime('%Y-%m-%d')
                    emp_id = resolve_emp_id(emp_code)

                    log_id = f"PL-{emp_code}-{p_dt.strftime('%Y%m%d%H%M%S')}"

                    cur.execute("""
                        INSERT OR IGNORE INTO hr_punchlog (
                            id, emp_code, emp_name, punch_datetime, machine_id,
                            m_flag, emp_card_no, source_table, raw_record_id,
                            synced_to_attendance, sync_error, created_at,
                            erp_employee_id, is_mapped, punch_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?)
                    """, (
                        log_id, emp_code, emp_name, iso_dt_str, mcid,
                        'IN', '', 'DownloadPunchDataMCID', '',
                        1, '', emp_id, 1, iso_date
                    ))
                    total_inserted += 1

        except Exception as e:
            print(f"Error fetching raw punches for range {f_date}-{t_date}: {e}")

    conn.commit()
    conn.close()
    print(f"Total Raw PunchLogs Processed: {total_inserted}")

if __name__ == '__main__':
    run_punchlog_sync()
