import sqlite3

local_db_path = r'd:\UMA ERP Test 3\BE-ERP-UMA-Test-2\db.sqlite3'
remote_db_path = r'd:\UMA ERP Test 3\BE-ERP-UMA-Test-2\db_remote_backup.sqlite3'

con_local = sqlite3.connect(local_db_path)
con_remote = sqlite3.connect(remote_db_path)

cur_l = con_local.cursor()
cur_r = con_remote.cursor()

tables = [row[0] for row in cur_r.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
print('Remote tables count:', len(tables))

# Sync authentication_user
machine_users = cur_l.execute("SELECT * FROM authentication_user WHERE id LIKE 'EMP-%' OR username LIKE 'user_%';").fetchall()
user_cols = [c[1] for c in cur_l.execute('PRAGMA table_info(authentication_user);').fetchall()]
print(f'Machine users to sync: {len(machine_users)}')

placeholders = ', '.join(['?'] * len(user_cols))
col_names = ', '.join(user_cols)

u_inserted = 0
for u in machine_users:
    u_dict = dict(zip(user_cols, u))
    exists = cur_r.execute('SELECT 1 FROM authentication_user WHERE id=? OR username=?', (u_dict['id'], u_dict['username'])).fetchone()
    if not exists:
        cur_r.execute(f'INSERT INTO authentication_user ({col_names}) VALUES ({placeholders})', u)
        u_inserted += 1
print(f'Inserted {u_inserted} machine users into remote DB.')

# Sync hr_biometricemployeemapping
if 'hr_biometricemployeemapping' in tables:
    map_cols = [c[1] for c in cur_l.execute('PRAGMA table_info(hr_biometricemployeemapping);').fetchall()]
    local_maps = cur_l.execute('SELECT * FROM hr_biometricemployeemapping').fetchall()
    cur_r.execute('DELETE FROM hr_biometricemployeemapping;')
    cur_r.executemany(f"INSERT INTO hr_biometricemployeemapping ({', '.join(map_cols)}) VALUES ({', '.join(['?']*len(map_cols))})", local_maps)
    print(f'Synced {len(local_maps)} biometric mappings into remote DB.')

# Sync hr_attendancerecord
if 'hr_attendancerecord' in tables:
    att_cols = [c[1] for c in cur_l.execute('PRAGMA table_info(hr_attendancerecord);').fetchall()]
    local_atts = cur_l.execute('SELECT * FROM hr_attendancerecord').fetchall()
    cur_r.execute('DELETE FROM hr_attendancerecord;')
    cur_r.executemany(f"INSERT INTO hr_attendancerecord ({', '.join(att_cols)}) VALUES ({', '.join(['?']*len(att_cols))})", local_atts)
    print(f'Synced {len(local_atts)} attendance records into remote DB.')

# Sync hr_punchmachineconfig
if 'hr_punchmachineconfig' in tables:
    cfg_cols = [c[1] for c in cur_l.execute('PRAGMA table_info(hr_punchmachineconfig);').fetchall()]
    local_cfgs = cur_l.execute('SELECT * FROM hr_punchmachineconfig').fetchall()
    cur_r.execute('DELETE FROM hr_punchmachineconfig;')
    cur_r.executemany(f"INSERT INTO hr_punchmachineconfig ({', '.join(cfg_cols)}) VALUES ({', '.join(['?']*len(cfg_cols))})", local_cfgs)
    print(f'Synced {len(local_cfgs)} config records into remote DB.')

con_remote.commit()
con_local.close()
con_remote.close()
print('Remote DB successfully merged with all biometric employees and attendance!')
