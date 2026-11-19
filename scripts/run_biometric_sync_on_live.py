import os
import sys
import logging
from datetime import date, timedelta, datetime
import json
import base64
import urllib.request

logger = logging.getLogger(__name__)

def run_sync():
    log_lines = []
    try:
        from apps.authentication.models import User
        from apps.hr.models import PunchMachineConfig, BiometricEmployeeMapping, AttendanceRecord, ShiftMaster, PunchLog

        cfg, _ = PunchMachineConfig.objects.get_or_create(id=1)
        cfg.corporate_id = 'UMATECHNOFAB'
        cfg.username = 'UMATECHNOFAB'
        cfg.password = 'KPS@0102'
        cfg.base_url = 'https://api.etimeoffice.com/api'
        cfg.is_active = True
        cfg.save()
        log_lines.append(f"PunchMachineConfig updated: {cfg.corporate_id} / {cfg.username}")

        # Fetch live machine data using urllib
        corp_id = cfg.corporate_id
        uname = cfg.username
        pwd = cfg.password
        base_url = cfg.base_url

        auth_plain = f"{corp_id}:{uname}:{pwd}:true"
        b64_auth = base64.b64encode(auth_plain.encode()).decode()

        today = date.today()
        from_str = (today - timedelta(days=45)).strftime('%d/%m/%Y')
        to_str = today.strftime('%d/%m/%Y')

        url = f"{base_url}/DownloadInOutPunchData?Empcode=ALL&FromDate={from_str}&ToDate={to_str}"
        req = urllib.request.Request(url, headers={'Authorization': f"Basic {b64_auth}"})
        
        with urllib.request.urlopen(req, timeout=30) as response:
            raw_data = response.read().decode('utf-8')
            data = json.loads(raw_data)

        inout_records = data.get('InOutPunchData', [])
        log_lines.append(f"Fetched {len(inout_records)} punch records from eTimeOffice.")

        emp_map = {}
        for rec in inout_records:
            c = str(rec.get('Empcode', '')).strip()
            n = str(rec.get('Name', '')).strip()
            if c and c not in emp_map:
                emp_map[c] = n

        log_lines.append(f"Identified {len(emp_map)} unique employees from machine.")

        created_users = 0
        updated_users = 0
        for code, full_name in emp_map.items():
            parts = full_name.split()
            fname = parts[0] if parts else 'Staff'
            lname = ' '.join(parts[1:]) if len(parts) > 1 else ''

            emp_id = f"EMP-{code}"
            user = User.objects.filter(id=emp_id).first() or User.objects.filter(id=code).first()
            if not user:
                user = User(
                    id=emp_id,
                    username=f"user_{code}",
                    first_name=fname,
                    last_name=lname,
                    department_name='Production & Operations',
                    designation='Machine Staff',
                    is_active=True
                )
                user.set_password('admin123')
                user.save()
                created_users += 1
            else:
                user.first_name = fname
                user.last_name = lname
                user.is_active = True
                user.save()
                updated_users += 1

            BiometricEmployeeMapping.objects.update_or_create(
                machine_emp_code=code,
                defaults={
                    'employee': user,
                    'employee_code': user.id,
                    'employee_name': user.name,
                    'is_active': True,
                    'notes': 'Imported from eTimeOffice Machine'
                }
            )

        log_lines.append(f"Users created: {created_users}, updated: {updated_users}. Total mappings: {BiometricEmployeeMapping.objects.count()}")

        mapping_dict = {m.machine_emp_code: m.employee for m in BiometricEmployeeMapping.objects.select_related('employee').all()}
        shift = ShiftMaster.objects.filter(status='Active').first()
        shift_title = shift.shift_name if shift else 'Factory General Shift'

        att_created = 0
        att_updated = 0

        for rec in inout_records:
            emp_code = str(rec.get('Empcode', '')).strip()
            name = str(rec.get('Name', '')).strip()
            date_str = rec.get('DateString', '')
            in_time = rec.get('INTime', '')
            out_time = rec.get('OUTTime', '')
            work_time = rec.get('WorkTime', '00:00')
            over_time = rec.get('OverTime', '00:00')
            late_in = rec.get('Late_In', '00:00')
            status_code = rec.get('Status', 'A')
            remark = rec.get('Remark', '')

            if not date_str or not emp_code:
                continue

            try:
                p_date = datetime.strptime(date_str, '%d/%m/%Y').date()
            except Exception:
                continue

            emp = mapping_dict.get(emp_code)
            emp_id = emp.id if emp else f"EMP-{emp_code}"
            dept_name = emp.department_name if emp and emp.department_name else 'Production & Operations'

            if status_code == 'P':
                att_status = 'Present'
            elif status_code == 'A':
                att_status = 'Absent'
            elif status_code == 'HD':
                att_status = 'Half Day'
            elif status_code == 'WO':
                att_status = 'Weekly Off'
            elif status_code == 'HL':
                att_status = 'Holiday'
            else:
                att_status = 'Present' if in_time != '--:--' else 'Absent'

            wh = 0.0
            if work_time and work_time != '--:--':
                try:
                    parts = work_time.split(':')
                    wh = round(int(parts[0]) + int(parts[1]) / 60.0, 2)
                except Exception:
                    wh = 0.0

            ot = 0.0
            if over_time and over_time != '--:--':
                try:
                    parts = over_time.split(':')
                    ot = round(int(parts[0]) + int(parts[1]) / 60.0, 2)
                except Exception:
                    ot = 0.0

            lm = 0
            if late_in and late_in != '--:--':
                try:
                    parts = late_in.split(':')
                    lm = int(parts[0]) * 60 + int(parts[1])
                except Exception:
                    lm = 0

            p_count = 0
            clean_in = ''
            clean_out = ''
            if in_time and in_time != '--:--':
                clean_in = in_time
                p_count += 1
            if out_time and out_time != '--:--':
                clean_out = out_time
                p_count += 1

            is_missing = (p_count == 1 and att_status == 'Present')

            att, is_new = AttendanceRecord.objects.update_or_create(
                employee_id=emp_id,
                date=p_date,
                defaults={
                    'employee_name': name or (emp.name if emp else f"Staff {emp_code}"),
                    'department': dept_name,
                    'shift_name': shift_title,
                    'check_in': clean_in,
                    'check_out': clean_out,
                    'first_in': clean_in,
                    'last_out': clean_out,
                    'punch_count': p_count,
                    'total_hours': wh,
                    'overtime_hours': ot,
                    'late_minutes': lm,
                    'status': att_status,
                    'is_missing_punch': is_missing,
                    'remarks': remark if remark != '--' else '',
                    'source': 'eTimeOffice Machine'
                }
            )
            if is_new:
                att_created += 1
            else:
                att_updated += 1

        log_lines.append(f"Attendance Records: {att_created} created, {att_updated} updated. Total attendance in DB: {AttendanceRecord.objects.count()}")

    except Exception as e:
        log_lines.append(f"FATAL ERROR during sync: {e}")

    output_path = '/home/erpUMA/biometric_sync_live_result.txt'
    try:
        with open(output_path, 'w', encoding='utf-8') as out_f:
            out_f.write('\n'.join(log_lines))
    except Exception:
        pass
    print('\n'.join(log_lines))

if __name__ == '__main__':
    run_sync()
