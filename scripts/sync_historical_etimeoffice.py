import os
import sys
import json
import base64
import urllib.request
from datetime import datetime, date, timedelta
import sqlite3

CORP_ID = 'UMATECHNOFAB'
USERNAME = 'UMATECHNOFAB'
PASSWORD = 'KPS@0102'

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'db.sqlite3')

def fetch_inout_data(from_date_str, to_date_str):
    auth_str = f"{CORP_ID}:{USERNAME}:{PASSWORD}:true"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    url = f"https://api.etimeoffice.com/api/DownloadInOutPunchData?Empcode=ALL&FromDate={from_date_str}&ToDate={to_date_str}"
    headers = {
        'Authorization': f'Basic {b64_auth}',
        'User-Agent': 'Mozilla/5.0'
    }
    req = urllib.request.Request(url, headers=headers)
    print(f"Fetching from eTimeOffice: {from_date_str} to {to_date_str}...")
    with urllib.request.urlopen(req, timeout=45) as resp:
        content = resp.read().decode('utf-8')
        data = json.loads(content)
        if data.get('Error'):
            raise Exception(f"eTimeOffice API returned error: {data.get('Msg')}")
        return data.get('InOutPunchData', [])

def run_sync():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Fetch all active Users to create mapping lookup
    cur.execute("SELECT id, username, first_name, last_name, department_name FROM authentication_user WHERE is_active=1")
    users = cur.fetchall()
    print(f"Active Users in DB: {len(users)}")
    user_by_id = {u[0]: u for u in users}

    # Fetch existing mappings
    cur.execute("SELECT machine_emp_code, employee_id FROM hr_biometricemployeemapping WHERE is_active=1")
    mapping_by_code = {m[0]: m[1] for m in cur.fetchall()}

    # Helper to resolve employee_id
    def resolve_emp_id(code, name):
        code_str = str(code).strip()
        # Direct mapping
        if code_str in mapping_by_code:
            return mapping_by_code[code_str]
        # Direct ID
        if code_str in user_by_id:
            return code_str
        # EMP-code
        if f"EMP-{code_str}" in user_by_id:
            return f"EMP-{code_str}"
        # Numeric normalized
        try:
            num = int(code_str)
            for cand in [f"EMP-{num:04d}", f"EMP-{num:03d}", f"EMP-{num:05d}", f"EMP-{num}"]:
                if cand in user_by_id:
                    return cand
        except ValueError:
            pass
        return None

    # Fetch date ranges: September 2026, October 2026, November 2026
    ranges = [
        ('01/09/2026', '30/09/2026'),
        ('01/10/2026', '31/10/2026'),
        ('01/11/2026', '19/11/2026'),
    ]

    total_synced = 0
    total_present = 0

    for f_date, t_date in ranges:
        records = fetch_inout_data(f_date, t_date)
        print(f"  Received {len(records)} records for range {f_date} - {t_date}")

        for r in records:
            emp_code = str(r.get('Empcode') or '').strip()
            raw_name = str(r.get('Name') or '').strip()
            date_str = str(r.get('DateString') or '').strip()

            if not emp_code or not date_str:
                continue

            try:
                dt = datetime.strptime(date_str, '%d/%m/%Y').date()
                iso_date = dt.strftime('%Y-%m-%d')
            except Exception:
                continue

            emp_id = resolve_emp_id(emp_code, raw_name)
            if not emp_id:
                # Fallback to EMP-{emp_code}
                emp_id = f"EMP-{emp_code}"

            user_info = user_by_id.get(emp_id)
            emp_display_name = raw_name
            dept = 'Production & Operations'
            if user_info:
                fname = user_info[2] or ''
                lname = user_info[3] or ''
                emp_display_name = f"{fname} {lname}".strip() or user_info[1] or raw_name
                dept = user_info[4] or 'Production & Operations'

            in_time = str(r.get('INTime') or '').strip()
            out_time = str(r.get('OUTTime') or '').strip()
            clean_in = in_time if in_time and in_time != '--:--' else ''
            clean_out = out_time if out_time and out_time != '--:--' else ''

            work_time = str(r.get('WorkTime') or '00:00').strip()
            over_time = str(r.get('OverTime') or '00:00').strip()
            late_in = str(r.get('Late_In') or '00:00').strip()
            status_char = str(r.get('Status') or 'A').strip().upper()

            total_hours = 0.0
            if work_time and work_time != '00:00':
                try:
                    h, m = map(int, work_time.split(':'))
                    total_hours = round(h + m / 60.0, 2)
                except Exception:
                    pass

            overtime_hours = 0.0
            if over_time and over_time != '00:00':
                try:
                    h, m = map(int, over_time.split(':'))
                    overtime_hours = round(h + m / 60.0, 2)
                except Exception:
                    pass

            late_mins = 0
            if late_in and late_in != '00:00':
                try:
                    h, m = map(int, late_in.split(':'))
                    late_mins = h * 60 + m
                except Exception:
                    pass

            # Determine Attendance Status
            if status_char == 'P' or clean_in or clean_out:
                if late_mins > 0:
                    att_status = 'Late'
                else:
                    att_status = 'Present'
            elif status_char == 'WO' or dt.weekday() == 6:
                att_status = 'Weekly Off'
            elif status_char == 'H':
                att_status = 'Holiday'
            elif status_char == 'HD':
                att_status = 'Half Day'
            elif status_char == 'L':
                att_status = 'On Leave'
            else:
                att_status = 'Absent'

            punch_count = 2 if clean_in and clean_out else (1 if clean_in or clean_out else 0)
            is_missing = 1 if clean_in and not clean_out else 0
            remarks = str(r.get('Remark') or '').strip()
            if remarks == '--': remarks = ''

            # Upsert into hr_attendancerecord
            rec_id = f"ATT-{emp_id}-{iso_date}"
            cur.execute("""
                INSERT INTO hr_attendancerecord (
                    id, employee_id, employee_name, department, date, shift_name,
                    check_in, check_out, first_in, last_out, punch_count, total_hours,
                    late_minutes, early_checkout_minutes, overtime_hours, status,
                    source, is_manually_approved, is_missing_punch, remarks
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(employee_id, date) DO UPDATE SET
                    employee_name=excluded.employee_name,
                    department=excluded.department,
                    check_in=CASE WHEN excluded.check_in != '' THEN excluded.check_in ELSE hr_attendancerecord.check_in END,
                    check_out=CASE WHEN excluded.check_out != '' THEN excluded.check_out ELSE hr_attendancerecord.check_out END,
                    first_in=CASE WHEN excluded.first_in != '' THEN excluded.first_in ELSE hr_attendancerecord.first_in END,
                    last_out=CASE WHEN excluded.last_out != '' THEN excluded.last_out ELSE hr_attendancerecord.last_out END,
                    punch_count=excluded.punch_count,
                    total_hours=excluded.total_hours,
                    late_minutes=excluded.late_minutes,
                    overtime_hours=excluded.overtime_hours,
                    status=excluded.status,
                    source='eTimeOffice Machine',
                    is_missing_punch=excluded.is_missing_punch,
                    remarks=excluded.remarks
            """, (
                rec_id, emp_id, emp_display_name, dept, iso_date,
                'General Office & Technical Shift',
                clean_in, clean_out, clean_in, clean_out,
                punch_count, total_hours, late_mins, 0, overtime_hours,
                att_status, 'eTimeOffice Machine', 0, is_missing, remarks
            ))

            total_synced += 1
            if punch_count > 0:
                total_present += 1

    conn.commit()
    conn.close()

    print(f"\n==========================================")
    print(f"SYNC COMPLETED SUCCESSFULLY!")
    print(f"Total Records Processed: {total_synced}")
    print(f"Total Punch Days (Present/Late): {total_present}")
    print(f"==========================================")

if __name__ == '__main__':
    run_sync()
